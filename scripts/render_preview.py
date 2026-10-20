"""Generate a dependency-free SVG preview from the actual terminal board."""

from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tic_tac_toe.cli import render_board
from tic_tac_toe.game import Game


def main():
    board = render_board(Game(tuple("XXXOO    "))).splitlines()
    lines = [
        ("TIC / TAC / TOE", "#72e1d1"),
        ("Small board. Thoughtful moves.", "#a8b7cb"),
        ("", "#fff"),
        ("ROUND 3  /  Alex (X) vs Sam (O)", "#edf2f9"),
        ("", "#fff"),
        *[(line, "#72e1d1" if index == 0 else "#edf2f9") for index, line in enumerate(board)],
        ("", "#fff"),
        ("Alex wins this round!", "#94e3a1"),
        ("Score: Alex 2  |  Sam 0  |  Draws 1", "#edf2f9"),
        ("", "#fff"),
        ("Play again? [Y/n]: _", "#a8b7cb"),
    ]
    height = 106 + len(lines) * 26
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="{height}" viewBox="0 0 780 {height}">',
             '<title>Tic-Tac-Toe terminal preview</title>',
             '<desc>Alex wins with three Xs across the top row. Sample score: Alex two, Sam zero, one draw.</desc>',
             f'<rect width="780" height="{height}" rx="18" fill="#101923"/>',
             '<text x="32" y="34" fill="#8396ae" font-size="12" font-family="monospace">TIC-TAC-TOE / LOCAL TWO-PLAYER</text>',
             '<path d="M32 52H748" stroke="#2c3b4e"/>']
    for index, (line, color) in enumerate(lines):
        parts.append(f'<text x="36" y="{88 + index * 26}" fill="{color}" font-size="18" font-family="monospace" xml:space="preserve">{escape(line)}</text>')
    parts.append("</svg>")
    destination = ROOT / "docs/preview.svg"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(destination)


if __name__ == "__main__":
    main()
