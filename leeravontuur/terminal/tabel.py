"""Maten (eenheden omzetten) als invoer-objecten voor terminal/oefenaar.py: een getal typen ("eenheid") of de
eenhedentabel invullen ("tabel").

Beide tekenen het hele scherm onder de voortgang zelf (`eigen_scherm`); de Oefenaar doet de rest (de voortgang, het
maatje, nakijken, bewaren, de reeks, het resultaat). Bovenop de gewone haakjes van een invoer-object:
  teken(s, goed)                       tekent (goed = None tijdens het invullen)
  toets(k)                             None of (getypt antwoord, getal) als het kind klaar is
  nagekeken(goed, d, tijd, punten, lof, uitleg)   na het nakijken: wat er onder de vraag komt
  lof, springt, maatje_ruim, denkt, volgende, hulp_gebruikt, wil_spiekbrief, extra, uitslag
"""

import curses
import textwrap

from ..kern.getal import fmt, lees_getal
from ..kern.wiskunde import eenheden as E
from .scherm import BACKSPACE, ENTER, ESC, HULP

TABEL_X, TABEL_Y = 12, 7


class _Maat:
    eigen_scherm = True
    geen_tweede_kans = True
    vraag_is_zin = True  # "3 km = ? m" eindigt niet op een vraagteken, maar is wel de hele vraag
    volgende = "volgende vraag"
    lof = springt = maatje_ruim = True

    def __init__(self, v, o):
        self.v, self.o, self.om = v, o, E.omzetting(v)
        self.app = None   # de Oefenaar zet het (typrichting, bewaren)
        self.vrij = False  # de Oefenaar zet het: F1 (tip, spiekbrief) alleen bij vrij oefenen
        self.s = None
        self.hulp_gebruikt = self.wil_spiekbrief = False
        self.extra, self.uitslag = None, None
        self.goed = self.d = None
        self.tijd = self.punten = self.lof_tekst = ""
        self.uitleg_na = True

    @property
    def denkt(self):
        return False

    def nagekeken(self, goed, d, tijd, punten, lof, uitleg_na):
        self.goed, self.d, self.tijd, self.punten, self.lof_tekst, self.uitleg_na = goed, d, tijd, punten, lof, uitleg_na


class EenheidInvoer(_Maat):
    """Een getal typen: 3 km = [     ] m."""

    def __init__(self, v, o):
        super().__init__(v, o)
        self.buf, self.melding, self.tip = "", "", False

    @property
    def denkt(self):
        return self.tip

    def knoppen(self):
        k = [("Enter", "controleren", 10), ("Esc", "stoppen", ESC)]
        if self.vrij:
            k.insert(1, ("F1", "spiekbrief" if self.tip else "tip", HULP))
        return k

    def teken(self, s, goed):
        self.s = s
        v = self.om
        y, x = 6, 6
        links = f"{fmt(v.getal)} {v.van}  =  "
        s.put(y, x, links, "bold")
        vx = x + len(links)
        rol = "veld" if goed is None else ("goedvak" if goed else "foutvak")
        s.tekstvak(y, vx, self.buf, 14, rol)
        s.put(y, vx + 17, v.naar, "bold")
        if goed is None:
            s.put(y + 3, x, self.melding, "fout")
            if self.tip:
                s.put(y + 3, x, "Tip: " + E.regel_uitleg(v)[0], "accent")
                s.put(y + 4, x, "Nog hulp nodig? Druk nog eens F1: je spiekbrief.", "dim")
            s.put(y + 6, x, "Kommagetal? Gebruik een komma: 0,25", "dim")
            s.cursor(True, y, vx + 1 + len(self.buf))
        elif not self.uitleg_na:  # zonder hulp (later een examen): niet zeggen of het juist was
            s.cursor(False)
            s.put(y + 3, x, "Je antwoord is bewaard.", "info")
        else:
            s.cursor(False)
            if goed:
                s.put(y + 3, x, "✔ " + self.lof_tekst + self.tijd + self.punten, "goed")
                uitleg = E.regel_uitleg(v) + E.tabel_uitleg(v) if self.vrij else []
            else:
                s.put(y + 3, x, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.{self.tijd}", "fout")
                d = E.diagnose(v, lees_getal(self.buf))
                uitleg = ([d[1]] if d else []) + E.regel_uitleg(v)[:1]
                if self.vrij:
                    uitleg += E.regel_uitleg(v)[1:] + E.tabel_uitleg(v)
            yy = y + 5
            for regel in uitleg:
                for stuk in textwrap.wrap(regel, 70):
                    s.put(yy, x, stuk, "accent")
                    yy += 1

    def toets(self, k):
        if k == HULP and self.vrij and self.tip:  # na de tip: de spiekbrief (#20); Esc = terug naar de vraag
            self.wil_spiekbrief = True
        elif k == HULP and self.vrij:
            self.tip = self.hulp_gebruikt = True
        elif k in ENTER:
            getal = lees_getal(self.buf)
            if getal is None:
                self.tip = False
                self.melding = ("Typ eerst je antwoord." if not self.buf.strip()
                                else "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25.")
                return None
            return self.buf, getal
        else:  # ook ("teken", ch): een getypt teken met de code van een curses-toets
            self.buf = self.s.bewerk(self.buf, k)
            self.melding = ""
        return None


class TabelInvoer(_Maat):
    """De eenhedentabel: cijfers in de vakjes, de komma verzetten, dan het antwoord aflezen."""
    volgende = "volgende oefening"
    lof = springt = maatje_ruim = False

    def __init__(self, v, o):
        super().__init__(v, o)
        om = self.om
        self.n = len(E.TABELLEN[om.cat])
        self.komma_van, self.komma_naar = E.kolom(om.cat, om.van), E.kolom(om.cat, om.naar)
        self.cellen, self.antw, self.pos, self.laatste_cel = [None] * self.n, "", 0, 0
        self.melding, self.oordeel, self.eigen_komma = "", None, None
        self.net_getypt = None  # vakje van het laatst getypte cijfer: daar komt een , achter
        self.tabel_ok = False

    @property
    def buf(self):
        return self.antw

    def knoppen(self):
        return [("Tab", "verder", 9), ("←", "terug", curses.KEY_LEFT), (",", "komma", ord(",")),
                ("↓", "antwoord", curses.KEY_DOWN), ("Enter", "nakijken", 10), ("Esc", "stop", ESC)]

    def teken(self, s, goed):
        self.s = s
        v, n, inst = self.om, self.n, self.app.inst
        cw = E.cw(v.cat)
        kop_hoogte = 2 if E.ALIASSEN.get(v.cat) else 1
        x = 4
        for stuk, rol in ((fmt(v.getal) + " ", "bold"), (v.van, "accent"), ("  =  ?  ", "bold"), (v.naar, "accent2")):
            s.put(4, x, stuk, rol)
            x += len(stuk)
        s.put(5, 4, f"Komma achter {v.van} · nullen aanvullen tot {v.naar} · zet met , de komma achter {v.naar}", "dim")
        if goed is None:
            pijl = "→ naar rechts" if inst.typrichting == 1 else "← naar links"
            s.put(6, 4, "Typrichting: ", "dim")
            s.put(6, 17, pijl, "accent")
            s.put(6, 32, "(r = omdraaien)", "dim")
            s.zones.voeg(6, 4, 1, 43, ("richting",))
        komma_ok = self.eigen_komma == self.komma_naar
        rijen = [("Jij", self.cellen, self.komma_van, self.oordeel, self.eigen_komma, goed is not None and not komma_ok)]
        if goed is not None:
            verw = E.verwachte_cijfers(v)
            rijen.append(("Juist", [verw.get(k) for _, k, _ in E.TABELLEN[v.cat]], self.komma_naar, None, None, False))
        ya = teken_tabel(s, TABEL_Y, TABEL_X, v, rijen, self.pos if goed is None and self.pos < n else None,
                         klikbaar=goed is None) + 1
        s.put(ya, 4, "Antwoord:", "bold")
        if goed is None:
            rol = "cursor" if self.pos == n else "veld"
        else:
            rol = "goedvak" if goed else "foutvak"
        s.tekstvak(ya, 15, self.antw, 14, rol, ("cel", n) if goed is None else None)
        s.put(ya, 33, v.naar, "accent2")
        if goed is None:
            if self.eigen_komma is not None:
                gelezen = E.aflezen(self.cellen, self.eigen_komma)
                plek = E.eenheid_bij(v.cat, self.eigen_komma) or "dit vakje"
                if gelezen is None:
                    tekst = "Zet eerst cijfers in de tabel."
                elif E.eenheid_bij(v.cat, self.eigen_komma):
                    tekst = f"Aflezen met de komma achter {plek}: {gelezen} {plek}"
                else:
                    tekst = f"Aflezen: {gelezen}, maar bij {plek} hoort geen eenheid."
                s.put(ya + 2, 4, tekst, "accent2")
            s.put(ya + 3, 4, self.melding, "fout")
            if self.pos < n:
                s.cursor(True, TABEL_Y + 2 + kop_hoogte, TABEL_X + 1 + self.pos * (cw + 1) + cw // 2)
            else:
                s.cursor(True, ya, 16 + len(self.antw))
            return
        s.cursor(False)
        cijfers_ok = all(o is not False for o in self.oordeel)
        if goed:
            s.put(ya + 2, 4, "✔ Je antwoord is juist!" + self.tijd + self.punten, "goed")
        else:
            s.put(ya + 2, 4, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.{self.tijd}", "fout")
        yy = ya + 3
        if self.tabel_ok:
            s.put(yy, 4, "✔ Je tabel en je komma zijn juist.", "goed")
            yy += 1
        if not cijfers_ok:
            s.put(yy, 4, "✘ Kijk naar de vakjes met ! : de rij 'Juist' toont hoe het moet.", "fout")
            yy += 1
        if self.eigen_komma is None:
            s.put(yy, 4, f"✘ Je hebt de komma niet verzet: die moet achter {v.naar}.", "fout")
            yy += 1
        elif not komma_ok:
            s.put(yy, 4, f"✘ Je komma stond achter {E.eenheid_bij(v.cat, self.eigen_komma) or 'een leeg vakje'}, "
                  f"maar moest achter {v.naar}.", "fout")
            yy += 1
        s.put(yy, 4, E.regel_uitleg(v)[0], "accent")
        s.put(yy + 1, 4, f"De komma springt van {v.van} naar {v.naar}: lees af → {fmt(v.antwoord)} {v.naar}.",
              "accent")

    def toets(self, k):
        n, inst = self.n, self.app.inst
        self.melding = ""
        vorig_getypt, self.net_getypt = self.net_getypt, None
        if isinstance(k, tuple):
            if k[0] == "cel":
                self.pos = k[1]
            elif k[0] == "komma":
                self.eigen_komma = None if self.eigen_komma == k[1] else k[1]
            elif k[0] == "richting":
                inst.typrichting = -inst.typrichting
                self.app.bewaar()
            if self.pos < n:
                self.laatste_cel = self.pos
            return None
        if k in (9, curses.KEY_RIGHT):
            self.pos = (self.pos + 1) % (n + 1)
        elif k in (curses.KEY_BTAB, curses.KEY_LEFT):
            self.pos = (self.pos - 1) % (n + 1)
        elif k == curses.KEY_DOWN:
            self.pos = n
        elif k == curses.KEY_UP and self.pos == n:
            self.pos = self.laatste_cel
        elif k in ENTER:
            getal = lees_getal(self.antw)
            if not self.antw.strip():
                self.melding = "Vul ook je antwoord in (met ↓ of Tab ga je naar het antwoordvak)."
                self.pos = n
            elif getal is None:
                self.melding = "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25."
                self.pos = n
            else:
                self.oordeel = E.controleer_tabel(self.om, self.cellen)
                komma_ok = self.eigen_komma == self.komma_naar
                cijfers_ok = all(o is not False for o in self.oordeel)
                self.tabel_ok = cijfers_ok and komma_ok
                self.extra = {"cijfers_ok": cijfers_ok, "komma_ok": komma_ok, "cellen": self.cellen,
                              "komma": self.eigen_komma}
                self.uitslag = {"tabel": self.tabel_ok}
                return self.antw, getal
        elif k in (ord("r"), ord("R")) and self.pos < n:
            inst.typrichting = -inst.typrichting
            self.app.bewaar()
        elif self.pos < n:
            if ord("0") <= k <= ord("9"):
                self.cellen[self.pos] = k - ord("0")
                self.net_getypt = self.pos
                self.pos = max(0, min(self.pos + inst.typrichting, n - 1))
            elif k in BACKSPACE:
                terug = self.pos - inst.typrichting
                if self.cellen[self.pos] is None and 0 <= terug < n:
                    self.pos = terug
                self.cellen[self.pos] = None
            elif k in (curses.KEY_DC, ord(" ")):
                self.cellen[self.pos] = None
            elif k in (ord(","), ord(".")):
                plek = self.pos if vorig_getypt is None else vorig_getypt
                self.eigen_komma = None if self.eigen_komma == plek else plek
        else:
            self.antw = self.s.bewerk(self.antw, k)
        if self.pos < n:
            self.laatste_cel = self.pos
        return None


def teken_tabel(s, y, x, v, rijen, actief=None, klikbaar=False):
    """De eenhedentabel: koppen (met de aliassen ha, l … op een tweede kopregel) en een rij per (label, cellen, komma,
    oordeel, eigen komma, kommafout). Geeft de rij onder de tabel."""
    cols = E.TABELLEN[v.cat]
    cw = E.cw(v.cat)
    lijn = lambda l, m, r: l + m.join(["─" * cw] * len(cols)) + r  # noqa: E731
    s.put(y, x, lijn("┌", "┬", "┐"), "dim")
    s.put(y + 1, x, "│", "dim")
    for lab, begin, n in E.koppen(v.cat):  # een kop loopt over al de vakjes van zijn eenheid
        cx = x + 1 + begin * (cw + 1)
        breed = n * (cw + 1) - 1
        echt = lab in E.MACHT_IN[v.cat]
        rol = "accent" if lab == v.van else "accent2" if lab == v.naar else ("" if echt else "dim")
        s.put(y + 1, cx, lab.center(breed), rol)
        s.put(y + 1, cx + breed, "│", "dim")
    yy = y + 2
    if E.ALIASSEN.get(v.cat):  # tweede kopregel: ha a ca, of hl dal l dl cl ml
        s.put(yy, x, "│", "dim")
        namen = dict((i, lab) for lab, i in E.alias_kop(v.cat))
        for i in range(len(cols)):
            cx = x + 1 + i * (cw + 1)
            lab = namen.get(i, "")
            rol = "accent" if lab == v.van else "accent2" if lab == v.naar else "dim"
            s.put(yy, cx, lab.center(cw)[:max(cw, len(lab))], rol)
            s.put(yy, cx + cw, "│", "dim")
        yy += 1
    for r, (label, cellen, komma, oordeel, eigen, komma_fout) in enumerate(rijen):
        s.put(yy, x, lijn("├", "┼", "┤"), "dim")
        s.put(yy + 1, x - 7, label.rjust(5), "bold")
        s.put(yy + 1, x, "│", "dim")
        for i in range(len(cols)):
            cx = x + 1 + i * (cw + 1)
            fout = bool(oordeel) and oordeel[i] is False
            if r == 0 and actief == i:
                rol = "cursor"
            elif oordeel and oordeel[i] is not None:
                rol = "goedvak" if oordeel[i] else "foutvak"
            else:
                rol = "goed" if r > 0 else ""
            s.put(yy + 1, cx, E.cel_tekst(cellen[i], i in (komma, eigen), fout, cw), rol)
            if komma_fout and i == (komma if eigen is None else eigen):
                s.put(yy + 1, cx + cw - 1, ",", "foutvak")
            elif i in (komma, eigen) and rol in ("", "goed"):
                s.put(yy + 1, cx + cw - 1, ",", "accent2" if i == eigen else "accent")
            s.put(yy + 1, cx + cw, "│", "dim")
            if klikbaar and r == 0:
                s.zones.voeg(yy + 1, cx, 1, cw, ("cel", i))
                s.zones.voeg(yy + 1, cx + cw, 1, 1, ("komma", i))
        yy += 2
    s.put(yy, x, lijn("└", "┴", "┘"), "dim")
    return yy + 1


INVOER = {"eenheid": EenheidInvoer, "tabel": TabelInvoer}
