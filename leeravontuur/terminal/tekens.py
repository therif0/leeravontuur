"""Terugval naar gewone ASCII-tekens voor terminals zonder UTF-8.

Elk speciaal teken wordt vervangen door precies één gewoon teken, zodat alles op zijn plaats blijft.
"""

import locale
import sys

_ASCII = {
    "─": "-", "│": "|", "┌": "+", "┐": "+", "└": "+", "┘": "+", "├": "+", "┤": "+",
    "┬": "+", "┴": "+", "┼": "+", "═": "=", "║": "|",
    "✔": "v", "✘": "x", "●": "*", "○": "o", "◉": "@", "•": "*", "·": "-", "›": ">",
    "▼": "v", "▲": "^", "→": ">", "←": "<", "↑": "^", "↓": "v", "×": "x",
    "█": "#", "░": ".", "▀": '"', "▄": "_", "“": '"', "”": '"', "‘": "'", "’": "'",
    "…": ".", "≈": "~", "²": "2", "³": "3",
}
TABEL = str.maketrans(_ASCII)


def naar_ascii(s):
    return s.translate(TABEL)


def ascii_nodig():
    """True als de terminal waarschijnlijk geen UTF-8 kan tonen."""
    codering = (getattr(sys.stdout, "encoding", None) or locale.getpreferredencoding(False) or "").lower()
    return "utf" not in codering
