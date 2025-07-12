import json
import random

from pathlib import Path
from typing import Optional


class TipleTriad:
    Pack: dict[int, dict[str, str | int]] = {}


with open(Path("/app/src/app/assets/cards-data.json")) as handle:
    TipleTriad.Pack = {data["id"] + 1: data for data in json.load(handle)}


class Card:
    def __init__(self, id: int):
        assert 1 <= id <= 110

        self.name: str = ""
        self.top: int = 0
        self.right: int = 0
        self.bottom: int = 0
        self.left: int = 0
        self.level: int = 0
        self.element: str = ""
        self.__dict__.update(TipleTriad.Pack.get(id) or {})
        self.id = id

    def __getitem__(self, name: str) -> int:
        return getattr(self, name)

    def __str__(self) -> str:
        return f"{self.name}[{self.top}, {self.right}, {self.bottom}, {self.left}, '{self.element or ''}']"


class Hand:
    def __init__(self, id: int, selected_cards: list[int]):
        assert id > 0
        assert len(selected_cards) == 5

        self.id: int = id
        self.hold_cards: dict[int, Card] = {
            1: Card(selected_cards[0]),
            2: Card(selected_cards[1]),
            3: Card(selected_cards[2]),
            4: Card(selected_cards[3]),
            5: Card(selected_cards[4]),
        }
        self.unhold_cards: list[int] = []

    def __str__(self) -> str:
        return f"P[{self.id}]"

    def is_card_available(self, hold_id: int) -> Card:
        assert 1 <= hold_id <= 5

        if hold_id not in self.unhold_cards:
            return self.hold_cards.get(hold_id)  # type: ignore

        raise Exception(f"Hand[{self.id}] does not holds card: {hold_id}")


class Game:
    def __init__(self, uniqid: str, hand: Hand, opposite_hand: Hand):
        assert hand.id != opposite_hand.id

        self.uniqid: str = uniqid
        self.hands: dict[int, Hand] = {
            1: hand,
            2: opposite_hand,
        }
        self.cells: dict[int, Game.Cell] = {
            1: Game.Cell(1, 1),
            2: Game.Cell(1, 2),
            3: Game.Cell(1, 3),
            4: Game.Cell(2, 1),
            5: Game.Cell(2, 2),
            6: Game.Cell(2, 3),
            7: Game.Cell(3, 1),
            8: Game.Cell(3, 2),
            9: Game.Cell(3, 3),
        }
        self.hand_turn: int = 1  # random.choice([1, 2])
        self.game_rules: list[str] = []
        self.notifications: list[str] = []

    def __getitem__(self, cell_id: int) -> "Game.Cell":
        assert 1 <= cell_id <= 9

        return self.cells.get(cell_id)  # type: ignore

    def move(self, *, cell_id: int, hand_id: int, hold_id: int):
        assert 1 <= cell_id <= 9
        assert 1 <= hold_id <= 5
        assert hand_id in [1, 2]
        assert self.hand_turn == hand_id

        if (cell := self.cells.get(cell_id)) and (hand := self.hands.get(hand_id)):
            if cell.is_occupied():
                raise Exception(f"Game.Cell is already occupied: {cell_id}")

            if card := hand.is_card_available(hold_id):
                cell.card = card
                cell.hand = hand
                self.hand_turn = 1 if self.hand_turn == 2 else 2
                self.notifications.append(
                    f"{cell.hand}: Placed {cell.card} in cell: {cell_id}"
                )
                return self.capture_cells(cell)

    def bot_move(self):
        pass

    def bot_possible_moves(self):
        pass

    def capture_cells(self, cell: "Game.Cell"):
        if cell.hand and cell.card:
            for side, (opp_cell_id, opp_side) in cell.neighbors():
                opp_cell = self.cells[opp_cell_id]

                if opp_cell.is_opposite_hand(cell.hand.id):
                    if opp_cell.hand and opp_cell.card:
                        if cell.card[side] > opp_cell.card[opp_side]:
                            opp_cell.hand = cell.hand
                            self.notifications.append(
                                f"{cell.card.name}[{side}={cell.card[side]}] > {opp_cell.card.name}[{opp_side}={opp_cell.card[opp_side]}]"
                            )

                            if "combo" in self.game_rules:
                                return self.capture_cells(opp_cell)

    class Cell:
        def __init__(self, row_id: int, column_id: int):
            assert 1 <= row_id <= 3
            assert 1 <= column_id <= 3

            self.row_id: int = row_id - 1
            self.column_id: int = column_id - 1
            self.card: Optional[Card] = None
            self.hand: Optional[Hand] = None

        def is_occupied(self) -> bool:
            return self.hand is not None and self.card is not None

        def is_opposite_hand(self, hand_id: int) -> bool:
            return self.is_occupied() and self.hand.id != hand_id  # type: ignore

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
