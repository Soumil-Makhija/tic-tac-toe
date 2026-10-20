"""Immutable game rules and computer opponents, independent of the terminal."""

from dataclasses import dataclass
from functools import lru_cache
import random

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)
PREFERENCE = (4, 0, 2, 6, 8, 1, 3, 5, 7)


@dataclass(frozen=True)
class Game:
    """A board reachable by alternating legal moves, with X starting."""

    cells: tuple[str, ...] = (" ",) * 9

    def __post_init__(self):
        if len(self.cells) != 9 or any(c not in (" ", "X", "O") for c in self.cells):
            raise ValueError("A board must contain nine spaces, Xs, or Os.")
        x, o = self.cells.count("X"), self.cells.count("O")
        winners = {self.cells[a] for a, b, c in LINES
                   if self.cells[a] != " " and self.cells[a] == self.cells[b] == self.cells[c]}
        if (x not in (o, o + 1) or len(winners) > 1
                or ("X" in winners and x != o + 1)
                or ("O" in winners and x != o)):
            raise ValueError("Board is not a legal game position.")

    @property
    def turn(self) -> str:
        return "X" if self.cells.count("X") == self.cells.count("O") else "O"

    @property
    def winning_line(self) -> tuple[int, ...]:
        for a, b, c in LINES:
            if self.cells[a] != " " and self.cells[a] == self.cells[b] == self.cells[c]:
                return (a, b, c)
        return ()

    @property
    def winner(self) -> str | None:
        line = self.winning_line
        return self.cells[line[0]] if line else None

    @property
    def over(self) -> bool:
        return self.winner is not None or " " not in self.cells

    @property
    def available(self) -> tuple[int, ...]:
        return () if self.over else tuple(i for i in PREFERENCE if self.cells[i] == " ")

    def play(self, square: int) -> "Game":
        """Play a zero-based square; reject completed games and occupied cells."""
        if self.over:
            raise ValueError("This round is already finished.")
        if type(square) is not int or not 0 <= square < 9:
            raise ValueError("Choose a square from 1 to 9.")
        if self.cells[square] != " ":
            raise ValueError("That square is taken. Try another.")
        cells = list(self.cells)
        cells[square] = self.turn
        return Game(tuple(cells))


@lru_cache(maxsize=6000)
def _value(game: Game) -> int:
    """Negamax value from the next player's perspective."""
    if game.winner:
        return -1
    if game.over:
        return 0
    return max(-_value(game.play(move)) for move in game.available)


def choose_move(game: Game, difficulty: str = "hard", rng=None) -> int:
    """Easy is random; medium wins/blocks; hard searches the entire game tree."""
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("Difficulty must be easy, medium, or hard.")
    if game.over:
        raise ValueError("This round is already finished.")
    rng = rng or random
    if difficulty == "easy":
        return rng.choice(game.available)
    if difficulty == "medium":
        for mark in (game.turn, "O" if game.turn == "X" else "X"):
            for line in LINES:
                values = [game.cells[i] for i in line]
                if values.count(mark) == 2 and values.count(" ") == 1:
                    return line[values.index(" ")]
        return rng.choice(game.available)
    return max(game.available, key=lambda move: -_value(game.play(move)))
