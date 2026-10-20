import random
import unittest
from itertools import combinations

from tic_tac_toe.game import Game, LINES, choose_move


class GameTests(unittest.TestCase):
    def test_every_winning_line_for_both_marks(self):
        for line in LINES:
            for mark in ("X", "O"):
                cells = [" "] * 9
                for i in line:
                    cells[i] = mark
                others = [i for i in range(9) if i not in line]
                count = 2 if mark == "X" else 3
                placements = next(combo for combo in combinations(others, count)
                                  if not any(set(other).issubset(combo) for other in LINES))
                for i in placements:
                    cells[i] = "O" if mark == "X" else "X"
                game = Game(tuple(cells))
                self.assertEqual(game.winner, mark)
                self.assertEqual(game.winning_line, line)
                self.assertTrue(game.over)
                self.assertEqual(game.available, ())

    def test_draw_and_finished_game(self):
        game = Game(tuple("XOXXOOOXX"))
        self.assertTrue(game.over)
        self.assertIsNone(game.winner)
        with self.assertRaises(ValueError):
            game.play(0)
        with self.assertRaises(ValueError):
            choose_move(game)

    def test_move_validation_and_immutability(self):
        original = Game()
        game = original.play(0)
        self.assertEqual(original.cells[0], " ")
        self.assertEqual(game.turn, "O")
        for move in (0, -1, 9, True, "1"):
            with self.assertRaises(ValueError):
                game.play(move)

    def test_bad_boards(self):
        for cells in ("X", "O        ", "XXXOOO   ", "Z        ", "OO       "):
            with self.assertRaises(ValueError):
                Game(tuple(cells))

    def test_medium_wins_before_blocking(self):
        self.assertEqual(choose_move(Game(tuple("XX OO    ")), "medium"), 2)
        self.assertEqual(choose_move(Game(tuple("XX  O    ")), "medium"), 2)

    def test_easy_returns_legal_moves(self):
        game = Game().play(4)
        rng = random.Random(17)
        moves = {choose_move(game, "easy", rng) for _ in range(100)}
        self.assertEqual(moves, set(game.available))

    def test_hard_cannot_lose_as_either_mark(self):
        # Explore every human reply against the actual hard move selector.
        for computer in ("X", "O"):
            visited = set()

            def explore(game):
                if game in visited:
                    return
                visited.add(game)
                if game.over:
                    self.assertIn(game.winner, (None, computer))
                    return
                moves = ((choose_move(game),) if game.turn == computer else game.available)
                for move in moves:
                    explore(game.play(move))

            explore(Game())


if __name__ == "__main__":
    unittest.main()
