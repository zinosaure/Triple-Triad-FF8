from email import message
import os
import sys
import json
import time
import asyncio

from typing import Any, Optional

from click import pause

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.websockets import WebSocketState
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from app.models.game import short_uuid, TripleTriad, Card, Hand, Session

# FastAPI
app = FastAPI(title="Triple Triad - FF8")
app.mount("/public", StaticFiles(directory="public/"), name="public")

# Jinja2 Env
env = Environment(loader=FileSystemLoader(["app/templates/"]))

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


connections = set()
loop = asyncio.get_event_loop()


@app.get("/")
@app.post("/")
def home(request: Request):
    session_id: str = f"{short_uuid()}-{short_uuid()}"
    context = {
        "v": time.time(),
        "session_id": session_id,
        "select_modes": {
            "human": "vs. Friend",
            "bot_lvl_1": "vs. Bot level 1",
            "bot_lvl_2": "vs. Bot level 2",
            "bot_lvl_3": "vs. Bot level 3",
            "bot_lvl_4": "vs. Bot level 4",
            "bot_lvl_5": "vs. Bot level 5",
        },
        "select_rules": {
            "open": "Open",
            "random": "Random",
            "elemental": "Elemental",
            "combo": "Combo",
            "same": "Same",
            "same_wall": "Same Wall",
            "plus": "Plus",
            "plus_wall": "Plus Wall",
            "swap": "Swap",
            "sudden_death": "Sudden Death",
        },
    }

    return HTMLResponse(
        status_code=200, content=env.get_template("pages/index.html").render(context)
    )


@app.get("/prepare")
@app.post("/prepare")
async def prepare(request: Request, session_id: str):
    try:
        host_id, opponent_id = session_id.split("-")

        if request.method == "POST":
            access_id = host_id
            session = Session(host_id, opponent_id)

            # for k, v in dict(await request.form()).items():
            #     if k == "mode":
            #         session.versus = v
            #     else:
            #         session.selected_rules.append(k)
        else:
            access_id = opponent_id

        if session := Session.join(access_id):
            session.selected_cards[access_id] = []
            context = {
                "v": time.time(),
                "access_id": access_id,
                "session_id": session.id,
                "chunked_selections": TripleTriad.chunk(11),
            }

            return HTMLResponse(
                status_code=200,
                content=env.get_template("pages/select_cards.html").render(context),
            )
    except Exception:
        pass

    return RedirectResponse(f"/?session_expired={session_id}", 307)


@app.get("/game")
@app.post("/game")
async def game(request: Request, session_id: str):
    try:
        host_id, opponent_id = session_id.split("-")
        payload = await request.form()
        access_id = payload.get("access_id")

        if (session := Session.load((host_id, opponent_id))) and access_id:
            selected_cards = {"a": [], "b": []}

            for _access_id, _selected_cards in session.selected_cards.items():
                if _access_id == access_id:
                    selected_cards["b"] = [Card(id, "b") for id in _selected_cards]
                else:
                    selected_cards["a"] = [Card(id, "a") for id in _selected_cards]

            context = {
                "v": time.time(),
                "access_id": access_id,
                "session_id": session_id,
                "selected_cards": selected_cards,
            }

            return HTMLResponse(
                status_code=200,
                content=env.get_template("pages/game.html").render(context),
            )
    except Exception:
        pass

    # return RedirectResponse(f"/?session_expired={session_id}", 307)


async def timeout(websocket: WebSocket, session: Session):
    await asyncio.sleep(1)


async def listen(websocket: WebSocket, session: Session):
    while True:
        try:
            d = await websocket.receive_json()

            if (type := d.get("type")) and (access_id := d.get("access_id")):
                if type == "select_card":
                    session.select_card(access_id, d.get("card_id", 0))
                elif type == "unselect_card":
                    session.unselect_card(access_id, d.get("card_id", 0))
        except (KeyboardInterrupt, WebSocketDisconnect):
            if websocket in connections:
                # await websocket.close()
                return connections.remove(websocket)

        if len(connections) == 0:
            return


@app.websocket("/ws")
async def websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    host_id, opponent_id = session_id.split("-")

    if not (session := Session.load((host_id, opponent_id))) or len(connections) >= 15:
        return await websocket.close()

    if websocket not in connections:
        print(f"IP: {websocket.client[0]} - Session ID: {session_id}")
        connections.add(websocket)
        loop.create_task(listen(websocket, session))
        # loop.create_task(timeout(websocket, session))

    while True:
        try:
            while len(session.dequeue) > 0:
                message = session.dequeue.pop()
                print(message)
                await websocket.send_json(message)

            await asyncio.sleep(1)
        except (KeyboardInterrupt, WebSocketDisconnect):
            if websocket in connections:
                # await websocket.close()
                return connections.remove(websocket)

        if len(connections) == 0:
            return
