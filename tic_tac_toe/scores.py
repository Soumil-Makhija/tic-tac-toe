"""Transactional local scoreboard; only completed rounds are recorded."""

from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
import sys


def default_data_dir() -> Path:
    if os.environ.get("TIC_TAC_TOE_HOME"):
        return Path(os.environ["TIC_TAC_TOE_HOME"]).expanduser()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "tic-tac-toe"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/tic-tac-toe"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "tic-tac-toe"


@dataclass(frozen=True)
class Matchup:
    mode: str
    difficulty: str
    player: str
    opponent: str


class ScoreStore:
    def __init__(self, directory: Path):
        self.path = directory / "scores.sqlite3"

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=3)
        try:
            connection.execute("""CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY,
                played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                mode TEXT NOT NULL, difficulty TEXT NOT NULL,
                player TEXT NOT NULL, opponent TEXT NOT NULL,
                result TEXT NOT NULL CHECK (result IN ('player', 'opponent', 'draw'))
            )""")
            return connection
        except BaseException:
            connection.close()
            raise

    def record(self, matchup: Matchup, result: str):
        if result not in ("player", "opponent", "draw"):
            raise ValueError("Only completed round results can be recorded.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    "INSERT INTO rounds (mode, difficulty, player, opponent, result) VALUES (?, ?, ?, ?, ?)",
                    (matchup.mode, matchup.difficulty, matchup.player, matchup.opponent, result),
                )
        finally:
            connection.close()

    def summaries(self) -> list[tuple]:
        if not self.path.exists():
            return []
        connection = self._connect()
        try:
            return connection.execute("""SELECT mode, difficulty, player, opponent,
                SUM(result = 'player'), SUM(result = 'opponent'), SUM(result = 'draw')
                FROM rounds GROUP BY mode, difficulty, player, opponent
                ORDER BY mode, difficulty, player, opponent""").fetchall()
        finally:
            connection.close()

    def totals(self, matchup: Matchup) -> list[int]:
        key = (matchup.mode, matchup.difficulty, matchup.player, matchup.opponent)
        for row in self.summaries():
            if row[:4] == key:
                return list(row[4:])
        return [0, 0, 0]
