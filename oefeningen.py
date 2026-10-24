#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eenheden oefenen: massa (t, kg, hg, dag, g, dg, cg, mg) en lengte (km ... mm).

Starten:            python3 oefeningen.py
Menu-snelkoppeling: python3 oefeningen.py --snelkoppeling
Zelftest:           python3 oefeningen.py --test

Alleen de standaardbibliotheek van Python 3 is nodig (staat standaard op Fedora).
"""

import curses
import locale
import os
import random
import re
import shutil
import sys
import textwrap
from decimal import Decimal

os.environ.setdefault("ESCDELAY", "25")  # Esc meteen laten reageren

NAAM = "Imrane"
MIN_B, MIN_H = 80, 24
REEKS = 10
CW = 5  # breedte van een vakje in de tabel

MASSA, LENGTE = "massa", "lengte"

# Kolommen van de tabel: (label, macht van 10 t.o.v. g of m, echte eenheid?)
TABELLEN = {
    MASSA: [("t", 6, True), ("100kg", 5, False), ("10kg", 4, False), ("kg", 3, True),
            ("hg", 2, True), ("dag", 1, True), ("g", 0, True), ("dg", -1, True),
            ("cg", -2, True), ("mg", -3, True)],
    LENGTE: [("km", 3, True), ("hm", 2, True), ("dam", 1, True), ("m", 0, True),
             ("dm", -1, True), ("cm", -2, True), ("mm", -3, True)],
}
EENHEDEN = {cat: [l for l, _, echt in cols if echt] for cat, cols in TABELLEN.items()}
MACHT = {l: k for cols in TABELLEN.values() for l, k, echt in cols if echt}
CATEGORIE = {u: cat for cat, us in EENHEDEN.items() for u in us}

NIVEAUS = [
    dict(naam="Makkelijk", uitleg="kleine stappen, alleen gehele getallen",
         max_stap=3, cijfers=(1, 2), dec_getal=0, dec_antw=0, max_getal=10_000, max_antw=100_000),
    dict(naam="Normaal", uitleg="alle eenheden, soms een kommagetal",
         max_stap=9, cijfers=(1, 3), dec_getal=1, dec_antw=2, max_getal=100_000, max_antw=1_000_000),
    dict(naam="Moeilijk", uitleg="grote sprongen en veel kommagetallen",
         max_stap=9, cijfers=(2, 4), dec_getal=3, dec_antw=3, max_getal=1_000_000, max_antw=10_000_000),
]

LOF = ["Goed zo!", "Super!", "Knap gedaan!", "Prima!", "Helemaal juist!", "Top!"]
STAT = {"goed": 0, "vragen": 0}


# --------------------------------------------------------------------------
# Rekenen en uitleg
# --------------------------------------------------------------------------

def decimalen(d):
    return max(0, -d.normalize().as_tuple().exponent)


def fmt(d):
    """Decimal -> tekst met komma, zonder wetenschappelijke notatie."""
    return format(d.normalize(), "f").replace(".", ",")


def lees_getal(tekst):
    """Leest wat het kind typte. '3,5' en '0.25' zijn kommagetallen, '3.500' is 3500."""
    t = re.sub(r"[a-z]+$", "", tekst.strip().lower()).replace(" ", "")
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[1-9]\d{0,2}(\.\d{3})+", t):
        t = t.replace(".", "")
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", t):
        return None
    return Decimal(t)


class Vraag:
    def __init__(self, cat, van, naar, getal):
        self.cat, self.van, self.naar, self.getal = cat, van, naar, getal
        self.stap = MACHT[van] - MACHT[naar]  # > 0: naar rechts in de tabel
        self.antwoord = getal.scaleb(self.stap)


def tabel_bereik(v):
    """Laagste en hoogste kolom (macht van 10) die ingevuld moeten worden."""
    t = v.getal.scaleb(MACHT[v.van]).normalize().as_tuple()
    laag = min(t.exponent, MACHT[v.van], MACHT[v.naar])
    hoog = max(len(t.digits) + t.exponent - 1, MACHT[v.van], MACHT[v.naar])
    return laag, hoog


def past_in_tabel(v):
    laag, hoog = tabel_bereik(v)
    cols = TABELLEN[v.cat]
    return cols[-1][1] <= laag and hoog <= cols[0][1]


def verwachte_cijfers(v):
    """{macht: cijfer} voor elk vakje dat ingevuld moet worden (inclusief nullen)."""
    basis = v.getal.scaleb(MACHT[v.van])
    laag, hoog = tabel_bereik(v)
    return {k: int(basis.scaleb(-k) // 1 % 10) for k in range(laag, hoog + 1)}


def controleer_tabel(v, cellen):
    """Per vakje: True (juist), False (fout) of None (leeg en hoeft niet)."""
    verw = verwachte_cijfers(v)
    res = []
    for (_, k, _), c in zip(TABELLEN[v.cat], cellen):
        if k in verw:
            res.append(c == verw[k])
        elif c is None:
            res.append(None)
        else:
            res.append(c == 0)  # een extra nul vooraan of achteraan mag
    return res


def regel_uitleg(v):
    n = abs(v.stap)
    f = 10 ** n
    pl = "plaats" if n == 1 else "plaatsen"
    if v.stap > 0:
        return [f"1 {v.van} = {f} {v.naar}, dus doe je maal {f}.",
                f"Van {v.van} naar {v.naar} ga je {n} {pl} naar rechts in de tabel: "
                f"de komma schuift {n} {pl} naar rechts.",
                f"{fmt(v.getal)} × {f} = {fmt(v.antwoord)}"]
    return [f"1 {v.naar} = {f} {v.van}, dus doe je gedeeld door {f}.",
            f"Van {v.van} naar {v.naar} ga je {n} {pl} naar links in de tabel: "
            f"de komma schuift {n} {pl} naar links.",
            f"{fmt(v.getal)} : {f} = {fmt(v.antwoord)}"]


def tabel_uitleg(v):
    if not past_in_tabel(v):
        return []
    verw = verwachte_cijfers(v)
    namen = {k: lab for lab, k, _ in TABELLEN[v.cat]}
    delen = ", ".join(f"{verw[k]} bij {namen[k]}" for k in sorted(verw, reverse=True))
    return [f"In de tabel: komma achter {v.van}, dus {delen}.",
            f"Lees af met de komma achter {v.naar}: {fmt(v.antwoord)} {v.naar}."]


def aflezen(cellen, komma):
    """Leest het getal in de tabel af met de komma achter vakje `komma`. None zonder cijfers."""
    gevuld = [i for i, c in enumerate(cellen) if c is not None]
    if not gevuld:
        return None
    eerste, laatste = min(gevuld[0], komma), max(gevuld[-1], komma)
    cijfers = [str(cellen[i] or 0) for i in range(eerste, laatste + 1)]
    deel = komma - eerste + 1
    voor = "".join(cijfers[:deel]).lstrip("0") or "0"
    na = "".join(cijfers[deel:])
    return voor + ("," + na if na else "")


def maak_vraag(eenheden, niveau, tabel=False, vorige=None):
    paren = [(a, b) for a in eenheden for b in eenheden
             if a != b and CATEGORIE[a] == CATEGORIE[b]]
    kort = [p for p in paren if abs(MACHT[p[0]] - MACHT[p[1]]) <= niveau["max_stap"]]
    paren = kort or paren
    for poging in range(6000):
        nv = niveau if poging < 3000 else NIVEAUS[-1]  # lukt het niet, wat losser
        van, naar = random.choice(paren)
        n = random.randint(*nv["cijfers"])
        m = random.randint(10 ** (n - 1), 10 ** n - 1)
        if n > 1 and m % 10 == 0:
            continue
        v = Vraag(CATEGORIE[van], van, naar, Decimal(m).scaleb(random.randint(-3, 4)))
        if decimalen(v.getal) > nv["dec_getal"] or decimalen(v.antwoord) > nv["dec_antw"]:
            continue
        if v.getal >= nv["max_getal"] or v.antwoord >= nv["max_antw"]:
            continue
        if tabel and not past_in_tabel(v):
            continue
        if vorige and (vorige.van, vorige.naar, vorige.getal) == (van, naar, v.getal):
            continue
        return v
    van, naar = random.choice(paren)
    return Vraag(CATEGORIE[van], van, naar, Decimal(1))


def tabel_tekst(cat, cijfers=None, komma=None):
    """De tabel als gewone tekstregels (voor de spiekbrief)."""
    cols = TABELLEN[cat]
    n = len(cols)
    lijn = lambda l, m, r: l + m.join(["─" * CW] * n) + r
    regels = [lijn("┌", "┬", "┐"), "│" + "│".join(l.center(CW) for l, _, _ in cols) + "│"]
    if cijfers is not None:
        regels.append(lijn("├", "┼", "┤"))
        regels.append("│" + "│".join(cel_tekst(cijfers.get(k), k == komma) for _, k, _ in cols) + "│")
    regels.append(lijn("└", "┴", "┘"))
    return regels


def cel_tekst(cijfer, komma):
    s = [" "] * CW
    if cijfer is not None:
        s[2] = str(cijfer)
    if komma:
        s[4] = ","
    return "".join(s)


# --------------------------------------------------------------------------
# Het scherm
# --------------------------------------------------------------------------

ENTER = (10, 13, curses.KEY_ENTER)
BACKSPACE = (curses.KEY_BACKSPACE, 127, 8)
ESC = 27


class App:
    def __init__(self, scr):
        self.scr = scr
        self.c = {}
        self.kleuren()
        self.cursor(False)

    # ---- hulpjes -------------------------------------------------------

    def kleuren(self):
        b = curses.A_BOLD
        self.c = dict(bold=b, dim=curses.A_DIM, titel=curses.A_REVERSE | b, cursor=curses.A_REVERSE,
                      goed=b, fout=b, geel=b, blauw=b, goedvak=curses.A_REVERSE, foutvak=curses.A_REVERSE,
                      voet=curses.A_REVERSE, veld=curses.A_UNDERLINE)
        if not curses.has_colors():
            return
        curses.start_color()
        try:
            curses.use_default_colors()
            bg = -1
        except curses.error:
            bg = curses.COLOR_BLACK
        paren = [(curses.COLOR_BLACK, curses.COLOR_CYAN), (curses.COLOR_GREEN, bg),
                 (curses.COLOR_RED, bg), (curses.COLOR_YELLOW, bg), (curses.COLOR_CYAN, bg),
                 (curses.COLOR_BLACK, curses.COLOR_YELLOW), (curses.COLOR_BLACK, curses.COLOR_GREEN),
                 (curses.COLOR_WHITE, curses.COLOR_RED)]
        for i, (fg, achter) in enumerate(paren, 1):
            curses.init_pair(i, fg, achter)
        p = curses.color_pair
        self.c.update(titel=p(1) | b, goed=p(2) | b, fout=p(3) | b, geel=p(4) | b, blauw=p(5) | b,
                      cursor=p(6) | b, goedvak=p(7) | b, foutvak=p(8) | b, voet=p(1))

    def cursor(self, aan):
        try:
            curses.curs_set(1 if aan else 0)
        except curses.error:
            pass

    def put(self, y, x, s, attr=0):
        h, w = self.scr.getmaxyx()
        if y < 0 or y >= h or x < 0 or x >= w:
            return
        s = s[:max(0, w - x - (1 if y == h - 1 else 0))]
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def te_klein(self):
        h, w = self.scr.getmaxyx()
        if h >= MIN_H and w >= MIN_B:
            return False
        self.cursor(False)
        self.scr.erase()
        self.put(0, 0, "Het venster is te klein.")
        self.put(1, 0, f"Maak het minstens {MIN_B}x{MIN_H} (nu {w}x{h}).")
        self.scr.refresh()
        self.scr.getch()
        return True

    def kader(self, titel, voet=""):
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        self.put(0, 0, " " * w, self.c["titel"])
        self.put(0, 2, titel, self.c["titel"])
        if STAT["vragen"]:
            rechts = f"Vandaag: {STAT['goed']}/{STAT['vragen']} juist "
            self.put(0, w - len(rechts) - 1, rechts, self.c["titel"])
        if voet:
            self.put(h - 1, 0, (" " + voet).ljust(w), self.c["voet"])

    def tekstvak(self, y, x, tekst, breedte, attr):
        self.put(y, x, " " * (breedte + 2), attr)
        self.put(y, x + 1, tekst, attr)

    @staticmethod
    def bewerk(buf, k):
        """Typen in een antwoordvak. Geeft de nieuwe tekst terug."""
        if k in BACKSPACE:
            return buf[:-1]
        if 0 <= k < 256 and len(buf) < 14:
            ch = chr(k)
            if ch.isdigit() or ch in ",. " or ch.isalpha():
                return buf + ch
        return buf

    def voortgang(self, y, nr, resultaten):
        self.put(y, 4, f"Vraag {nr + 1} van {REEKS}", self.c["bold"])
        for i in range(REEKS):
            if i < len(resultaten):
                ch, attr = "●", self.c["goed"] if resultaten[i]["goed"] else self.c["fout"]
            else:
                ch, attr = ("◉", self.c["geel"]) if i == nr else ("○", self.c["dim"])
            self.put(y, 22 + 2 * i, ch, attr)
        self.put(y, 46, f"Punten: {sum(r['goed'] for r in resultaten)}", self.c["bold"])

    # ---- algemene schermen ---------------------------------------------

    def menu(self, titel, vraag, opties, info=None):
        sel = 0
        breed = max(len(o[0]) for o in opties)
        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            self.kader(titel, "↑/↓ kiezen · Enter = ok · Esc = terug")
            self.put(3, 4, vraag, self.c["bold"])
            for i, (label, uitleg) in enumerate(opties):
                tekst = f" {i + 1}. {label.ljust(breed)} "
                self.put(5 + 2 * i, 6, tekst, self.c["cursor"] if i == sel else 0)
                if uitleg:
                    self.put(5 + 2 * i, 8 + len(tekst), uitleg, self.c["dim"])
            for j, regel in enumerate(info or []):
                self.put(6 + 2 * len(opties) + j, 4, regel, self.c["blauw"])
            self.scr.refresh()
            k = self.scr.getch()
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(opties)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(opties)
            elif ord("1") <= k < ord("1") + len(opties):
                return k - ord("1")
            elif k in ENTER:
                return sel
            elif k in (ESC, ord("q")):
                return None

    def lezer(self, titel, regels, voet, toetsen):
        """Scrollbare tekst. regels = [(tekst, attr)]; toetsen = {toets: terugwaarde}."""
        top = 0
        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            h, w = self.scr.getmaxyx()
            lijnen = []
            for tekst, attr in regels:
                inspring = " " * (len(tekst) - len(tekst.lstrip()))
                stukken = textwrap.wrap(tekst, w - 8, subsequent_indent=inspring + "  ") or [""]
                lijnen += [(s, attr) for s in stukken]
            zicht = h - 4
            top = max(0, min(top, len(lijnen) - zicht))
            self.kader(titel, voet)
            for i, (tekst, attr) in enumerate(lijnen[top:top + zicht]):
                self.put(2 + i, 4, tekst, attr)
            if top + zicht < len(lijnen):
                self.put(h - 2, w - 22, "▼ scroll voor meer ▼", self.c["geel"])
            self.scr.refresh()
            k = self.scr.getch()
            if k in toetsen:
                return toetsen[k]
            if k == curses.KEY_UP:
                top -= 1
            elif k == curses.KEY_DOWN:
                top += 1
            elif k == curses.KEY_PPAGE:
                top -= zicht - 1
            elif k in (curses.KEY_NPAGE, ord(" ")):
                top += zicht - 1
            elif k == curses.KEY_HOME:
                top = 0
            elif k == curses.KEY_END:
                top = len(lijnen)

    # ---- eenheden kiezen -----------------------------------------------

    def kies_oefening(self, titel):
        while True:
            k = self.menu(titel, "Welke eenheden wil je oefenen?", [
                ("Massa", "t  kg  hg  dag  g  dg  cg  mg"),
                ("Lengte", "km  hm  dam  m  dm  cm  mm"),
                ("Allebei", "massa en lengte door elkaar"),
                ("Zelf kiezen", "duid zelf de eenheden aan")])
            if k is None:
                return None
            if k == 3:
                eenheden = self.kies_zelf()
                if eenheden is None:
                    continue
                soort = "Zelf gekozen"
            else:
                eenheden = [EENHEDEN[MASSA], EENHEDEN[LENGTE],
                            EENHEDEN[MASSA] + EENHEDEN[LENGTE]][k]
                soort = ["Massa", "Lengte", "Massa + lengte"][k]
            n = self.menu(titel, "Hoe moeilijk?", [(nv["naam"], nv["uitleg"]) for nv in NIVEAUS])
            if n is not None:
                return eenheden, NIVEAUS[n], f"{soort} · {NIVEAUS[n]['naam']}"

    def kies_zelf(self):
        kolommen = [EENHEDEN[MASSA], EENHEDEN[LENGTE]]
        aan, kol, rij, melding = set(), 0, 0, ""
        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            self.kader("Zelf eenheden kiezen",
                       "↑/↓/←/→ bewegen · Spatie = aan/uit · Enter = klaar · Esc = terug")
            self.put(3, 4, "Duid minstens 2 eenheden van dezelfde soort aan.", self.c["bold"])
            for c, (kop, lijst) in enumerate(zip(("Massa", "Lengte"), kolommen)):
                x = 8 + c * 30
                self.put(5, x, kop, self.c["geel"])
                for r, u in enumerate(lijst):
                    vak = "[x]" if u in aan else "[ ]"
                    self.put(7 + r, x, f" {vak} {u:<4} ", self.c["cursor"] if (c, r) == (kol, rij) else 0)
            self.put(17, 4, melding, self.c["fout"])
            self.scr.refresh()
            k = self.scr.getch()
            melding = ""
            if k == curses.KEY_UP:
                rij = max(0, rij - 1)
            elif k == curses.KEY_DOWN:
                rij = min(len(kolommen[kol]) - 1, rij + 1)
            elif k in (curses.KEY_LEFT, curses.KEY_RIGHT, 9):
                kol = 1 - kol
                rij = min(rij, len(kolommen[kol]) - 1)
            elif k in (ord(" "), ord("x")):
                aan ^= {kolommen[kol][rij]}
            elif k in ENTER:
                if any(sum(CATEGORIE[u] == cat for u in aan) >= 2 for cat in (MASSA, LENGTE)):
                    return [u for lijst in kolommen for u in lijst if u in aan]
                melding = "Kies minstens 2 eenheden bij massa of bij lengte."
            elif k == ESC:
                return None

    # ---- een gewone vraag ----------------------------------------------

    def stel_vraag(self, titel, v, nr=None, resultaten=None, vrij=False):
        """Toont één vraag. Geeft (getypt antwoord, goed?, stoppen?) of None bij Esc."""
        buf, melding, goed, tip = "", "", None, False
        lof = random.choice(LOF)
        voet = ("Enter = controleren · ? = tip · Esc = stoppen" if vrij
                else "Enter = controleren · Esc = stoppen · Kommagetal? Gebruik een komma: 0,25")
        while True:
            if self.te_klein():
                continue
            self.kader(titel, voet)
            if vrij:
                self.put(2, 4, f"Vrij oefenen: {self.vrij_goed + bool(goed)} van "
                               f"{self.vrij_aantal + (goed is not None)} juist", self.c["bold"])
            else:
                self.voortgang(2, nr, resultaten)
            y, x = 6, 6
            links = f"{fmt(v.getal)} {v.van}  =  "
            self.put(y, x, links, self.c["bold"])
            vx = x + len(links)
            veld_attr = self.c["veld"] if goed is None else (self.c["goedvak"] if goed else self.c["foutvak"])
            self.tekstvak(y, vx, buf, 14, veld_attr)
            self.put(y, vx + 17, v.naar, self.c["bold"])
            if goed is None:
                self.put(y + 3, x, melding, self.c["fout"])
                if tip:
                    self.put(y + 3, x, "Tip: " + regel_uitleg(v)[0], self.c["geel"])
                    self.put(y + 4, x, "(Kijk ook eens in de spiekbrief in het hoofdmenu.)", self.c["dim"])
            else:
                if goed:
                    self.put(y + 3, x, "✔ " + lof, self.c["goed"])
                else:
                    self.put(y + 3, x, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.",
                             self.c["fout"])
                uitleg = (regel_uitleg(v) + tabel_uitleg(v)) if vrij or not goed else []
                if not vrij and uitleg:
                    uitleg = uitleg[:1]
                yy = y + 5
                for regel in uitleg:
                    for stuk in textwrap.wrap(regel, 70):
                        self.put(yy, x, stuk, self.c["geel"])
                        yy += 1
                laatste = not vrij and nr == REEKS - 1
                self.put(yy + 1, x, "Enter = naar je resultaat" if laatste else "Enter = volgende vraag",
                         self.c["dim"])
            if goed is None:
                self.cursor(True)
                self.scr.move(y, vx + 1 + len(buf))
            else:
                self.cursor(False)
            self.scr.refresh()
            k = self.scr.getch()
            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return buf, goed, False
                if k == ESC:
                    return buf, goed, True
                continue
            if k == ESC:
                return None
            if k == ord("?") and vrij:
                tip = True
            elif k in ENTER:
                getal = lees_getal(buf)
                if getal is None:
                    tip = False
                    melding = ("Typ eerst je antwoord." if not buf.strip()
                               else "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25.")
                    continue
                goed = getal == v.antwoord
                STAT["vragen"] += 1
                STAT["goed"] += goed
            else:
                buf = self.bewerk(buf, k)
                melding = ""

    # ---- de tabel ------------------------------------------------------

    def teken_tabel(self, y, x, v, rijen, actief=None):
        cols = TABELLEN[v.cat]
        lijn = lambda l, m, r: l + m.join(["─" * CW] * len(cols)) + r
        dim = self.c["dim"]
        self.put(y, x, lijn("┌", "┬", "┐"), dim)
        self.put(y + 1, x, "│", dim)
        for i, (lab, _, echt) in enumerate(cols):
            cx = x + 1 + i * (CW + 1)
            attr = (self.c["geel"] if lab == v.van else self.c["blauw"] if lab == v.naar
                    else (0 if echt else dim))
            self.put(y + 1, cx, lab.center(CW), attr)
            self.put(y + 1, cx + CW, "│", dim)
        yy = y + 2
        for r, (label, cellen, komma, oordeel, eigen) in enumerate(rijen):
            self.put(yy, x, lijn("├", "┼", "┤"), dim)
            self.put(yy + 1, x - 7, label.rjust(5), self.c["bold"])
            self.put(yy + 1, x, "│", dim)
            for i in range(len(cols)):
                cx = x + 1 + i * (CW + 1)
                if r == 0 and actief == i:
                    attr = self.c["cursor"]
                elif oordeel and oordeel[i] is not None:
                    attr = self.c["goedvak"] if oordeel[i] else self.c["foutvak"]
                else:
                    attr = self.c["goed"] if r > 0 else 0
                self.put(yy + 1, cx, cel_tekst(cellen[i], i in (komma, eigen)), attr)
                if i in (komma, eigen) and attr in (0, self.c["goed"]):
                    self.put(yy + 1, cx + 4, ",", self.c["blauw"] if i == eigen else self.c["geel"])
                self.put(yy + 1, cx + CW, "│", dim)
            yy += 2
        self.put(yy, x, lijn("└", "┴", "┘"), dim)
        return yy + 1

    def tabel_vraag(self, titel, v, nr, resultaten):
        """Eén tabel-oefening. Geeft (antwoord, goed?, tabel goed?, stoppen?) of None bij Esc."""
        cols = TABELLEN[v.cat]
        n = len(cols)
        labels = [lab for lab, _, _ in cols]
        komma_van, komma_naar = labels.index(v.van), labels.index(v.naar)
        verw = verwachte_cijfers(v)
        juist_rij = [verw.get(k) for _, k, _ in cols]
        cellen, antw, pos, laatste_cel = [None] * n, "", 0, 0
        melding, oordeel, goed, eigen_komma = "", None, None, None
        voet = "Tab/→ verder · ← terug · , = komma · ↓ antwoord · Enter = nakijken · Esc stop"
        while True:
            if self.te_klein():
                continue
            self.kader(titel, voet)
            self.voortgang(2, nr, resultaten)
            x = 4
            for stuk, attr in ((fmt(v.getal) + " ", self.c["bold"]), (v.van, self.c["geel"]),
                               ("  =  ?  ", self.c["bold"]), (v.naar, self.c["blauw"])):
                self.put(4, x, stuk, attr)
                x += len(stuk)
            self.put(5, 4, f"Komma achter {v.van} · vul aan met nullen tot {v.naar} · "
                           "druk , om de komma te zetten", self.c["dim"])
            rijen = [("Jij", cellen, komma_van, oordeel, eigen_komma)]
            if goed is not None:
                rijen.append(("Juist", juist_rij, komma_naar, None, None))
            ya = self.teken_tabel(7, 12, v, rijen, pos if goed is None and pos < n else None) + 1
            self.put(ya, 4, "Antwoord:", self.c["bold"])
            if goed is None:
                veld_attr = self.c["cursor"] if pos == n else self.c["veld"]
            else:
                veld_attr = self.c["goedvak"] if goed else self.c["foutvak"]
            self.tekstvak(ya, 15, antw, 14, veld_attr)
            self.put(ya, 33, v.naar, self.c["blauw"])
            if goed is None:
                if eigen_komma is not None:
                    gelezen = aflezen(cellen, eigen_komma)
                    plek = labels[eigen_komma]
                    if gelezen is None:
                        tekst = "Zet eerst cijfers in de tabel."
                    elif cols[eigen_komma][2]:
                        tekst = f"Aflezen met de komma achter {plek}: {gelezen} {plek}"
                    else:
                        tekst = f"Aflezen: {gelezen}, maar bij {plek} hoort geen eenheid."
                    self.put(ya + 2, 4, tekst, self.c["blauw"])
                self.put(ya + 3, 4, melding, self.c["fout"])
                self.cursor(True)
                if pos < n:
                    self.scr.move(10, 12 + 1 + pos * (CW + 1) + 2)
                else:
                    self.scr.move(ya, 16 + len(antw))
            else:
                self.cursor(False)
                tabel_ok = all(o is not False for o in oordeel)
                if goed:
                    self.put(ya + 2, 4, "✔ Je antwoord is juist!", self.c["goed"])
                else:
                    self.put(ya + 2, 4, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.",
                             self.c["fout"])
                if tabel_ok:
                    self.put(ya + 3, 4, "✔ Je tabel is ook juist ingevuld.", self.c["goed"])
                else:
                    self.put(ya + 3, 4, "✘ Kijk naar de rode vakjes: de rij 'Juist' toont hoe het moet.",
                             self.c["fout"])
                yy = ya + 4
                if eigen_komma == komma_naar:
                    self.put(yy, 4, f"✔ Je komma staat goed: achter {v.naar}.", self.c["goed"])
                    yy += 1
                elif eigen_komma is not None:
                    self.put(yy, 4, f"✘ Je komma stond achter {labels[eigen_komma]}, "
                                    f"maar moest achter {v.naar}.", self.c["fout"])
                    yy += 1
                self.put(yy, 4, regel_uitleg(v)[0], self.c["geel"])
                self.put(yy + 1, 4, f"De komma springt van {v.van} naar {v.naar}: "
                                    f"lees af → {fmt(v.antwoord)} {v.naar}.", self.c["geel"])
                self.put(ya + 7, 4, "Enter = naar je resultaat" if nr == REEKS - 1
                         else "Enter = volgende oefening", self.c["dim"])
            self.scr.refresh()
            k = self.scr.getch()

            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return antw, goed, tabel_ok, False
                if k == ESC:
                    return antw, goed, tabel_ok, True
                continue
            melding = ""
            if k == ESC:
                return None
            if k in (9, curses.KEY_RIGHT):
                pos = (pos + 1) % (n + 1)
            elif k in (curses.KEY_BTAB, curses.KEY_LEFT):
                pos = (pos - 1) % (n + 1)
            elif k == curses.KEY_DOWN:
                pos = n
            elif k == curses.KEY_UP and pos == n:
                pos = laatste_cel
            elif k in ENTER:
                getal = lees_getal(antw)
                if not antw.strip():
                    melding = "Vul ook je antwoord in (met ↓ of Tab ga je naar het antwoordvak)."
                    pos = n
                elif getal is None:
                    melding = "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25."
                    pos = n
                else:
                    goed = getal == v.antwoord
                    oordeel = controleer_tabel(v, cellen)
                    STAT["vragen"] += 1
                    STAT["goed"] += goed
            elif pos < n:
                if ord("0") <= k <= ord("9"):
                    cellen[pos] = k - ord("0")
                    pos = min(pos + 1, n - 1)
                elif k in BACKSPACE:
                    if cellen[pos] is None and pos > 0:
                        pos -= 1
                    cellen[pos] = None
                elif k in (curses.KEY_DC, ord(" ")):
                    cellen[pos] = None
                elif k in (ord(","), ord(".")):
                    eigen_komma = None if eigen_komma == pos else pos
            else:
                antw = self.bewerk(antw, k)
            if pos < n:
                laatste_cel = pos

    # ---- reeksen en rapport --------------------------------------------

    def reeks(self, eenheden, niveau, soort, tabel):
        titel = ("Tabel-oefening" if tabel else "Reeks van 10") + " · " + soort
        while True:
            resultaten, vorige = [], None
            for nr in range(REEKS):
                v = maak_vraag(eenheden, niveau, tabel, vorige)
                vorige = v
                if tabel:
                    uit = self.tabel_vraag(titel, v, nr, resultaten)
                else:
                    uit = self.stel_vraag(titel, v, nr, resultaten)
                if uit is None:
                    return
                resultaten.append(dict(v=v, antw=uit[0], goed=uit[1], tabel=uit[2] if tabel else None))
                if uit[-1]:
                    return
            if not self.rapport(titel, resultaten):
                return

    def rapport(self, titel, resultaten):
        goed = sum(r["goed"] for r in resultaten)
        if goed == REEKS:
            bericht, kleur = f"Perfect, {NAAM}! Alles juist!", self.c["goed"]
        elif goed >= 8:
            bericht, kleur = "Heel goed gedaan!", self.c["goed"]
        elif goed >= 6:
            bericht, kleur = "Goed bezig! Lees de uitleg bij je fouten en probeer nog een reeks.", self.c["geel"]
        else:
            bericht, kleur = "Blijf oefenen, je kan het! Lees de uitleg hieronder rustig na.", self.c["fout"]
        regels = [(f"Je score: {goed} / {REEKS}", kleur), (bericht, kleur), ("", 0),
                  (f"Vandaag in totaal: {STAT['goed']} van {STAT['vragen']} juist.", self.c["blauw"]),
                  ("", 0)]
        fouten = [(i, r) for i, r in enumerate(resultaten) if not r["goed"] or r["tabel"] is False]
        if not fouten:
            regels.append(("Geen enkele fout. Proficiat!", self.c["goed"]))
        else:
            regels += [("Wat ging er mis? Lees de uitleg goed:", self.c["geel"]), ("", 0)]
        for i, r in fouten:
            v = r["v"]
            regels.append((f"Vraag {i + 1}:  {fmt(v.getal)} {v.van} = ? {v.naar}", self.c["bold"]))
            if r["goed"]:
                regels.append(("   Je antwoord was juist, maar in de tabel stonden foutjes.", self.c["geel"]))
            else:
                regels.append((f"   Jij schreef: {r['antw'].strip()}    Juist is: {fmt(v.antwoord)} {v.naar}",
                               self.c["fout"]))
            regels += [("   " + l, 0) for l in regel_uitleg(v)]
            regels += [("   " + l, self.c["blauw"]) for l in tabel_uitleg(v)]
            regels.append(("", 0))
        toetsen = {ord("n"): True, ord("N"): True, ESC: False, ord("m"): False, ord("M"): False}
        toetsen.update({k: True for k in ENTER})
        return self.lezer(f"Resultaat · {titel}", regels,
                          "↑/↓ scrollen · Enter of N = nieuwe reeks · Esc of M = menu", toetsen)

    def vrij_oefenen(self, eenheden, niveau, soort):
        titel = "Vrij oefenen · " + soort
        self.vrij_goed = self.vrij_aantal = 0
        vorige = None
        while True:
            v = maak_vraag(eenheden, niveau, vorige=vorige)
            vorige = v
            uit = self.stel_vraag(titel, v, vrij=True)
            if uit is None:
                return
            self.vrij_aantal += 1
            self.vrij_goed += uit[1]
            if uit[2]:
                return

    # ---- spiekbrief ----------------------------------------------------

    def spiekbrief(self):
        b, g, bl, d = self.c["bold"], self.c["geel"], self.c["blauw"], self.c["dim"]
        voorbeeld = Vraag(LENGTE, "m", "cm", Decimal("4.25"))
        regels = [
            ("Hoe werkt omzetten?", g),
            ("  • Elke kolom naar rechts is 10 keer kleiner: je doet maal 10.", 0),
            ("  • Elke kolom naar links is 10 keer groter: je doet gedeeld door 10.", 0),
            ("  • Zet het getal in de tabel met de komma achter de eenheid die je krijgt.", 0),
            ("  • Vul aan met nullen tot de eenheid die gevraagd wordt en lees af.", 0),
            ("", 0),
            ("LENGTE", g),
            *[("  " + r, 0) for r in tabel_tekst(LENGTE)],
            ("  1 km = 1000 m      1 m = 10 dm = 100 cm = 1000 mm      1 cm = 10 mm", bl),
            ("  km = kilometer, hm = hectometer, dam = decameter, m = meter,", d),
            ("  dm = decimeter, cm = centimeter, mm = millimeter", d),
            ("  Ezelsbruggetje: Koning Hendrik Dronk Elke Dag Chocolade Melk", d),
            ("", 0),
            ("MASSA", g),
            *[("  " + r, 0) for r in tabel_tekst(MASSA)],
            ("  1 t = 1000 kg      1 kg = 1000 g      1 g = 1000 mg      1 kg = 10 hg", bl),
            ("  t = ton, kg = kilogram, hg = hectogram, dag = decagram, g = gram,", d),
            ("  dg = decigram, cg = centigram, mg = milligram", d),
            ("  Tussen t en kg zitten twee lege kolommen (100 kg en 10 kg).", d),
            ("", 0),
            ("VOORBEELD:  4,25 m = ? cm", g),
            ("  1. Zet 4,25 in de tabel met de komma achter m:", 0),
            *[("     " + r, 0) for r in tabel_tekst(LENGTE, verwachte_cijfers(voorbeeld), 0)],
            ("  2. De komma springt naar cm. Lees af:", 0),
            *[("     " + r, 0) for r in tabel_tekst(LENGTE, verwachte_cijfers(voorbeeld), -2)],
            ("  3. 4,25 m = 425 cm", b),
            ("", 0),
            ("  Nog een: 5 mm = ? m → 0 bij m, 0 bij dm, 0 bij cm, 5 bij mm → 0,005 m", 0),
        ]
        toetsen = {k: None for k in (ESC, ord("q"), *ENTER)}
        self.lezer("Spiekbrief", regels, "↑/↓ of PgUp/PgDn scrollen · Enter of Esc = terug", toetsen)

    # ---- hoofdmenu -----------------------------------------------------

    def start(self):
        while True:
            info = ([f"Vandaag al {STAT['goed']} van {STAT['vragen']} juist. Goed bezig!"]
                    if STAT["vragen"] else [])
            k = self.menu("Eenheden oefenen", f"Hallo {NAAM}! Wat wil je doen?", [
                ("Vrij oefenen", "zoveel vragen als je wil, met tip en uitleg"),
                ("Reeks van 10", "10 vragen, daarna je score en uitleg"),
                ("Tabel-oefening", "vul de eenhedentabel in met Tab"),
                ("Spiekbrief", "hoe werkt omzetten?"),
                ("Stoppen", "")], info)
            if k is None or k == 4:
                return
            if k == 3:
                self.spiekbrief()
                continue
            keuze = self.kies_oefening(["Vrij oefenen", "Reeks van 10", "Tabel-oefening"][k])
            if keuze is None:
                continue
            if k == 0:
                self.vrij_oefenen(*keuze)
            else:
                self.reeks(*keuze, tabel=(k == 2))


# --------------------------------------------------------------------------
# Extra's: snelkoppeling en zelftest
# --------------------------------------------------------------------------

def snelkoppeling():
    pad = os.path.abspath(__file__)
    os.chmod(pad, os.stat(pad).st_mode | 0o111)
    if shutil.which("konsole"):
        exec_regel, terminal = f'konsole --hide-menubar -e python3 "{pad}"', "false"
    else:
        exec_regel, terminal = f'python3 "{pad}"', "true"
    map_ = os.path.expanduser("~/.local/share/applications")
    os.makedirs(map_, exist_ok=True)
    bestand = os.path.join(map_, "eenheden-oefenen.desktop")
    with open(bestand, "w", encoding="utf-8") as f:
        f.write("[Desktop Entry]\nType=Application\nName=Eenheden oefenen\n"
                "Comment=Massa en lengte omzetten oefenen\n"
                f"Exec={exec_regel}\nTerminal={terminal}\nIcon=accessories-calculator\n"
                "Categories=Education;\n")
    print(f"Snelkoppeling gemaakt: {bestand}")
    print("Je vindt 'Eenheden oefenen' nu in het startmenu (bij Onderwijs/Education).")


def zelftest():
    def q(getal, van, naar):
        return fmt(Vraag(CATEGORIE[van], van, naar, Decimal(getal)).antwoord)

    assert q("3.5", "km", "m") == "3500"
    assert q("250", "mg", "g") == "0,25"
    assert q("2", "t", "kg") == "2000"
    assert q("4.25", "m", "cm") == "425"
    assert q("5", "mm", "m") == "0,005"
    assert q("1", "t", "mg") == "1000000000"
    assert q("3500", "g", "kg") == "3,5"
    assert lees_getal("3,5") == Decimal("3.5")
    assert lees_getal("0.25") == Decimal("0.25")
    assert lees_getal("3.500") == 3500
    assert lees_getal("1 000") == 1000
    assert lees_getal("0,25 g") == Decimal("0.25")
    assert lees_getal("abc") is None and lees_getal("") is None and lees_getal("3,,5") is None

    v = Vraag(LENGTE, "m", "cm", Decimal("4.25"))
    assert verwachte_cijfers(v) == {0: 4, -1: 2, -2: 5}
    assert verwachte_cijfers(Vraag(LENGTE, "mm", "m", Decimal(5))) == {0: 0, -1: 0, -2: 0, -3: 5}
    assert verwachte_cijfers(Vraag(LENGTE, "m", "km", Decimal(3500))) == {3: 3, 2: 5, 1: 0, 0: 0}
    juist = [None, None, None, 4, 2, 5, None]
    assert all(o is not False for o in controleer_tabel(v, juist))
    assert controleer_tabel(v, [None, None, 0, 4, 2, 5, 0])[2] is True  # extra nul mag
    assert controleer_tabel(v, [None, None, None, 4, 2, 6, None])[5] is False

    assert aflezen([4, 0, 0, 0, None, None, None, None, None, None], 0) == "4,000"   # 4000 kg -> t
    assert aflezen([None, None, None, 4, 2, 5, None], 5) == "425"                  # 4,25 m -> cm
    assert aflezen([None, None, None, None, None, None, 5], 3) == "0,005"          # 5 mm -> m
    assert aflezen([None, None, None, 4, None, 5, None], 3) == "4,05"
    assert aflezen([None] * 7, 3) is None

    alles = EENHEDEN[MASSA] + EENHEDEN[LENGTE]
    for nv in NIVEAUS:
        for tabel in (False, True):
            for eenheden in (EENHEDEN[MASSA], EENHEDEN[LENGTE], alles, ["t", "mg"]):
                for _ in range(300):
                    v = maak_vraag(eenheden, nv, tabel)
                    assert v.antwoord == v.getal * Decimal(10) ** v.stap
                    assert v.van in eenheden and v.naar in eenheden and v.van != v.naar
                    if tabel:
                        assert past_in_tabel(v)
                    regel_uitleg(v), tabel_uitleg(v)
    print("Alle tests geslaagd.")


def main(scr):
    App(scr).start()


if __name__ == "__main__":
    if "--test" in sys.argv:
        zelftest()
        sys.exit(0)
    if "--snelkoppeling" in sys.argv:
        snelkoppeling()
        sys.exit(0)
    locale.setlocale(locale.LC_ALL, "")
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    if STAT["vragen"]:
        print(f"Tot de volgende keer, {NAAM}! Vandaag: {STAT['goed']} van {STAT['vragen']} juist.")
    else:
        print(f"Tot de volgende keer, {NAAM}!")
