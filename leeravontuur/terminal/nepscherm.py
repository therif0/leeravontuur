"""Een nagemaakt curses-venster om schermen te testen zonder echte terminal (ook in CI op Windows/macOS).

Toetsen geef je op als tekens ("a", "\\n"), curses-codes (curses.KEY_DOWN) of muisacties:
("klik", y, x) en ("wiel", 1) of ("wiel", -1). ("wacht",) doet alsof er even niets getypt wordt.
("grootte", h, w) maakt het venster h × w (zoals een gebruiker die het venster versleept).

Tekent een scherm heel vaak zonder op een toets te wachten, dan hangt het: dat geeft een fout (HangtFout).
"""

import curses

from .venster import Klokvenster


class ToetsenOp(Exception):
    """Alle opgegeven toetsen zijn gebruikt."""


class HangtFout(Exception):
    """Het scherm wordt steeds opnieuw getekend zonder dat het op een toets wacht (een eindeloze lus)."""


MAX_ZONDER_TOETS = 200


class NepScherm:
    nep = True

    def __init__(self, toetsen=(), hoogte=24, breedte=80):
        self.h, self.w = hoogte, breedte
        self.toetsen = list(toetsen)
        self.raster = [[" "] * breedte for _ in range(hoogte)]
        self.beelden = []  # tekst van elk getoond scherm (bij elke refresh)
        self._muis = (0, 0, 0, 0, 0)
        self._zonder_toets = 0

    # --- wat curses ook heeft ---
    def getmaxyx(self):
        return self.h, self.w

    def keypad(self, aan):
        pass

    def timeout(self, ms):
        pass

    def erase(self):
        self.raster = [[" "] * self.w for _ in range(self.h)]

    def addstr(self, y, x, s, attr=0):
        if not (0 <= y < self.h and 0 <= x < self.w):
            raise curses.error("buiten het scherm")
        for i, ch in enumerate(s):
            if x + i >= self.w:
                raise curses.error("buiten het scherm")
            self.raster[y][x + i] = ch

    def move(self, y, x):
        pass

    def refresh(self):
        self._zonder_toets += 1
        if self._zonder_toets > MAX_ZONDER_TOETS:
            raise HangtFout(f"{MAX_ZONDER_TOETS} keer getekend zonder op een toets te wachten")
        tekst = self.tekst()
        if not self.beelden or self.beelden[-1] != tekst:
            self.beelden.append(tekst)

    def get_wch(self):
        self._zonder_toets = 0
        if not self.toetsen:
            raise ToetsenOp()
        k = self.toetsen.pop(0)
        if isinstance(k, tuple):
            if k[0] == "wacht":
                raise curses.error("geen toets")
            if k[0] == "grootte":
                self.h, self.w = k[1], k[2]
                self.erase()
                return curses.KEY_RESIZE
            if k[0] == "klik":
                self._muis = (0, k[2], k[1], 0, curses.BUTTON1_PRESSED)
            elif k[0] == "wiel":
                knop = getattr(curses, "BUTTON5_PRESSED", 0x200000) if k[1] > 0 \
                    else getattr(curses, "BUTTON4_PRESSED", 0x10000)
                self._muis = (0, 0, 0, 0, knop)
            return curses.KEY_MOUSE
        return k

    def getmouse(self):
        return self._muis

    # --- hulp voor tests ---
    def tekst(self):
        return "\n".join("".join(r).rstrip() for r in self.raster)

    def zoek(self, woord):
        """(y, x) van de eerste plek waar dit woord op het scherm staat, of None."""
        for y, r in enumerate(self.raster):
            x = "".join(r).find(woord)
            if x >= 0:
                return y, x
        return None


class NepKlokvenster(Klokvenster):
    """Een klokvenster zonder proces, voor schermtests: bewaart wat het venster kreeg, en geeft `berichten`
    (bv. {"klik": [0, -50]} of {"toets": "Enter"}) door zodra het venster te zien is, zoals een echt kind."""

    def __init__(self, berichten=()):
        super().__init__()
        self.wacht = list(berichten)
        self.gekregen = []

    def _start(self):
        self.proc = True
        return True

    def _stuur(self, **bericht):
        self.gekregen.append(bericht)
        return True

    def stop(self):
        self.proc = None

    def volgende(self):
        if self.zichtbaar and self.wacht and self.uit.empty():
            self.uit.put(self.wacht.pop(0))
        return super().volgende()
