from pathlib import Path
import sqlite3
import tempfile
import unittest

from tic_tac_toe.scores import Matchup, ScoreStore


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "data"
        self.store = ScoreStore(self.directory)
        self.matchup = Matchup("solo", "hard", "Alex", "Computer")

    def test_empty_reads_do_not_create_files(self):
        self.assertEqual(self.store.summaries(), [])
        self.assertEqual(self.store.totals(self.matchup), [0, 0, 0])
        self.assertFalse(self.directory.exists())

    def test_totals_survive_restart_and_matchups_stay_separate(self):
        for result in ("player", "opponent", "draw", "player"):
            self.store.record(self.matchup, result)
        other = Matchup("solo", "easy", "Alex", "Computer")
        self.store.record(other, "draw")
        fresh = ScoreStore(self.directory)
        self.assertEqual(fresh.totals(self.matchup), [2, 1, 1])
        self.assertEqual(fresh.totals(other), [0, 0, 1])

    def test_names_are_parameterized(self):
        matchup = Matchup("local", "-", "O'Brien", "DROP TABLE rounds;")
        self.store.record(matchup, "player")
        self.assertEqual(self.store.totals(matchup), [1, 0, 0])

    def test_invalid_result_never_writes(self):
        with self.assertRaises(ValueError):
            self.store.record(self.matchup, "unfinished")
        self.assertFalse(self.directory.exists())

    def test_damaged_file_is_preserved(self):
        self.directory.mkdir()
        self.store.path.write_bytes(b"not a sqlite database")
        with self.assertRaises(sqlite3.DatabaseError):
            self.store.summaries()
        self.assertEqual(self.store.path.read_bytes(), b"not a sqlite database")
