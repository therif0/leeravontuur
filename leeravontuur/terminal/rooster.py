"""Invullen in een rooster (cijferen onder elkaar) en de staartdeling stap voor stap.

Beide zijn 'invoer-objecten' voor terminal/oefenaar.py:
  teken(s, y, uitslag, hulp)  tekent (uitslag = None tijdens het invullen, anders True/False)
  toets(k)                    verwerkt een toets of klik; geeft None of (getypt antwoord, getal) als het kind klaar is
  hoogte(nagekeken), knoppen(), hint, melding, fouten, diagnose, cursor_pos, hulp(o), rijen()
"""

import curses

from ..kern.getal import lees_getal
from .scherm import BACKSPACE, ENTER, ESC

TAB = 9


class RoosterInvoer:
    X0 = 12

    def __init__(self, v, o):
        self.v, self.o, self.r = v, o, v.model
        self.cellen = [{} for _ in self.r.invul]
        self.onth = {}
        self.komma = None
        self.rij = 0
        self.kol = self.r.breedte - 1
        self.links = True  # typrichting: van rechts naar links
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = "Typ van rechts naar links · ↑ = onthouden-rij · Tab = volgende rij"

    # ---- vorm --------------------------------------------------------------------------
    def hoogte(self, nagekeken=False):
        n = len(self.r.invul)
        return 1 + len(self.r.gegeven) + 1 + n + (1 if n > 1 else 0)

    def rij_y(self, y):
        n = len(self.r.invul)
        eerste = y + 1 + len(self.r.gegeven) + 1
        uit = {-1: y}
        for i in range(n):
            uit[i] = eerste + i + (1 if n > 1 and i == n - 1 else 0)
        return uit

    def x(self, kol):
        return self.X0 + 2 * kol

    def knoppen(self):
        k = [("Enter", "klaar", 10), ("?/F1", "hulp", ord("?")), ("r", "richting", ord("r"))]
        if self.r.komma_zelf:
            k.append((",", "komma", ord(",")))
        return k + [("Esc", "stoppen", ESC)]

    # ---- tekenen ------------------------------------------------------------------------
    def teken(self, s, y, uitslag=None, hulp=False):
        r = self.r
        ys = self.rij_y(y)
        bezig = uitslag is None
        links, rechts = self.x(0) - 3, self.x(r.breedte - 1)
        # welke vakjes van de gegeven getallen oplichten bij hulp: {(rij, kolom)}
        licht = set()
        if hulp and bezig:
            n = len(r.invul)
            if r.teken != "×":
                licht = {(i, self.kol) for i in range(len(r.gegeven))}
            elif n == 1 or self.rij < n - 1:  # een maalrij: cijfer van boven × één cijfer van onder
                rij = max(self.rij, 0) if n > 1 else 0
                licht = {(0, self.kol + rij), (1, r.breedte - 1 - rij)}
        # onthouden-rij
        for c in range(r.breedte):
            tekst = self.onth.get(c, "·")
            rol = "cursor" if bezig and self.rij == -1 and c == self.kol else ("accent2" if c in self.onth else "dim")
            s.put(y, self.x(c), tekst, rol)
            if bezig:
                s.zones.voeg(y, self.x(c), 1, 1, ("cel", -1, c))
        if bezig and self.rij == -1:
            s.put(y, rechts + 3, "← onthouden", "dim")
        # de gegeven getallen
        for i, tekst in enumerate(r.gegeven):
            yy = y + 1 + i
            cellen, komma = r.plaats(tekst)
            for c, cijfer in cellen.items():
                s.put(yy, self.x(c), cijfer, "accent" if (i, c) in licht else "bold")
            if komma is not None:
                s.put(yy, self.x(komma) + 1, ",", "bold")
            if i == len(r.gegeven) - 1:
                s.put(yy, links, r.teken, "bold")
        s.put(y + 1 + len(r.gegeven), links, "─" * (rechts - links + 1), "dim")
        # de rijen om in te vullen
        n = len(r.invul)
        if n > 1:
            s.put(ys[n - 1] - 1, links, "+", "bold")
            s.put(ys[n - 1] - 1, links + 2, "─" * (rechts - links - 1), "dim")
        for i in range(n):
            yy = ys[i]
            laatste = i == n - 1
            for c in range(r.breedte):
                if bezig and self.rij == i and c == self.kol:
                    rol = "cursor"
                elif not bezig and laatste:
                    rol = "goedvak" if uitslag else "foutvak"
                else:
                    rol = "veld"
                s.put(yy, self.x(c), self.cellen[i].get(c, " "), rol)
                if bezig:
                    s.zones.voeg(yy, self.x(c), 1, 1, ("cel", i, c))
                    if laatste and r.komma_zelf and c < r.breedte - 1:
                        s.zones.voeg(yy, self.x(c) + 1, 1, 1, ("komma", c))
            komma = self.komma if r.komma_zelf else r.vaste_komma()
            if laatste and komma is not None:
                s.put(yy, self.x(komma) + 1, ",", "bold")
            if n > 1 and not laatste:
                s.put(yy, rechts + 3, r.invul[i], "dim")
        if bezig:
            pijl = "←" if self.links else "→"
            s.put(ys[n - 1], rechts + 3, f"uitkomst  (typrichting {pijl})", "dim")

    # ---- invoer -------------------------------------------------------------------------
    def rijen_lijst(self):
        return [-1] + list(range(len(self.r.invul)))

    def stap(self, richting):
        """Een vakje verder in de typrichting (richting = +1) of terug (−1)."""
        d = (-1 if self.links else 1) * richting
        self.kol = min(self.r.breedte - 1, max(0, self.kol + d))

    def toets(self, k):
        r = self.r
        rij_cellen = self.onth if self.rij == -1 else self.cellen[self.rij]
        if isinstance(k, tuple):
            if k[0] == "cel":
                self.rij, self.kol = k[1], k[2]
            elif k[0] == "komma":
                self.zet_komma(k[1])
            return None
        if k in ENTER:
            tekst, melding = r.lees(self.cellen[-1], self.komma)
            if tekst is None:
                self.melding, self.melding_rol = melding, "fout"
                return None
            return tekst, lees_getal(tekst)
        if k == curses.KEY_LEFT:
            self.kol = max(0, self.kol - 1)
        elif k == curses.KEY_RIGHT:
            self.kol = min(r.breedte - 1, self.kol + 1)
        elif k in (curses.KEY_UP, curses.KEY_DOWN):
            lijst = self.rijen_lijst()
            i = lijst.index(self.rij) + (-1 if k == curses.KEY_UP else 1)
            self.rij = lijst[max(0, min(len(lijst) - 1, i))]
        elif k == TAB:
            lijst = self.rijen_lijst()[1:]
            self.rij = lijst[(lijst.index(self.rij) + 1) % len(lijst)] if self.rij in lijst else lijst[0]
            self.kol = r.breedte - 1
        elif k in BACKSPACE:
            if self.kol not in rij_cellen:
                self.stap(-1)
            rij_cellen.pop(self.kol, None)
        elif k in (ord(" "), curses.KEY_DC):
            rij_cellen.pop(self.kol, None)
            self.stap(1)
        elif k in (ord("r"), ord("R")):
            self.links = not self.links
            self.melding, self.melding_rol = f"Typrichting: {'← van rechts naar links' if self.links else '→ van links naar rechts'}", "info"
            return None
        elif k == ord(","):
            if r.komma_zelf and self.rij == len(r.invul) - 1:
                self.zet_komma(self.kol)
            elif r.komma_zelf:
                self.melding, self.melding_rol = "De komma zet je in de uitkomst (de onderste rij).", "info"
                return None
            else:
                self.melding, self.melding_rol = "Bij + en − staat de komma al onder de komma.", "info"
                return None
        elif isinstance(k, int) and 48 <= k <= 57:
            rij_cellen[self.kol] = chr(k)
            self.stap(1)
        else:
            return None
        self.melding = ""
        return None

    def zet_komma(self, kol):
        self.komma = None if self.komma == kol or kol >= self.r.breedte - 1 else kol
        self.rij = len(self.r.invul) - 1

    def hulp(self, o):
        return o.kolom_hulp(self.v, self.rij, self.kol)

    def rijen(self):
        uit = []
        for i, cellen in enumerate(self.cellen):
            laatste = i == len(self.cellen) - 1
            uit.append(self.r.lees(cellen, self.komma if laatste else None)[0])
        return uit


class StaartInvoer:
    X0 = 8
    VENSTER = 7  # zoveel regels van de staartdeling passen tijdens het rekenen

    def __init__(self, v, o):
        self.v, self.o, self.m = v, o, v.model
        self.i = 0
        self.buf = ""
        self.pogingen = 0
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.hint = "Typ het antwoord op de stap en druk Enter. Zo bouw je de staartdeling op."

    def hoogte(self, nagekeken=False):
        return self.VENSTER + 2

    def knoppen(self):
        return [("Enter", "ok", 10), ("?/F1", "tip", ord("?")), ("Esc", "stoppen", ESC)]

    def teken(self, s, y, uitslag=None, hulp=False):
        m = self.m
        bezig = uitslag is None
        regels, quotient = m.beeld(self.i)
        venster = self.VENSTER if bezig else self.VENSTER + 2
        if len(regels) > venster:
            regels = [regels[0], "  ⋮"] + regels[-(venster - 2):]
        for j, regel in enumerate(regels):
            s.put(y + j, self.X0, regel, "bold" if j == 0 else "")
        xb = self.X0 + m.kolom(len(m.cijfers()) - 1) + 3
        for j in range(max(3, len(regels))):
            s.put(y + j, xb, "│" if j != 1 else "├", "dim")
        breed = max(len(str(m.deler)), len(quotient), 3) + 2
        s.put(y, xb + 2, str(m.deler), "bold")
        s.put(y + 1, xb + 1, "─" * breed, "dim")
        s.put(y + 2, xb + 2, quotient, "goed" if uitslag else "accent" if bezig else "fout")
        if not bezig and m.rest and not self.v.data.get("dec"):
            s.put(y + 3, xb + 2, f"rest {m.rest}", "accent")
        self.cursor_pos = None
        if bezig and self.i < len(m.stappen):
            st = m.stappen[self.i]
            yy = y + self.VENSTER + 1
            vraag = f"Stap {self.i + 1}: {st.vraag}"
            s.put(yy, 6, vraag, "bold")
            s.tekstvak(yy, 6 + len(vraag) + 2, self.buf, 6, "veld")
            self.cursor_pos = (yy, 6 + len(vraag) + 3 + len(self.buf))
            s.put(yy, 6 + len(vraag) + 12, "deel → maal → min → neer"[:max(0, 78 - len(vraag) - 18)], "dim")

    def toets(self, k):
        m = self.m
        if isinstance(k, tuple):
            return None
        if k in BACKSPACE:
            self.buf = self.buf[:-1]
            return None
        if isinstance(k, int) and 48 <= k <= 57 and len(self.buf) < 6:
            self.buf += chr(k)
            return None
        if k not in ENTER:
            return None
        if not self.buf:
            self.melding, self.melding_rol = "Typ eerst je antwoord.", "fout"
            return None
        st = m.stappen[self.i]
        gegeven = int(self.buf)
        self.buf = ""
        if gegeven == st.antwoord:
            self.melding, self.melding_rol = f"✔ {st.vraag.rstrip(' =?')} → {gegeven}", "goed"
            return self.verder()
        self.fouten += 1
        code, uitleg = self.o.stap_fout(self.v, st, gegeven)
        if self.diagnose is None:
            self.diagnose = (code, uitleg)
        self.pogingen += 1
        if self.pogingen >= 2:
            self.melding, self.melding_rol = f"! Het is {st.antwoord}. {uitleg}", "accent"
            return self.verder()
        self.melding, self.melding_rol = f"✘ {uitleg} Probeer nog eens.", "fout"
        return None

    def verder(self):
        self.i += 1
        self.pogingen = 0
        if self.i < len(self.m.stappen):
            return None
        tekst = self.v.verwacht + (f" ({self.fouten} {'fout' if self.fouten == 1 else 'fouten'} onderweg)"
                                   if self.fouten else "")
        return tekst, self.v.antwoord

    def hulp(self, o):
        if self.i < len(self.m.stappen):
            return self.m.stappen[self.i].tip
        return o.tip(self.v)

    def rijen(self):
        return []


INVOER = {"rooster": RoosterInvoer, "staart": StaartInvoer}
