import json
import uuid
import time
import random

from pathlib import Path
from typing import Any, Optional
from collections import deque


def short_uuid() -> str:
    return str(uuid.uuid4())[0:8]


class TripleTriad:
    Pack: dict[int, dict[str, str | int]] = {}

    @staticmethod
    def chunk(chunk_size: int = 11) -> list[dict[str, str | int]]:
        results = []
        new_dict = {}

        for k, v in TripleTriad.Pack.items():
            if len(new_dict) < chunk_size:
                new_dict[k] = v
            else:
                results.append(new_dict)
                new_dict = {k: v}

        results.append(new_dict)

        return results


with open(Path("/app/src/app/assets/cards.json")) as handle:
    TripleTriad.Pack = {data["id"]: data for data in json.load(handle)}


class Card:
    def __init__(self, id: int, team: str = "?"):
        assert 1 <= id <= 110
        assert team in ["a", "b", "?"]

        self.id = id
        self.name: str = ""
        self.top: int = 0
        self.right: int = 0
        self.bottom: int = 0
        self.left: int = 0
        self.level: int = 0
        self.element: str = ""

        if data := TripleTriad.Pack.get(id):
            self.__dict__.update(data)

        filename = self.name.replace(" ", "_")

        if team == "?":
            self.image: str = "/public/images/cards/back.png"
        elif team == "a":
            self.image: str = f"/public/images/cards/a/TT_{filename}.png"
        elif team == "b":
            self.image: str = f"/public/images/cards/b/TT_{filename}.png"

    def __getitem__(self, name: str) -> int:
        return getattr(self, name)

    def __str__(self) -> str:
        return f"{self.name}[{self.top}, {self.right}, {self.bottom}, {self.left}, '{self.element or ''}']"


class S:
    H1: int = 1
    H2: int = 2
    RED: int = 2
    BLUE: int = 1

    S1: int = 1
    S2: int = 2
    S3: int = 3
    S4: int = 4
    S5: int = 5

    C1: int = 1
    C2: int = 2
    C3: int = 3
    C4: int = 4
    C5: int = 5
    C6: int = 6
    C7: int = 7
    C8: int = 8
    C9: int = 9


class Hand:
    TEAM_RED: str = "a"
    TEAM_BLUE: str = "b"

    def __init__(self, id: int, team: str, selected_cards: list[int]):
        assert team in [Hand.TEAM_RED, Hand.TEAM_BLUE]
        assert id in [S.H1, S.H2]
        assert len(selected_cards) == 5

        self.id: int = id
        self.team: str = team
        self.selected_cards = {
            S.S1: Card(selected_cards[0], self.team),
            S.S2: Card(selected_cards[1], self.team),
            S.S3: Card(selected_cards[2], self.team),
            S.S4: Card(selected_cards[3], self.team),
            S.S5: Card(selected_cards[4], self.team),
        }

    def __str__(self) -> str:
        return f"P{self.id} ({'RED' if self.team == Hand.TEAM_RED else 'BLUE'})"


class Game:
    RULES: dict[str, str] = {
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
    }

    def __init__(self):
        self.cells: dict[int, Game.Cell] = {
            S.C1: Game.Cell(1, 1),
            S.C2: Game.Cell(1, 2),
            S.C3: Game.Cell(1, 3),
            S.C4: Game.Cell(2, 1),
            S.C5: Game.Cell(2, 2),
            S.C6: Game.Cell(2, 3),
            S.C7: Game.Cell(3, 1),
            S.C8: Game.Cell(3, 2),
            S.C9: Game.Cell(3, 3),
        }
        self.hands: dict[int, Hand] = {}
        self.applied_rules = []

    class Cell:
        def __init__(self, row_id: int, column_id: int):
            assert 1 <= row_id <= 3
            assert 1 <= column_id <= 3

            self.row_id: int = row_id - 1
            self.column_id: int = column_id - 1
            self.card: Optional[Card] = None
            self.hand: Optional[Hand] = None
            self.occupied: bool = False

        def is_occupied(self) -> bool:
            return self.occupied

        def is_opposite_hand(self, hand_id: int) -> bool:
            if self.hand is not None:
                return self.occupied and self.hand.id != hand_id

            return True

        def neighbors(self) -> list[tuple[str, tuple[int, str]]]:
            items = []

            for row in range(3):
                for column in range(3):
                    if self.row_id == row and self.column_id == column:
                        for next_row_index, next_column_index, side, opp_side in [
                            (-1, 0, "top", "bottom"),
                            (1, 0, "bottom", "top"),
                            (0, -1, "left", "right"),
                            (0, 1, "right", "left"),
                        ]:
                            next_row = row + next_row_index
                            next_column = column + next_column_index
                            cell_id: int = (next_row * 3) + next_column + 1

                            if 0 <= next_row < 3 and 0 <= next_column < 3:
                                items.append((side, (cell_id, opp_side)))
            return items


class Bot(Game):
    def load_board(self, board: dict[int, dict[str, int]]):
        for cell_id, item in board.items():
            if item["is_occupied"]:
                self.cells[cell_id].card = Card(item["card_id"])
                self.cells[cell_id].hand = self.hands[item["hand_id"]]
                self.cells[cell_id].occupied = True

    def count_captures(self, cell: "Game.Cell", count: int = 0) -> int:
        if cell and not cell.occupied and cell.hand and cell.card:
            for side, (opp_cell_id, opp_side) in cell.neighbors():
                opp_cell = self.cells[opp_cell_id]

                if opp_cell.is_opposite_hand(cell.hand.id):
                    if opp_cell.hand and opp_cell.card:
                        if cell.card[side] > opp_cell.card[opp_side]:
                            opp_cell.hand = cell.hand
                            count += 1

                            if "combo" in self.applied_rules:
                                return self.count_captures(opp_cell, count)

        return count

    def possible_moves(self) -> tuple[int, int]:
        return (0, 0)


class Session:
    sessions: dict[tuple[str, str], "Session"] = {}

    def __init__(self, host_id: str, opponent_id: str):
        self.id: str = f"{host_id}-{opponent_id}"
        self.host_id: str = host_id
        self.access_id: str = host_id
        self.timeout: int = int(time.time()) + 900
        self.selected_cards: dict[str, list[int]] = {
            host_id: [],
            opponent_id: [],
        }
        self.dequeue: deque = deque([], 100)
        Session.sessions[(host_id, opponent_id)] = self

    def is_timeout(self) -> bool:
        return time.time() > self.timeout
    
    def enqueue(self, access_id: str, did: str, args: Any = None) -> "Session":
        self.dequeue.appendleft({"access_id": access_id, "did": did, "args": args})
        return self

    def select_card(self, access_id: str, card_id: int) -> "Session":
        if len(self.selected_cards[access_id]) < 5:
            self.selected_cards[access_id].append(card_id)

        return self.enqueue(access_id, "SELECTED_CARD", self.selected_cards[access_id])

    def unselect_card(self, access_id: str, card_id: int) -> "Session":
        index = self.selected_cards[access_id].index(card_id)

        if index > -1:
            del self.selected_cards[access_id][index]

        return self.enqueue(access_id, "UNSELECTED_CARD", self.selected_cards[access_id])

    def has_joined(self, access_id: str) -> "Session":
        self.access_id = access_id
        return self.enqueue(access_id, "JOINED_THE_GAME")

    @staticmethod
    def load(session_id: tuple[str, str]) -> Optional["Session"]:
        assert isinstance(session_id, tuple)
        assert len(session_id) == 2

        return Session.sessions.get(session_id)

    @staticmethod
    def join(access_id: str) -> Optional["Session"]:
        assert isinstance(access_id, str)

        for key, session in Session.sessions.items():
            if access_id in key:
                return session.has_joined(access_id)
