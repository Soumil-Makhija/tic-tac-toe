"""Line-oriented terminal interface, friendly to keyboards and screen readers."""

import argparse
import os
from pathlib import Path
import sqlite3
import sys

from . import __version__
from .game import Game, choose_move
from .scores import Matchup, ScoreStore, default_data_dir


class QuitGame(Exception):
    pass


def ask(prompt: str) -> str:
    answer = input(prompt).strip()
    if answer.lower() in ("q", "quit", "exit"):
        raise QuitGame
    return answer


def player_name(value: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 24 or not value.isprintable():
        raise argparse.ArgumentTypeError("Names must be 1–24 printable characters.")
    return value


def paint(text: str, code: str, color: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if color else text


def render_board(game: Game, color: bool = False) -> str:
    rows = []
    winning = game.winning_line
    for row in range(3):
        cells = []
        for index in range(row * 3, row * 3 + 3):
            mark = game.cells[index]
            label = str(index + 1) if mark == " " else mark
            code = "1;32" if index in winning else {"X": "1;36", "O": "1;35", " ": "2"}[mark]
            cells.append(paint(label, code, color))
        rows.append("    " + " | ".join(cells))
        if row < 2:
            rows.append("   ---+---+---")
    return "\n".join(rows)


def show_scores(store: ScoreStore):
    print("\n  SAVED SCOREBOARD\n  " + "-" * 48)
    rows = store.summaries()
    if not rows:
        print("  No completed rounds yet. Your first game starts here.")
    for mode, difficulty, player, opponent, wins, losses, draws in rows:
        label = f"computer / {difficulty}" if mode == "solo" else "local two-player"
        print(f"  {player} vs {opponent} ({label})")
        print(f"  {player}: {wins}  |  {opponent}: {losses}  |  Draws: {draws}\n")
    print(f"\n  Saved at: {store.path}\n")


def play(args, store: ScoreStore, color: bool):
    mode = args.mode
    opponent = "Computer" if mode == "solo" else args.opponent
    if args.name.casefold() == opponent.casefold():
        raise ValueError("Use distinct player names so the scoreboard is clear.")
    matchup = Matchup(mode, args.difficulty if mode == "solo" else "-", args.name, opponent)
    totals = [0, 0, 0] if args.no_save else store.totals(matchup)
    player_mark = args.mark
    round_number = 1
    print("\n  " + paint("TIC / TAC / TOE", "1;36", color))
    print("  Small board. Thoughtful moves.")
    print("\n  Squares 1–9, arranged like the board. X always starts.")
    print("  Enter q to leave at any prompt. Unfinished rounds do not count.")
    print("  " + ("Session scores only (saving disabled)." if args.no_save else "Completed rounds are saved automatically."))
    while True:
        game = Game()
        names = {player_mark: args.name, "O" if player_mark == "X" else "X": opponent}
        print(f"\n  ROUND {round_number}  /  {names['X']} (X) vs {names['O']} (O)")
        if mode == "solo":
            print(f"  Computer difficulty: {args.difficulty}")
        while not game.over:
            print("\n" + render_board(game, color) + "\n")
            mark = game.turn
            if mode == "solo" and mark != player_mark:
                move = choose_move(game, args.difficulty)
                print(f"  Computer ({mark}) chooses {move + 1}.")
            else:
                answer = ask(f"  {names[mark]} ({mark}), choose a square [1–9]: ")
                if answer not in tuple("123456789"):
                    print("  Choose one number from 1 to 9, or q to quit.")
                    continue
                move = int(answer) - 1
            try:
                game = game.play(move)
            except ValueError as error:
                print(f"  {error}")
        print("\n" + render_board(game, color))
        if game.winner:
            print("\n  " + paint(f"{names[game.winner]} wins this round!", "1;32", color))
            result = "player" if game.winner == player_mark else "opponent"
        else:
            print("\n  A draw. Well matched!")
            result = "draw"
        if not args.no_save:
            store.record(matchup, result)
        totals[("player", "opponent", "draw").index(result)] += 1
        print(f"  Score: {args.name} {totals[0]}  |  {opponent} {totals[1]}  |  Draws {totals[2]}")
        while True:
            answer = ask("\n  Play again? [Y/n]: ").lower()
            if answer in ("n", "no"):
                return
            if answer in ("", "y", "yes"):
                break
            print("  Enter y for another round, n to finish, or q to quit.")
        player_mark = "O" if player_mark == "X" else "X"
        round_number += 1
        print("  Swapping marks so each player gets a turn to start.")


def menu(args, store):
    while True:
        print("\n  TIC / TAC / TOE\n  Small board. Thoughtful moves.\n")
        print("  1  Play the computer\n  2  Play a friend\n  3  Saved scoreboard\n  q  Quit\n")
        choice = ask("  Your choice: ")
        if choice in ("1", "2"):
            args.mode = "solo" if choice == "1" else "local"
            if choice == "1":
                while True:
                    difficulty = ask("  Difficulty [easy / medium / hard] (hard): ").lower() or "hard"
                    if difficulty in ("easy", "medium", "hard"):
                        args.difficulty = difficulty
                        break
                    print("  Choose easy, medium, or hard.")
            return
        if choice == "3":
            show_scores(store)
        else:
            print("  Choose 1, 2, 3, or q.")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Tic-Tac-Toe with local multiplayer, computer opponents, and saved scores.")
    result.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    result.add_argument("--mode", choices=("solo", "local"), help="play the computer or a friend")
    result.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="hard")
    result.add_argument("--name", type=player_name, default="Player 1", help="your scoreboard name")
    result.add_argument("--opponent", type=player_name, default="Player 2", help="second local player's name")
    result.add_argument("--mark", choices=("X", "O"), default="X", help="your mark in the first round (default: X)")
    result.add_argument("--scores", action="store_true", help="show saved scores and exit")
    result.add_argument("--data-dir", type=Path, default=None, help="directory for scores.sqlite3")
    result.add_argument("--no-save", action="store_true", help="play with session-only scores")
    result.add_argument("--no-color", action="store_true", help="disable terminal colors")
    return result


def main(argv=None) -> int:
    argument_parser = parser()
    args = argument_parser.parse_args(argv)
    store = ScoreStore(args.data_dir.expanduser() if args.data_dir else default_data_dir())
    color = (sys.stdout.isatty() and not args.no_color and "NO_COLOR" not in os.environ
             and os.environ.get("TERM") != "dumb" and sys.platform != "win32")
    try:
        if args.scores:
            show_scores(store)
            return 0
        if args.mode is None:
            if not sys.stdin.isatty():
                argument_parser.print_help()
                return 0
            menu(args, store)
        play(args, store, color)
        print("\n  Thanks for playing. See you next round!\n")
        return 0
    except (QuitGame, EOFError):
        print("\n  See you next round! Completed rounds stay on the scoreboard.\n")
        return 0
    except KeyboardInterrupt:
        print("\n  Game interrupted. Only completed rounds count.\n")
        return 130
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        print("Scores could not be read or saved. Check the data directory, or play with --no-save.", file=sys.stderr)
        return 1
