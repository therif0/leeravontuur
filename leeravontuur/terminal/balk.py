"""Interactieve modellen als invoer-objecten voor terminal/oefenaar.py (zelfde vorm als terminal/rooster.py):
de breukbalk (arceren, noemer kiezen, vereenvoudigen).
"""

import curses

from ..kern.getal import GetypteBreuk
from ..kern.modellen import Breukbalk
from . import modellen as M
from .scherm import ENTER, ESC

NOEMER_MAX = 20


class BalkInvoer:
    X0 = 8

    def __init__(self, v, o):
        self.v, self.o = v, o
        self.noemer = v.model.noemer
        self.gearceerd = set(v.model.gearceerd)
        self.cursor = 0
        self.vast = bool(v.data.get("noemer_vast"))
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = ("←→ kies een stuk · spatie of klik = arceren" if self.vast else
                     "↑↓ noemer · ←→ stuk · spatie of klik = arceren · v = vereenvoudigen")

    def hoogte(self, nagekeken=False):
        return 5

    def knoppen(self):
        if self.vast:
            return [("spatie", "arceer", ord(" ")), ("Enter", "klaar", 10), ("?", "tip", ord("?")),
                    ("Esc", "stoppen", ESC)]
        return [("spatie", "arceer", ord(" ")), ("↑", "", curses.KEY_UP), ("↓", "noemer", curses.KEY_DOWN),
                ("v", "vereenvoudig", ord("v")), ("Enter", "ok", 10), ("Esc", "stop", ESC)]

    def teken(self, s, y, uitslag=None, hulp=False):
        bezig = uitslag is None
        y += 1  # onder het maatje
        rechts = M.teken_balk(s, y, self.noemer, self.gearceerd, self.X0,
                              actie=(lambda i: ("stuk", i)) if bezig else None)
        teller = len(self.gearceerd)
        rol = "bold" if bezig else ("goed" if uitslag else "fout")
        s.put(y, rechts + 3, f"{teller}/{self.noemer}", rol)
        if bezig:
            a, b = M.stuk_grenzen(self.noemer, self.X0)[self.cursor]
            s.put(y + 2, (a + b) // 2, "▲", "accent")
            s.put(y + 3, self.X0, f"{self.noemer} stukken" + ("" if self.vast else "  (↑↓ om te veranderen)"), "dim")

    def toets(self, k):
        if isinstance(k, tuple):
            if k[0] == "stuk":
                self.cursor = k[1]
                self.wissel()
            return None
        if k in ENTER:
            if not self.gearceerd:
                self.melding, self.melding_rol = "Arceer eerst een of meer stukken.", "fout"
                return None
            t = len(self.gearceerd)
            return f"{t}/{self.noemer}", GetypteBreuk(0, t, self.noemer)
        self.melding = ""
        if k == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
        elif k == curses.KEY_RIGHT:
            self.cursor = min(self.noemer - 1, self.cursor + 1)
        elif k == ord(" "):
            self.wissel()
        elif k in (curses.KEY_UP, curses.KEY_DOWN) and not self.vast:
            nieuw = self.noemer + (1 if k == curses.KEY_UP else -1)
            if 1 <= nieuw <= NOEMER_MAX:
                self.noemer = nieuw
                self.gearceerd = {i for i in self.gearceerd if i < nieuw}
                self.cursor = min(self.cursor, nieuw - 1)
        elif k in (ord("v"), ord("V")) and not self.vast:
            balk = Breukbalk(self.noemer, set(range(len(self.gearceerd)))).vereenvoudig()
            if balk is None:
                self.melding, self.melding_rol = "! Dit kan niet eenvoudiger.", "info"
            else:
                self.melding, self.melding_rol = (f"Samengevoegd: {len(self.gearceerd)}/{self.noemer} = "
                                                  f"{balk.teller}/{balk.noemer}"), "info"
                self.noemer, self.gearceerd = balk.noemer, set(balk.gearceerd)
                self.cursor = min(self.cursor, self.noemer - 1)
        return None

    def wissel(self):
        self.gearceerd ^= {self.cursor}

    def hulp(self, o):
        return o.tip(self.v)

    def rijen(self):
        return []


INVOER = {"balk": BalkInvoer}
