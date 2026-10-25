"""Terugval naar gewone ASCII-tekens voor terminals zonder UTF-8.

Elk speciaal teken wordt vervangen door precies één gewoon teken, zodat alles op zijn plaats blijft.
"""

import locale
import sys
import unicodedata

_ASCII = {
    "─": "-", "│": "|", "┌": "+", "┐": "+", "└": "+", "┘": "+", "├": "+", "┤": "+",
    "┬": "+", "┴": "+", "┼": "+", "═": "=", "║": "|",
    "✔": "v", "✘": "x", "●": "*", "○": "o", "◉": "@", "•": "*", "·": "-", "›": ">",
    "▼": "v", "▲": "^", "▶": ">", "◀": "<", "→": ">", "←": "<", "↑": "^", "↓": "v", "×": "x",
    "█": "#", "━": "=", "╋": "#", "░": ".", "▀": '"', "▄": "_", "“": '"', "”": '"', "‘": "'", "’": "'",
    "…": ".", "≈": "~", "²": "2", "³": "3", "★": "*", "☆": "*", "−": "-", "÷": ":",
    "⋮": ":", "°": "o", "↔": "-", "■": "#", "□": ".", "€": "E", "«": '"', "»": '"', "–": "-", "—": "-",
    "œ": "o", "Œ": "O", "æ": "a", "Æ": "A", "ß": "s",  # 1-op-1 (geen 'oe'): de tekst moet op zijn plaats blijven
}
TABEL = str.maketrans(_ASCII)


def _gewoon(ch):
    """Een letter met een accent wordt de letter zelf (é → e); iets anders onbekends wordt '?'."""
    if ord(ch) < 128:
        return ch
    basis = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
    return basis[:1] if len(basis) >= 1 and unicodedata.category(ch).startswith("L") else "?"


def naar_ascii(s):
    s = s.translate(TABEL)
    if s.isascii():
        return s
    return "".join(_gewoon(c) for c in s)


def ascii_nodig():
    """True als de terminal waarschijnlijk geen UTF-8 kan tonen."""
    codering = (getattr(sys.stdout, "encoding", None) or locale.getpreferredencoding(False) or "").lower()
    return "utf" not in codering
