from contextlib import redirect_stdout, redirect_stderr
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tic_tac_toe.cli import main, render_board
from tic_tac_toe.game import Game
from tic_tac_toe.scores import Matchup, ScoreStore


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "data"

    def run_game(self, answers, *options):
        output, errors = io.StringIO(), io.StringIO()
        with patch("builtins.input", side_effect=answers), redirect_stdout(output), redirect_stderr(errors):
            status = main(["--data-dir", str(self.directory), "--no-color", *options])
        return status, output.getvalue(), errors.getvalue()

    def test_local_win_invalid_inputs_and_persistence(self):
        status, output, _ = self.run_game(["hello", "0", "1", "1", "4", "2", "5", "3", "n"], "--mode", "local")
        self.assertEqual(status, 0)
        self.assertIn("square is taken", output)
        self.assertIn("Player 1 wins", output)
        self.assertNotIn("\033[", output)
        matchup = Matchup("local", "-", "Player 1", "Player 2")
        self.assertEqual(ScoreStore(self.directory).totals(matchup), [1, 0, 0])

    def test_rematch_swaps_starter_and_records_once(self):
        answers = ["1", "4", "2", "5", "3", "y", "1", "4", "2", "5", "3", "n"]
        status, output, _ = self.run_game(answers, "--mode", "local")
        self.assertEqual(status, 0)
        self.assertIn("Player 2 (X) vs Player 1 (O)", output)
        self.assertEqual(ScoreStore(self.directory).totals(Matchup("local", "-", "Player 1", "Player 2")), [1, 1, 0])

    def test_draw_and_no_save(self):
        status, output, _ = self.run_game(["1", "2", "3", "5", "4", "6", "8", "7", "9", "n"], "--mode", "local", "--no-save")
        self.assertEqual(status, 0)
        self.assertIn("A draw", output)
        self.assertIn("Draws 1", output)
        self.assertFalse(self.directory.exists())

    def test_quit_and_eof_do_not_save_unfinished_round(self):
        for answers in (["1", "q"], [EOFError]):
            status, _, _ = self.run_game(answers, "--mode", "local")
            self.assertEqual(status, 0)
            self.assertFalse(self.directory.exists())

    def test_computer_starts_when_human_chooses_o(self):
        status, output, _ = self.run_game(["q"], "--mode", "solo", "--mark", "O")
        self.assertEqual(status, 0)
        self.assertIn("Computer (X) chooses 5", output)

    def test_storage_error_is_actionable(self):
        self.directory.mkdir()
        (self.directory / "scores.sqlite3").write_bytes(b"broken database")
        status, _, errors = self.run_game([], "--mode", "solo")
        self.assertEqual(status, 1)
        self.assertIn("--no-save", errors)

    def test_board_reference_and_winning_marks(self):
        self.assertIn("1 | 2 | 3", render_board(Game()))
        board = render_board(Game(tuple("XXXOO    ")), True)
        self.assertEqual(board.count("\033[1;32mX"), 3)
