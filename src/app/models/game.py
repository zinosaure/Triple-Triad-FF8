import json
import random

from pathlib import Path
from typing import Any, Optional


class TripleTriad:
    Pack: dict[int, dict[str, str | int]] = {}

    @staticmethod
    def chunk(chunk_size: int = 10) -> list[dict[str, str | int]]:
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


with open(Path("/app/src/app/assets/cards-data.json")) as handle:
    TripleTriad.Pack = {data["id"] + 1: data for data in json.load(handle)}


class Card:
    def __init__(self, id: int, hand: "Hand"):
        assert 1 <= id <= 110

        self.name: str = ""
        self.top: int = 0
        self.right: int = 0
        self.bottom: int = 0
        self.left: int = 0
        self.level: int = 0
        self.element: str = ""
        self.__dict__.update(TripleTriad.Pack.get(id) or {})
        self.id = id
        filename = self.name.replace(" ", "_")

        if hand.POSITION == OppositeHand.POSITION:
            self.image: str = f"/public/images/cards/a/TT_{filename}.png"
        else:
            self.image: str = f"/public/images/cards/b/TT_{filename}.png"

    def __getitem__(self, name: str) -> int:
        return getattr(self, name)

    def __str__(self) -> str:
        return f"{self.name}[{self.top}, {self.right}, {self.bottom}, {self.left}, '{self.element or ''}']"


class Hand:
    POSITION: int = 1
    H1: int = 1
    H2: int = 2
    H3: int = 3
    H4: int = 4
    H5: int = 5

    def __init__(self, id: int, selected_cards: list[int]):
        assert id > 0
        assert len(selected_cards) == 5

        self.id: int = id
        self.hold_cards: dict[int, Card] = {
            1: Card(selected_cards[0], self),
            2: Card(selected_cards[1], self),
            3: Card(selected_cards[2], self),
            4: Card(selected_cards[3], self),
            5: Card(selected_cards[4], self),
        }
        self.unhold_cards: list[int] = []

    def __str__(self) -> str:
        return f"P{self.POSITION}"

    def is_card_available(self, hold_id: int) -> Card:
        assert 1 <= hold_id <= 5

        if hold_id not in self.unhold_cards:
            return self.hold_cards.get(hold_id)  # type: ignore

        raise Exception(f"Hand[{self.id}] does not holds card: {hold_id}")


class OppositeHand(Hand):
    POSITION: int = 2


class Game:
    Singleton: dict[str, "Game"] = {}
    rule_list = [
        "open",
        "closed",
        "random",
        "same",
        "combo",
        "wall",
        "plus",
        "swap",
        "elemental",
        "sudden_death",
    ]

    def __init__(self, uniqid: str):
        self.uniqid: str = uniqid
        self.hands: dict[int, Hand] = {}
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
        self.state: Game.State = Game.State()
        Game.Singleton[uniqid] = self

    def __getitem__(self, cell_id: int) -> "Game.Cell":
        assert 1 <= cell_id <= 9

        return self.cells.get(cell_id)  # type: ignore

    @staticmethod
    def load(uniqid: str) -> "Game":
        if uniqid not in Game.Singleton:
            Game.Singleton[uniqid] = Game(uniqid)

        return Game.Singleton[uniqid]

    def set_hand(self, hand: Hand):
        assert Hand.POSITION not in self.hands

        self.hands[Hand.POSITION] = hand

    def update(self) -> dict[str, Any]:
        if self.state.status == "setup":
            if Hand.POSITION in self.hands and OppositeHand.POSITION in self.hands:
                self.state.status = "started"
                self.state.hand_turn = random.choice(
                    [Hand.POSITION, OppositeHand.POSITION]
                )
        else:
            self.state.status = "setup"

        return self.state.send()

    def move(self, *, cell_id: int, hand_id: int, hold_id: int):
        assert 1 <= cell_id <= 9
        assert 1 <= hold_id <= 5
        assert hand_id in [Hand.POSITION, OppositeHand.POSITION]
        assert self.state.hand_turn == hand_id

        if (cell := self.cells.get(cell_id)) and (hand := self.hands.get(hand_id)):
            if cell.is_occupied():
                raise Exception(f"Game.Cell is already occupied: {cell_id}")

            if card := hand.is_card_available(hold_id):
                cell.card = card
                cell.hand = hand
                self.state.notifications.append(
                    f"{cell.hand}: Placed {cell.card} in cell: {cell_id}"
                )
                self.capture_cells(cell)

                if hand_id != Hand.POSITION:
                    self.state.hand_turn = Hand.POSITION
                else:
                    self.state.hand_turn = OppositeHand.POSITION

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

                            if self.state.hand_turn == Hand.POSITION:
                                self.state.score_board[Hand.POSITION] += 1
                                self.state.score_board[OppositeHand.POSITION] -= 1
                            else:
                                self.state.score_board[OppositeHand.POSITION] += 1
                                self.state.score_board[Hand.POSITION] -= 1

                            self.state.notifications.append(
                                f"{cell.card.name}[{side}={cell.card[side]}] > {opp_cell.card.name}[{opp_side}={opp_cell.card[opp_side]}]"
                            )

                            if "combo" in self.state.current_rules:
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

    class State:
        def __init__(self):
            self.status: str = "setup"
            self.hand_turn: int = -1
            self.score_board: dict[int, int] = {
                Hand.POSITION: 5,
                OppositeHand.POSITION: 5,
            }
            self.current_rules: list[str] = []
            self.notifications: list[str] = []

        def send(self) -> dict[str, Any]:
            return self.__dict__
