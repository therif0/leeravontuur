"""De basis van elk scherm: tekenen met rollen, titel met broodkruimel, knoppen, muis en invoer."""

import curses
import sys
import textwrap
import time

from . import tekens, thema
from .klikzones import Klikzones

MIN_B, MIN_H = 80, 24
ENTER = (10, 13, curses.KEY_ENTER)
BACKSPACE = (curses.KEY_BACKSPACE, 127, 8)
ESC = 27
NIETS = -1
# toetsen die het klokvenster doorgeeft (terminal/venster.py)
VENSTER_TOETSEN = {"Enter": 10, "Escape": 27, "Left": curses.KEY_LEFT, "Right": curses.KEY_RIGHT,
                   "Up": curses.KEY_UP, "Down": curses.KEY_DOWN, "BackSpace": curses.KEY_BACKSPACE, "Tab": 9}

# het numeriek klavier (#11) geeft soms een eigen toetscode in plaats van het teken:
# - Windows (PDCurses): vaste codes voor / * - + . en Enter (ncurses gebruikt die codes niet);
# - Linux/macOS (ncurses), als de terminal het klavier in "toepassingsmodus" zet: extra toetsen met een naam
#   (kpADD …) en een code boven KEY_MAX die per terminal verschilt; daarom op naam.
KLAVIER_PDCURSES = {getattr(curses, naam, code): teken for naam, code, teken in (
    ("PADSLASH", 458, ord("/")), ("PADENTER", 459, 10), ("CTL_PADENTER", 460, 10), ("ALT_PADENTER", 461, 10),
    ("PADSTOP", 462, ord(".")), ("PADSTAR", 463, ord("*")), ("PADMINUS", 464, ord("-")), ("PADPLUS", 465, ord("+")))}
KLAVIER = KLAVIER_PDCURSES if sys.platform == "win32" else {}
KLAVIER_NAMEN = {"kpADD": ord("+"), "kpSUB": ord("-"), "kpMUL": ord("*"), "kpDIV": ord("/"), "kpDOT": ord("."),
                 "kpCMA": ord(","), "kpZRO": ord("0")}


def vertaal_klavier(k):
    """Een toets van het numeriek klavier als het gewone teken (of Enter); elke andere toets ongewijzigd."""
    if not isinstance(k, int):
        return k
    if k in KLAVIER:
        return KLAVIER[k]
    if k > curses.KEY_MAX:
        try:
            return KLAVIER_NAMEN.get(curses.keyname(k).decode("ascii", "replace"), k)
        except (ValueError, curses.error, AttributeError):
            return k
    return k

WIEL_OP = getattr(curses, "BUTTON4_PRESSED", 0x10000)
WIEL_NEER = getattr(curses, "BUTTON5_PRESSED", 0x200000)
KLIK = curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED


def is_functietoets(k):
    """Een curses-toetscode (pijltje, F1, KEY_RESIZE …), geen getypt teken."""
    return isinstance(k, int) and curses.KEY_MIN <= k <= curses.KEY_MAX


def teken_van(k):
    """Het getypte teken bij een toets, of None (functietoets, Enter, klik …).

    Tekens met een code in het bereik van de curses-toetscodes (bv. œ, ą) komen van toets() als ("teken", ch),
    zodat ze nooit met een pijltje verward worden (chr(KEY_LEFT) is 'Ą')."""
    if isinstance(k, tuple) and len(k) == 2 and k[0] == "teken":
        return k[1]
    if isinstance(k, int) and 32 <= k < 0x110000 and k != 127 and not is_functietoets(k):
        return chr(k)
    return None


class TerugNaar(Exception):
    """Klik op de broodkruimel: ga terug naar het scherm op dit niveau (0 = hoofdmenu)."""

    def __init__(self, niveau):
        super().__init__(niveau)
        self.niveau = niveau


class Vergrendeld(Exception):
    """Te lang niets gedaan in een beveiligd deel (bv. het ouderdeel)."""


class Scherm:
    def __init__(self, win, inst, kleuren=True):
        self.win = win
        self.inst = inst
        self.kleuren = kleuren
        self.zones = Klikzones()
        self.kruimel = []
        self.status = ""       # rechts in de titelbalk
        self.status_kort = ""  # als er weinig plaats is
        self.slot = None       # seconden zonder toets waarna Vergrendeld volgt (None = nooit)
        self.klokvenster = None  # terminal/venster.Klokvenster, of None (dan tekent de terminal de klok)
        self._laatste_toets = time.monotonic()
        try:
            win.keypad(True)
        except (curses.error, AttributeError):
            pass
        self.pas_toe()

    def pas_toe(self):
        """(Opnieuw) het thema, de ASCII-terugval en de muis instellen volgens de instellingen."""
        self.ascii = tekens.ascii_nodig() if self.inst.ascii is None else self.inst.ascii
        self.c = thema.maak(self.inst.thema, self.kleuren)
        self.muis = False
        if getattr(self.win, "nep", False):
            self.muis = self.inst.muis
            return
        try:
            if self.inst.muis:
                curses.mousemask(curses.ALL_MOUSE_EVENTS)
                curses.mouseinterval(0)
                self.muis = True
            else:
                curses.mousemask(0)
        except (curses.error, AttributeError):
            self.muis = False

    # ---- tekenen ---------------------------------------------------------

    def maat(self):
        return self.win.getmaxyx()

    def put(self, y, x, s, rol=""):
        attr = self.c.get(rol, 0) if isinstance(rol, str) else rol
        h, w = self.win.getmaxyx()
        if y < 0 or y >= h or x < 0 or x >= w:
            return
        if self.ascii:
            s = tekens.naar_ascii(s)
        s = s[:max(0, w - x - (1 if y == h - 1 else 0))]
        try:
            self.win.addstr(y, x, s, attr)
        except curses.error:
            pass

    def cursor(self, aan, y=None, x=None):
        try:
            curses.curs_set(1 if aan else 0)
        except curses.error:
            pass
        if aan and y is not None:
            try:
                self.win.move(y, x)
            except curses.error:
                pass

    def nieuw(self, kruimel, knoppen=()):
        """Leeg scherm met titelbalk (broodkruimel, klikbaar) en een voetbalk met knoppen."""
        self.win.erase()
        if self.klokvenster:
            self.klokvenster.nieuw_beeld()
        self.zones.wis()
        h, w = self.win.getmaxyx()
        self.put(0, 0, " " * w, "titel")
        delen = [kruimel] if isinstance(kruimel, str) else list(kruimel)
        self.kruimel = list(delen)  # waar we zijn (voor het foutenlogboek)
        # te lang? kort de middelste stukken in (het eerste en het laatste blijven volledig)
        while sum(len(d) for d in delen) + 3 * (len(delen) - 1) + 2 > w and len(delen) > 2:
            midden = max(range(1, len(delen) - 1), key=lambda i: len(delen[i]))
            if len(delen[midden]) <= 4:
                break
            delen[midden] = delen[midden][:3] + "…"
        x = 1
        for i, deel in enumerate(delen):
            if i:
                self.put(0, x, " › ", "titel")
                x += 3
            self.put(0, x, deel, "titel")
            if i < len(delen) - 1:
                self.zones.voeg(0, x, 1, len(deel), ("kruimel", i))
            x += len(deel)
        for status in (self.status, self.status_kort):
            if status and x + 3 + len(status) < w:
                self.put(0, w - len(status) - 1, status, "titel")
                break
        self.voet(knoppen)

    def voet(self, knoppen):
        """knoppen = [(toets, uitleg, actie)]; elke knop is klikbaar en doet hetzelfde als de toets."""
        h, w = self.win.getmaxyx()
        self.put(h - 1, 0, " " * w, "voet")
        x = 1
        for label, uitleg, actie in knoppen:
            stuk = f"[{label}]"
            breedte = len(stuk) + (1 + len(uitleg) if uitleg else 0)
            if x + breedte > w - 1:
                break
            self.put(h - 1, x, stuk, "knop")
            if uitleg:
                self.put(h - 1, x + len(stuk), " " + uitleg, "voet")
            if actie is not None:
                self.zones.voeg(h - 1, x, 1, breedte, actie)
            x += breedte + 2

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.put(y, x, " " * (breedte + 2), rol)
        self.put(y, x + 1, tekst, rol)
        if actie is not None:
            self.zones.voeg(y, x, 1, breedte + 2, actie)

    # ---- invoer ----------------------------------------------------------

    def toets(self, wacht_ms=None):
        """Wacht op een toets of klik (met wacht_ms: hoogstens zo lang, en dan NIETS).

        Geeft een getal (toetscode; letters als ord(teken)) of een tuple-actie van een klikzone,
        bv. ("kies", 2) of ("scroll", 1). Een klik op de broodkruimel geeft TerugNaar.
        """
        self.win.refresh()
        venster = self.klokvenster
        if venster:
            venster.beeld_klaar()
        self._laatste_toets = time.monotonic()
        tik = 100 if venster else None  # met een klokvenster: kort wachten en dan het venster nakijken
        wacht = [w for w in (wacht_ms, tik) if w]
        try:
            self.win.timeout(min(wacht) if wacht else 1000 if self.slot else -1)
        except (curses.error, AttributeError):
            pass
        stap = (tik or wacht_ms or 1000) / 1000
        wachtbeurten = 0
        while True:
            k = self._van_venster(venster.volgende()) if venster else None
            if k is not None:
                if isinstance(k, str):  # een getypt teken in het klokvenster: zoals hieronder
                    return ("teken", k) if is_functietoets(ord(k)) else ord(k)
                return k
            try:
                k = self.win.get_wch()
            except curses.error:  # geen toets binnen de tijd
                wachtbeurten += 1
                stil = max(time.monotonic() - self._laatste_toets, wachtbeurten * stap)
                if wacht_ms and (not tik or stil * 1000 >= wacht_ms):
                    return NIETS
                if self.slot and stil >= self.slot:
                    raise Vergrendeld()
                continue
            k = vertaal_klavier(k)
            if k == curses.KEY_F2 and venster and venster.getekend:  # de klok in de terminal of terug in het venster
                venster.wissel()
                return curses.KEY_RESIZE  # opnieuw tekenen
            if isinstance(k, str):
                if len(k) != 1:
                    k = NIETS
                elif is_functietoets(ord(k)):
                    return ("teken", k)  # een echt teken dat toevallig dezelfde code heeft als een toets
                else:
                    k = ord(k)
            if k == curses.KEY_RESIZE:
                if sys.platform == "win32" and hasattr(curses, "resize_term"):
                    try:
                        curses.resize_term(0, 0)
                    except curses.error:
                        pass
                return k
            if k == curses.KEY_MOUSE:
                actie = self._muis()
                if actie is None:
                    continue
                if actie == ("klokvenster",):
                    if venster:
                        venster.wissel()
                    return curses.KEY_RESIZE
                if isinstance(actie, tuple) and actie[0] == "kruimel":
                    raise TerugNaar(actie[1])
                return actie
            return k

    @staticmethod
    def _van_venster(b):
        """Een bericht uit het klokvenster als toets: een code, een getypt teken (str), ("wijzer", dx, dy) of
        KEY_RESIZE (opnieuw tekenen, bv. toen het kind het venster sloot)."""
        if not b:
            return None
        if "toets" in b:
            t = b["toets"]
            if t in VENSTER_TOETSEN:
                return VENSTER_TOETSEN[t]
            return t if isinstance(t, str) and len(t) == 1 else None
        if "klik" in b:
            try:
                dx, dy = (float(x) for x in b["klik"])
            except (TypeError, ValueError):
                return None
            return ("wijzer", dx, dy)
        if b.get("dicht"):
            return curses.KEY_RESIZE
        return None

    def _muis(self):
        try:
            getmouse = getattr(self.win, "getmouse", None) or curses.getmouse
            _, x, y, _, knop = getmouse()
        except curses.error:
            return None
        if knop & WIEL_OP:
            return ("scroll", -1)
        if knop & WIEL_NEER:
            return ("scroll", 1)
        if knop & KLIK:
            return self.zones.zoek(y, x)
        return None

    @staticmethod
    def bewerk(buf, k, max_lengte=14):
        """Typen in een antwoordvak. Geeft de nieuwe tekst terug."""
        if k in BACKSPACE:
            return buf[:-1]
        ch = teken_van(k)
        if ch is not None and len(buf) < max_lengte and (ch.isalnum() or ch in ",. -−/<>=%€:"):
            return buf + ch
        return buf

    # ---- algemene schermen -----------------------------------------------

    def te_klein(self):
        h, w = self.win.getmaxyx()
        if h >= MIN_H and w >= MIN_B:
            return False
        self.cursor(False)
        self.win.erase()
        self.zones.wis()
        self.put(0, 0, "Het venster is te klein.")
        self.put(1, 0, f"Maak het minstens {MIN_B}x{MIN_H} (nu {w}x{h}).")
        self.toets()
        return True

    def pauze(self, ms):
        """Even wachten (voor een korte animatie). Doet niets in tests."""
        if getattr(self.win, "nep", False):
            return
        self.win.refresh()
        try:
            curses.napms(ms)
        except curses.error:
            pass

    def menu(self, kruimel, vraag, opties, info=(), onder="", start=0, extra=None, toetsen=None, uitleg_tot=None):
        """Keuzemenu. opties = [(label, uitleg)]. Geeft de index terug, of None bij Esc/terug.
        uitleg_tot = de kolom waar de uitleg moet stoppen (bv. vóór de avatar); te lang = ingekort met '…'.

        toetsen (de aanroeper bepaalt ze per keuze): [[("Enter", uitleg), ("v", uitleg), …], …], de eerste is
        altijd Enter. Dan is de terugwaarde (index, toets): "Enter" bij Enter, een cijfer of een klik op de keuze,
        anders de kleine letter (ook met Shift). Een letter die niet bij de gemarkeerde keuze hoort, doet niets.
        De voetregel toont de toetsen van de gemarkeerde keuze; elke knop is klikbaar."""
        sel = start
        breed = max(len(o[0]) for o in opties)
        knoppen = [("↑↓", "kiezen", None), ("Enter", "ok", 10), ("Esc", "terug", ESC)]

        def gekozen(i, toets="Enter"):
            return i if toetsen is None else (i, toets)

        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            if toetsen is not None:
                knoppen = [("Enter", uitleg, 10) if t == "Enter" else (t.upper(), uitleg, ord(t))
                           for t, uitleg in toetsen[sel]] + [("Esc", "terug", ESC)]
            self.nieuw(kruimel, knoppen)
            h, w = self.win.getmaxyx()
            self.put(3, 4, vraag, "bold")
            stap = 2 if 5 + 2 * len(opties) < h - 4 else 1
            for i, (label, uitleg) in enumerate(opties):
                y = 5 + stap * i
                tekst = f" {(i + 1) % 10}. {label.ljust(breed)} "  # de 10de keuze heeft toets 0
                self.put(y, 6, tekst, "cursor" if i == sel else "")
                if uitleg:
                    ruimte = (uitleg_tot or w) - 8 - len(tekst)
                    if len(uitleg) > ruimte > 1:
                        uitleg = uitleg[:ruimte - 1].rstrip(" ,·") + "…"
                    self.put(y, 8 + len(tekst), uitleg, "dim")
                self.zones.voeg(y, 4, 1, w - 6, ("kies", i))
            for j, regel in enumerate(info):
                self.put(6 + stap * len(opties) + j, 4, regel, "info")
            if onder:
                self.put(h - 3, 4, onder, "dim")
            if extra:
                extra()
            k = self.toets()
            if isinstance(k, tuple):
                if k[0] == "kies":
                    return gekozen(k[1])
                if k[0] == "scroll":
                    sel = (sel + k[1]) % len(opties)
                continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(opties)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(opties)
            elif ord("1") <= k < ord("1") + min(len(opties), 9):
                return gekozen(k - ord("1"))
            elif k == ord("0") and len(opties) >= 10:
                return gekozen(9)
            elif k in ENTER:
                return gekozen(sel)
            elif k in (ESC, ord("q")):
                return None
            elif toetsen is not None and (teken_van(k) or "").lower() in {t for t, _ in toetsen[sel][1:]}:
                return gekozen(sel, teken_van(k).lower())

    def lezer(self, kruimel, regels, knoppen, toetsen, scroll_uitleg="scrollen"):
        """Scrollbare tekst. regels = [(tekst, rol)]; toetsen = {toets of actie: terugwaarde}."""
        top = 0
        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            h, w = self.win.getmaxyx()
            lijnen = []
            for tekst, rol in regels:
                inspring = " " * (len(tekst) - len(tekst.lstrip()))
                stukken = textwrap.wrap(tekst, w - 8, subsequent_indent=inspring + "  ") or [""]
                lijnen += [(s, rol) for s in stukken]
            zicht = h - 4
            top = max(0, min(top, len(lijnen) - zicht))
            self.nieuw(kruimel, [("↑↓", scroll_uitleg, None)] + list(knoppen))
            for i, (tekst, rol) in enumerate(lijnen[top:top + zicht]):
                self.put(2 + i, 4, tekst, rol)
            if top + zicht < len(lijnen):
                self.put(h - 2, w - 22, "▼ scroll voor meer ▼", "accent")
            k = self.toets()
            if k in toetsen:
                return toetsen[k]
            if isinstance(k, tuple):
                if k[0] == "scroll":
                    top += 3 * k[1]
                continue
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

    def invoer(self, kruimel, vraag, start="", max_lengte=20, verborgen=False, uitleg=(), cijfers=False,
               vrij=False):
        """Eén regel tekst laten typen (bv. een naam of wachtwoord). Geeft de tekst of None bij Esc.

        verborgen = toon bolletjes in plaats van de tekens; cijfers = alleen cijfers (pincode);
        vrij = alle tekens (ook leestekens), bv. voor een opmerking.
        """
        buf = start
        knoppen = [("Enter", "ok", 10), ("Esc", "terug", ESC)]
        while True:
            if self.te_klein():
                continue
            self.nieuw(kruimel, knoppen)
            self.put(4, 4, vraag, "bold")
            self.tekstvak(6, 4, "•" * len(buf) if verborgen else buf, max_lengte, "veld")
            for i, regel in enumerate(uitleg):
                self.put(8 + i, 4, regel, "dim")
            self.cursor(True, 6, 5 + len(buf))
            k = self.toets()
            if k == ESC:
                self.cursor(False)
                return None
            if k in ENTER:
                self.cursor(False)
                return buf.strip()
            ch = teken_van(k)
            if k in BACKSPACE:
                buf = buf[:-1]
            elif ch is None or len(buf) >= max_lengte:
                pass
            elif cijfers:
                if ch in "0123456789":
                    buf += ch
            elif verborgen or vrij or ch.isalnum() or ch in " -'":
                buf += ch
