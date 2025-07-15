import os
import sys
import json
import time
import asyncio

from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.websockets import WebSocketState
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from app.models.game import S, short_uuid, TripleTriad, Card, Hand, Game, GameSession

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
    hand_name_1, hand_name_2 = session_id.split("-")

    if request.method == "POST":
        hand_name = hand_name_1
        session = GameSession.create_session(hand_name_1, hand_name_2)

        for k, v in dict(await request.form()).items():
            if k == "mode":
                session.versus = v
            else:
                session.selected_rules.append(k)
    else:
        hand_name = hand_name_2

    if session := GameSession.load_session(session_id):
        session.selected_cards[hand_name] = []

        context = {
            "v": time.time(),
            "hand_name": hand_name,
            "session_id": session_id,
            "selections": TripleTriad.chunk(11),
        }

        return HTMLResponse(
            status_code=200,
            content=env.get_template("pages/select_cards.html").render(context),
        )

    return RedirectResponse(f"/?session_expired={session_id}", 307)


@app.get("/game")
async def game(request: Request, hand_name: str, session_id: str):
    try:
        if session := GameSession.load_session(session_id):
            session.actions[hand_name] = "is_waiting"
            selected_cards = {"a": [], "b": []}

            for _hand_name, _selected_cards in session.selected_cards.items():
                if _hand_name == hand_name:
                    selected_cards["b"] = [Card(id, "b") for id in _selected_cards]
                else:
                    selected_cards["a"] = [Card(id, "a") for id in _selected_cards]

            context = {
                "v": time.time(),
                "session_id": session_id,
                "selected_cards": selected_cards,
            }

            return HTMLResponse(
                status_code=200,
                content=env.get_template("pages/game.html").render(context),
            )
    except Exception:
        pass

    return RedirectResponse(f"/?session_expired={session_id}", 307)


@app.post("/api/select_this_card")
async def select_this_card(request: Request):
    try:
        payload = await request.form()
        card_id = payload.get("card_id")
        hand_name = payload.get("hand_name")
        session_id = payload.get("session_id")

        if card_id and hand_name and session_id:
            if session := GameSession.load_session(session_id):
                session.selected_cards[hand_name].append(int(card_id))
                return {
                    "status": 1,
                    "card": Card(int(card_id), Hand.TEAM_BLUE),
                }
    except Exception as e:
        print("Exception:", str(e))

    return {"status": 0}


@app.post("/api/unselect_this_card")
async def unselect_this_card(request: Request):
    try:
        payload = await request.form()
        card_id = payload.get("card_id")
        hand_name = payload.get("hand_name")
        session_id = payload.get("session_id")

        if card_id and hand_name and session_id and ():
            if session := GameSession.load_session(session_id):
                index = session.selected_cards[hand_name].index(int(card_id))

                if index > -1:
                    del session.selected_cards[hand_name][index]
                    return {"status": 1}
    except Exception as e:
        print("Exception:", str(e))

    return {"status": 0}


@app.websocket("/ws")
async def websocket(websocket: WebSocket, session_id: str):
    try:
        await websocket.accept()

        if len(connections) >= 15:
            return

        if websocket not in connections:
            print(f"IP: {websocket.client[0]} - UUID: {session_id}")
            connections.add(websocket)
            # loop.create_task(timeout(websocket, unique_id))
            # loop.create_task(listen(websocket, unique_id))

        if not (session := GameSession.load_session(session_id)):
            return websocket.close()

        while True:
            try:
                payload = await websocket.receive_json()

                if action := payload.get("action"):
                    data = {}
                    if action == "is_waiting":
                        for hand_name, action in session.actions.items():
                            if action == "prepapring":
                                data = {
                                    "response": "load_cards",
                                    "selected_cards": session.selected_cards[hand_name],
                                }

                    await websocket.send_json(data)
            except WebSocketDisconnect:
                try:
                    return connections.remove(websocket)
                except Exception:
                    return
            except Exception:
                return
    except Exception:
        return
