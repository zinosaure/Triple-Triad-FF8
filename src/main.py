import os
import sys
import json
import uuid
import time
import random
import asyncio

from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.websockets import WebSocketState
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader

from app.models.game import Opponent, Game

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


P1: Opponent = Opponent("P1")
P2: Opponent = Opponent("P2")
game: Game = Game("xxxx-yyyyyy-zzzz", P1, P2)
P1.set_selected_cards({"H1": 50, "H2": 20, "H3": 110, "H4": 98, "H5": 99})
P2.set_selected_cards({"H1": 88, "H2": 70, "H3": 103, "H4": 101, "H5": 100})

game.place_on_board("C1.1", ("P1", "H5"))
game.place_on_board("C1.2", ("P1", "H2"))
game.place_on_board("C2.1", ("P2", "H5"))
for name, cell in game.cells.items():
    if cell.occupied:
        print(name, ":", cell.occupied.opponent.id, cell.occupied.hand.card.name)
    else:
        print(name, ":")

CARDS: list[dict[int, int | str]] = []
GAMES: dict[str, dict[str, Any]] = {}

with open("/app/src/app/assets/cards-data.json") as handle:
    for item in json.load(handle):
        CARDS.append(item)

connections = set()
loop = asyncio.get_event_loop()


@app.get("/")
def home(request: Request):
    context = {"v": time.time()}
    return HTMLResponse(
        status_code=200, content=env.get_template("index.html").render(context)
    )


def get_random_cards(color: str = "a"):
    selected_cards = []
    for i in range(5):
        card: dict[str, Any] = random.choice(CARDS)
        card["image"] = (
            f"/public/images/cards/{color}/TT_{card['name'].replace(' ', '_')}.png"
        )
        selected_cards.append(card)
    return selected_cards


@app.websocket("/ws")
async def websocket(websocket: WebSocket, game_id: str = ""):
    try:
        await websocket.accept()
        websocket_id = id(websocket)

        if len(connections) >= 15:
            return

        if websocket not in connections:
            print(f"IP: {websocket.client[0]} - UUID: {game_id}")
            connections.add(websocket)
            # loop.create_task(timeout(websocket, unique_id))
            # loop.create_task(listen(websocket, unique_id))

        while True:
            try:
                payload = await websocket.receive_json()

                if action := payload.get("action"):
                    if action == "setup" or game_id not in GAMES:
                        game_id = str(uuid.uuid4())
                        GAMES[game_id] = {
                            "type": "reload",
                            "game_id": game_id,
                            "websocket_id": websocket_id,
                            "board": {
                                "rules": {},
                                "hold": {
                                    "a": get_random_cards("a"),
                                    "b": get_random_cards("b"),
                                },
                                "ondeck": [],
                                "score": {
                                    "a": 0,
                                    "b": 0,
                                },
                                "turn": random.choice(["B", "R"]),
                            },
                        }
                    elif game_id in GAMES:
                        if action == "start-game":
                            GAMES[game_id]["type"] = "distribute"
                        elif action == "next_turn_a":
                            GAMES[game_id]["type"] = "prev_move_a"
                            print(payload)
                        elif action == "next_move_b":
                            GAMES[game_id]["type"] = "prev_move_b"
                            print(payload)
                        else:
                            GAMES[game_id] = {
                                "type": "unmatch",
                                "game_id": game_id,
                                "websocket_id": websocket_id,
                            }

                    await websocket.send_json(GAMES[game_id])
                await asyncio.sleep(1 / 30)
            except WebSocketDisconnect:
                try:
                    return connections.remove(websocket)
                except Exception:
                    return
            except Exception:
                return
    except Exception:
        return
