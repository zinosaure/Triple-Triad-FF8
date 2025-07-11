import json

from pathlib import Path
from typing import Optional

from click import Option


class TipleTriad:
    Pack: dict[int, dict[str, str | int]] = {}


with open(Path("/app/src/app/assets/cards-data.json")) as handle:
    TipleTriad.Pack = {data["id"]: data for data in json.load(handle)}


class Card:
    def __init__(self):
        self.id: int = -1
        self.name: str = ""
        self.top: int = 0
        self.right: int = 0
        self.bottom: int = 0
        self.left: int = 0
        self.element: str = ""
        self.level: int = 0
        self.price: int = 0

    def __getitem__(self, name: str) -> int:
        return getattr(self, name)

    @staticmethod
    def load(id: int) -> Optional["Card"]:
        if data := TipleTriad.Pack.get(id - 1):
            card = Card()
            card.__dict__.update(data)
            return card


class Opponent:
    def __init__(self, id: str = "P??"):
        self.id: str = id
        self.selected_cards: dict[str, "Opponent.Hand"] = {
            "H1": Opponent.Hand(),
            "H2": Opponent.Hand(),
            "H3": Opponent.Hand(),
            "H4": Opponent.Hand(),
            "H5": Opponent.Hand(),
        }

    def set_selected_cards(self, selected_cards: dict[str, int]):
        for hand_id, card_id in selected_cards.items():
            if hand := self.selected_cards.get(hand_id.upper()):
                if card := Card.load(card_id):
                    hand.card = card
                    hand.in_hand = True
                else:
                    raise Exception(f"Invalid card id: {card_id}")
            else:
                raise Exception(f"Invalid hand id: {hand_id}")

    class Hand:
        def __init__(self):
            self.card: Card = Card()
            self.in_hand: bool = False


class Cell:
    def __init__(self, name: str):
        self.name: str = name
        self.element: str = ""
        self.occupied: Optional[Cell.Occupied] = None

    def neighbors(self) -> list[tuple[str, tuple[str, str]]]:
        items = []

        for row in range(3):
            for column in range(3):
                if self.name == f"{row + 1}.{column + 1}":
                    for next_row_index, next_column_index, side, opp_side in [
                        (-1, 0, "top", "bottom"),
                        (1, 0, "bottom", "top"),
                        (0, -1, "left", "right"),
                        (0, 1, "right", "left"),
                    ]:
                        next_row = row + next_row_index
                        next_column = column + next_column_index

                        if 0 <= next_row < 3 and 0 <= next_column < 3:
                            items.append(
                                (side, (f"C{next_row + 1}.{next_column + 1}", opp_side))
                            )
        return items

    class Occupied:
        def __init__(self, opponent: Opponent, hand: Opponent.Hand):
            self.opponent: Opponent = opponent
            self.hand: Opponent.Hand = hand


class Game:
    rule_list = [
        "open",
        "random",
        "same",
        "combo",
        "plus",
        "swap",
        "sudden_death",
    ]

    def __init__(self, id: str, P1: Opponent, P2: Opponent = Opponent("BOT")):
        self.id: str = id
        self.cells: dict[str, Cell] = {
            "C1.1": Cell("1.1"),
            "C1.2": Cell("1.2"),
            "C1.3": Cell("1.3"),
            "C2.1": Cell("2.1"),
            "C2.2": Cell("2.2"),
            "C2.3": Cell("2.3"),
            "C3.1": Cell("3.1"),
            "C3.2": Cell("3.2"),
            "C3.3": Cell("3.3"),
        }
        self.opponents: dict[str, Opponent] = {
            "P1": P1,  # right/blue
            "P2": P2,  # left/red (bot)
        }
        self.rules_applied: list[str] = ["combo"]

    def place_on_board(self, cell_id: str, opponent_hand: tuple[str, str]):
        if cell := self.cells.get(cell_id):
            if cell.occupied is None:
                opponent_id, hand_id = opponent_hand

                if (opponent := self.opponents.get(opponent_id)) and (
                    hand := opponent.selected_cards.get(hand_id)
                ):
                    cell.occupied = Cell.Occupied(opponent, hand)
                    return self.capture_surronded_cells(cell)
                else:
                    raise Exception(f"Invalid opponent hand: {opponent_hand}")
            else:
                raise Exception(f"Invalid cell, already taken: {cell_id}")
        else:
            raise Exception(f"Invalid cell id: {cell_id}")

    def capture_surronded_cells(self, cell: Cell):
        if cell.occupied:
            for side, (opp_cell_id, opp_side) in cell.neighbors():
                opp_cell = self.cells[opp_cell_id]

                if opp_cell.occupied and cell.occupied.opponent != opp_cell.occupied.opponent:
                    opp_hand = opp_cell.occupied.hand
                    print(cell.occupied.hand.card.name, cell.occupied.hand.card[side], '>', opp_cell.occupied.hand.card.name,  opp_cell.occupied.hand.card[opp_side])

                    if cell.occupied.hand.card[side] > opp_hand.card[opp_side]:
                        opp_cell.occupied.opponent = cell.occupied.opponent

                        if "combo" in self.rules_applied:
                            return self.capture_surronded_cells(opp_cell)
