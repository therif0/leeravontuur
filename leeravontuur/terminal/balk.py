"""Interactieve modellen als invoer-objecten voor terminal/oefenaar.py (zelfde vorm als terminal/rooster.py):
de breukbalk (arceren, noemer kiezen, vereenvoudigen), het honderdveld (vakjes kleuren), de schatkaart
(een kruisje zetten) en de wijzerklok (de wijzers zetten).
"""

import curses
import math
from decimal import Decimal

from ..kern.getal import GetypteBreuk
from dataclasses import replace

from ..kern.modellen import Breukbalk, Wijzerklok
from ..kern.wiskunde.grootheden import klok_tekst
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


class VeldInvoer:
    """Het honderdveld: vakjes kleuren met de pijltjes en spatie, een hele rij met r, of met de muis."""
    X0 = 10

    def __init__(self, v, o):
        self.v, self.o = v, o
        self.gekleurd = set(v.model.gekleurd)
        self.cursor = 0
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = "Pijltjes + spatie (of klik) = vakje · r (of klik op ▶) = hele rij"
        self.naast = (13, self.X0 + 23)  # (rij, kolom) van de feedback: rechts van het veld

    def hoogte(self, nagekeken=False):
        return 10

    def knoppen(self):
        return [("spatie", "kleur", ord(" ")), ("r", "hele rij", ord("r")), ("Enter", "klaar", 10),
                ("?", "tip", ord("?")), ("Esc", "stoppen", ESC)]

    def teken(self, s, y, uitslag=None, hulp=False):
        bezig = uitslag is None
        y += 1  # onder het maatje
        M.teken_veld(s, y, self.gekleurd, self.X0, self.cursor if bezig else None,
                     (lambda i: ("vak", i)) if bezig else None, (lambda r: ("rij", r)) if bezig else None)
        n = len(self.gekleurd)
        s.put(y, self.X0 + 23, f"{n} van de 100", "bold" if bezig else ("goed" if uitslag else "fout"))
        s.put(y + 1, self.X0 + 23, f"= {n} %", "bold" if bezig else ("goed" if uitslag else "fout"))

    def toets(self, k):
        if isinstance(k, tuple):
            if k[0] == "vak":
                self.cursor = k[1]
                self.gekleurd ^= {k[1]}
            elif k[0] == "rij":
                self.cursor = k[1] * 10
                self.rij()
            return None
        if k in ENTER:
            n = len(self.gekleurd)
            return f"{n} %", Decimal(n)
        stap = {curses.KEY_LEFT: (0, -1), curses.KEY_RIGHT: (0, 1), curses.KEY_UP: (-1, 0), curses.KEY_DOWN: (1, 0)}
        if k in stap:
            r, c = divmod(self.cursor, 10)
            dr, dc = stap[k]
            self.cursor = min(9, max(0, r + dr)) * 10 + min(9, max(0, c + dc))
        elif k == ord(" "):
            self.gekleurd ^= {self.cursor}
        elif k in (ord("r"), ord("R")):
            self.rij()
        return None

    def rij(self):
        """Kleur de rij van de cursor helemaal (of maak ze leeg als ze al vol is)."""
        rij = set(range(self.cursor // 10 * 10, self.cursor // 10 * 10 + 10))
        self.gekleurd = self.gekleurd - rij if rij <= self.gekleurd else self.gekleurd | rij

    def hulp(self, o):
        return o.tip(self.v)

    def rijen(self):
        return []


class CoordInvoer:
    """De schatkaart of het assenstelsel: zet een kruisje met de pijltjes en Enter, of met een klik."""
    X0 = 8

    def __init__(self, v, o):
        self.v, self.o = v, o
        self.kaart = v.model
        xs, ys = self.kaart.xs(), self.kaart.ys()
        self.cursor = (xs[len(xs) // 2], ys[len(ys) // 2])
        self.gekozen = None
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = "Pijltjes = kruisje verplaatsen · Enter (of klik) = hier!"
        self.naast = (10, self.X0 + 3 + 3 * len(xs) + 4)

    def hoogte(self, nagekeken=False):
        return len(self.kaart.ys()) + 1

    def knoppen(self):
        return [("←→↑↓", "verplaats", None), ("Enter", "hier!", 10), ("?", "tip", ord("?")), ("Esc", "stoppen", ESC)]

    def teken(self, s, y, uitslag=None, hulp=False):
        bezig = uitslag is None
        punten = dict(self.kaart.punten)
        if not bezig and self.gekozen:
            if not uitslag:
                punten[(self.v.data["x"], self.v.data["y"])] = ("●", "goed")
            punten[self.gekozen] = ("✔", "goed") if uitslag else ("✘", "fout")
        M.teken_kaart(s, y + 1, replace(self.kaart, punten=punten), self.X0, self.cursor if bezig else None,
                      (lambda x, yy: ("punt", x, yy)) if bezig else None)
        if bezig:
            s.put(y + 1, self.naast[1], "Jij: " + self.kaart.naam(*self.cursor), "bold")

    def toets(self, k):
        if isinstance(k, tuple):
            if k[0] == "punt":
                self.cursor = (k[1], k[2])
                return self.kies()
            return None
        if k in ENTER:
            return self.kies()
        xs, ys = self.kaart.xs(), self.kaart.ys()
        stap = {curses.KEY_LEFT: (-1, 0), curses.KEY_RIGHT: (1, 0), curses.KEY_UP: (0, 1), curses.KEY_DOWN: (0, -1)}
        if k in stap:
            dx, dy = stap[k]
            x, y = self.cursor
            self.cursor = (min(xs[-1], max(xs[0], x + dx)), min(ys[-1], max(ys[0], y + dy)))
        return None

    def kies(self):
        self.gekozen = self.cursor
        naam = self.kaart.naam(*self.cursor)
        return naam, naam

    def hulp(self, o):
        return o.tip(self.v)

    def rijen(self):
        return []


class KlokInvoer:
    """De wijzers van een klok zetten: ←→ per minuut, ↑↓ per 5 minuten, + en − per uur, of klik waar de lange
    wijzer moet staan. De uurwijzer draait mee, zoals op een echte klok."""
    X0 = 8

    def __init__(self, v, o):
        self.v, self.o = v, o
        self.t = int(v.model.minuten) % 720
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = "←→ 1 min · ↑↓ 5 min · + − 1 uur · klik of sleep de lange wijzer · Enter"
        self.naast = (10, self.X0 + 25 + 4)
        self.h = 13

    def hoogte(self, nagekeken=False):
        return self.h

    def knoppen(self):
        return [("←→↑↓", "draaien", None), ("Enter", "zo staat hij goed", 10), ("?", "tip", ord("?")),
                ("Esc", "stoppen", ESC)]

    def teken(self, s, y, uitslag=None, hulp=False):
        h, _ = M.teken_klok(s, y + 1, Wijzerklok(self.t), self.X0,
                            (lambda dx, dy: ("wijzer", dx, dy)) if uitslag is None else None, uitslag=uitslag,
                            juist=self.v.antwoord if uitslag is False else None, tekst=self.v.tekst)
        venster = h < 13  # de klok staat in het klokvenster: de feedback komt dan gewoon eronder
        self.h, self.naast = (h + 1, None) if venster else (13, (10, self.X0 + 25 + 4))

    def toets(self, k):
        if isinstance(k, tuple):
            if k[0] == "wijzer" and (k[1] or k[2]):
                hoek = math.degrees(math.atan2(k[1], -k[2])) % 360
                minuut = round(hoek / 6) % 60
                uur = self.t // 60
                if self.t % 60 >= 45 and minuut < 15:   # voorbij 12: een uur later
                    uur += 1
                elif self.t % 60 < 15 and minuut >= 45:  # terug voorbij 12: een uur vroeger
                    uur -= 1
                self.t = (uur * 60 + minuut) % 720
            return None
        stap = {curses.KEY_LEFT: -1, curses.KEY_RIGHT: 1, curses.KEY_UP: 5, curses.KEY_DOWN: -5,
                ord("+"): 60, ord("="): 60, ord("-"): -60, ord("−"): -60}.get(k)
        if stap:
            self.t = (self.t + stap) % 720
            return None
        if k in ENTER:
            return klok_tekst(self.t), Decimal(self.t)
        return None

    def hulp(self, o):
        return o.tip(self.v)

    def rijen(self):
        return []


INVOER = {"balk": BalkInvoer, "veld": VeldInvoer, "coord": CoordInvoer, "wijzers": KlokInvoer}
