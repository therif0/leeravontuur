"""Een nagemaakt curses-venster om schermen te testen zonder echte terminal (ook in CI op Windows/macOS).

Toetsen geef je op als tekens ("a", "\\n"), curses-codes (curses.KEY_DOWN) of muisacties:
("klik", y, x) en ("wiel", 1) of ("wiel", -1).
"""

import curses


class ToetsenOp(Exception):
    """Alle opgegeven toetsen zijn gebruikt."""


class NepScherm:
    nep = True

    def __init__(self, toetsen=(), hoogte=24, breedte=80):
        self.h, self.w = hoogte, breedte
        self.toetsen = list(toetsen)
        self.raster = [[" "] * breedte for _ in range(hoogte)]
        self.beelden = []  # tekst van elk getoond scherm (bij elke refresh)
        self._muis = (0, 0, 0, 0, 0)

    # --- wat curses ook heeft ---
    def getmaxyx(self):
        return self.h, self.w

    def keypad(self, aan):
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
        tekst = self.tekst()
        if not self.beelden or self.beelden[-1] != tekst:
            self.beelden.append(tekst)

    def get_wch(self):
        if not self.toetsen:
            raise ToetsenOp()
        k = self.toetsen.pop(0)
        if isinstance(k, tuple):
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
