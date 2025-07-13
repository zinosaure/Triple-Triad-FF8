import os
import sys
import json
import uuid
import time
import asyncio

from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.websockets import WebSocketState
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from app.models.game import TripleTriad, Card, Hand, Game

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
def home(request: Request):
    context = {
        "v": time.time(),
        "session_id": str(uuid.uuid4()),
        "select_modes": {
            "bot_lvl_1": "Bot level 1",
            "bot_lvl_2": "Bot level 2",
            "bot_lvl_3": "Bot level 3",
            "bot_lvl_4": "Bot level 4",
            "bot_lvl_5": "Bot level 5",
            "human": "Friend — send the invitation link",
        },
        "selection_rules": {
            "random": "Random",
        },
        "game_rules": {
            "open": "Open",
            "elemental": "Elemental",
            "combo": "Combo",
            "same": "Same",
            "same_wall": "Same Wall",
            "plus": "Plus",
            "plus_wall": "Plus Wall",
        },
        "draw_rules": {
            "swap": "Swap",
            "sudden_death": "Sudden Death",
        },
    }

    return HTMLResponse(
        status_code=200, content=env.get_template("pages/index.html").render(context)
    )


@app.get("/prepare")
@app.post("/prepare")
async def prepare(request: Request, response: Response, session_id: str):
    try:
        payload = await request.form()

        if request.method == "POST":
            context = {
                "v": time.time(),
                "post_data": dict(payload),
                "selections": TripleTriad.chunk(11),
            }

            return HTMLResponse(
                status_code=200,
                content=env.get_template("pages/select_cards.html").render(context),
            )
    except Exception:
        pass

    return RedirectResponse("/", 307)


@app.get("/game")
async def game(request: Request, response: Response, session_id: str):
    context = {
        "v": time.time(),
    }

    return HTMLResponse(
        status_code=200,
        content=env.get_template("pages/game.html").render(context),
    )


@app.post("/api/select_this_card")
async def select_this_card(request: Request, response: Response):
    try:
        payload = await request.form()

        if card_id := payload.get("card_id"):
            return {
                "status": 1,
                "card": Card(int(card_id) + 1, Hand.POSITION),
            }
    except Exception as e:
        print("Exception:", str(e))

    return {"status": 0}


@app.post("/api/unselect_this_card")
async def unselect_this_card(request: Request, response: Response):
    return {"status": 1}


# @app.websocket("/ws")
# async def websocket(websocket: WebSocket, session_id: str):
#     try:
#         game: Game = Game.load(session_id)
#         await websocket.accept()

#         if len(connections) >= 15:
#             return

#         if websocket not in connections:
#             print(f"IP: {websocket.client[0]} - UUID: {session_id}")
#             connections.add(websocket)
#             # loop.create_task(timeout(websocket, unique_id))
#             # loop.create_task(listen(websocket, unique_id))

#         while True:
#             try:
#                 payload = await websocket.receive_json()

#                 if session_id != "" and (action := payload.get("action")):
#                     message: dict[str, Any] = {}

#                     # if action == "select_cards":
#                     #     message = {
#                     #         "type": "reload",
#                     #         "session_id": game.uniqid,
#                     #         "board": {
#                     #             "rules": {},
#                     #             "hold": {
#                     #                 "a": game.random_cards(Hand),
#                     #                 "b": get_random_cards("b"),
#                     #             },
#                     #             "ondeck": [],
#                     #             "score": {
#                     #                 "a": 0,
#                     #                 "b": 0,
#                     #             },
#                     #             "turn": random.choice(["B", "R"]),
#                     #         },
#                     #     }
#                     # elif session_id in GAMES:
#                     #     if action == "start-game":
#                     #         GAMES[session_id]["type"] = "distribute"
#                     #     elif action == "next_turn_a":
#                     #         GAMES[session_id]["type"] = "prev_move_a"
#                     #         print(payload)
#                     #     elif action == "next_move_b":
#                     #         GAMES[session_id]["type"] = "prev_move_b"
#                     #         print(payload)
#                     #     else:
#                     #         GAMES[session_id] = {
#                     #             "type": "unmatch",
#                     #             "session_id": session_id,
#                     #             "websocket_id": websocket_id,
#                     #         }

#                     await websocket.send_json(message)
#                 await asyncio.sleep(1 / 30)
#             except WebSocketDisconnect:
#                 try:
#                     return connections.remove(websocket)
#                 except Exception:
#                     return
#             except Exception:
#                 return
#     except Exception:
#         return
