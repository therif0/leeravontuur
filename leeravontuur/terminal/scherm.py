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

WIEL_OP = getattr(curses, "BUTTON4_PRESSED", 0x10000)
WIEL_NEER = getattr(curses, "BUTTON5_PRESSED", 0x200000)
KLIK = curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED


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
        self.status = ""       # rechts in de titelbalk
        self.status_kort = ""  # als er weinig plaats is
        self.slot = None       # seconden zonder toets waarna Vergrendeld volgt (None = nooit)
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
        self.zones.wis()
        h, w = self.win.getmaxyx()
        self.put(0, 0, " " * w, "titel")
        delen = [kruimel] if isinstance(kruimel, str) else list(kruimel)
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

    def toets(self):
        """Wacht op een toets of klik.

        Geeft een getal (toetscode; letters als ord(teken)) of een tuple-actie van een klikzone,
        bv. ("kies", 2) of ("scroll", 1). Een klik op de broodkruimel geeft TerugNaar.
        """
        self.win.refresh()
        self._laatste_toets = time.monotonic()
        try:
            self.win.timeout(1000 if self.slot else -1)
        except (curses.error, AttributeError):
            pass
        wachtbeurten = 0
        while True:
            try:
                k = self.win.get_wch()
            except curses.error:  # geen toets binnen de tijd (telkens 1 seconde)
                wachtbeurten += 1
                stil = max(time.monotonic() - self._laatste_toets, wachtbeurten * 1.0)
                if self.slot and stil >= self.slot:
                    raise Vergrendeld()
                continue
            if isinstance(k, str):
                k = ord(k) if len(k) == 1 else NIETS
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
                if isinstance(actie, tuple) and actie[0] == "kruimel":
                    raise TerugNaar(actie[1])
                return actie
            return k

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
        if not isinstance(k, int):
            return buf
        if k in BACKSPACE:
            return buf[:-1]
        if 32 <= k < 0x110000 and len(buf) < max_lengte:
            ch = chr(k)
            if ch.isalnum() or ch in ",. ":
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

    def menu(self, kruimel, vraag, opties, info=(), onder="", start=0):
        """Keuzemenu. opties = [(label, uitleg)]. Geeft de index terug, of None bij Esc/terug."""
        sel = start
        breed = max(len(o[0]) for o in opties)
        knoppen = [("↑↓", "kiezen", None), ("Enter", "ok", 10), ("Esc", "terug", ESC)]
        while True:
            if self.te_klein():
                continue
            self.cursor(False)
            self.nieuw(kruimel, knoppen)
            h, w = self.win.getmaxyx()
            self.put(3, 4, vraag, "bold")
            stap = 2 if 5 + 2 * len(opties) < h - 4 else 1
            for i, (label, uitleg) in enumerate(opties):
                y = 5 + stap * i
                tekst = f" {i + 1}. {label.ljust(breed)} "
                self.put(y, 6, tekst, "cursor" if i == sel else "")
                if uitleg:
                    self.put(y, 8 + len(tekst), uitleg, "dim")
                self.zones.voeg(y, 4, 1, w - 6, ("kies", i))
            for j, regel in enumerate(info):
                self.put(6 + stap * len(opties) + j, 4, regel, "info")
            if onder:
                self.put(h - 3, 4, onder, "dim")
            k = self.toets()
            if isinstance(k, tuple):
                if k[0] == "kies":
                    return k[1]
                if k[0] == "scroll":
                    sel = (sel + k[1]) % len(opties)
                continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(opties)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(opties)
            elif ord("1") <= k < ord("1") + min(len(opties), 9):
                return k - ord("1")
            elif k in ENTER:
                return sel
            elif k in (ESC, ord("q")):
                return None

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

    def invoer(self, kruimel, vraag, start="", max_lengte=20, verborgen=False, uitleg=(), cijfers=False):
        """Eén regel tekst laten typen (bv. een naam of wachtwoord). Geeft de tekst of None bij Esc.

        verborgen = toon bolletjes in plaats van de tekens; cijfers = alleen cijfers (pincode).
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
            if isinstance(k, int):
                if k in BACKSPACE:
                    buf = buf[:-1]
                elif cijfers:
                    if chr(k).isdigit() and len(buf) < max_lengte:
                        buf += chr(k)
                elif verborgen and 32 <= k < 0x110000 and len(buf) < max_lengte:
                    buf += chr(k)
                elif 32 <= k < 0x110000 and len(buf) < max_lengte and (chr(k).isalnum() or chr(k) in " -'"):
                    buf += chr(k)
