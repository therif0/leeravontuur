"""De terminal-app: startscherm, hoofdmenu, menu's per vak en domein, en opties."""

import curses

from .. import LICENTIE, MAKER, MOTTO, NAAM, VERSIE
from ..kern import instellingen, leerjaren
from .scherm import ENTER, ESC, Scherm, TerugNaar
from .schermen.eenheden import Eenheden

HOOFD = "Leeravontuur"


class App:
    def __init__(self, win, inst, kleuren=True):
        self.inst = inst
        self.s = Scherm(win, inst, kleuren)
        self.stat = {"goed": 0, "vragen": 0}

    # ---- gedeelde hulpjes --------------------------------------------------

    def tel(self, goed):
        self.stat["vragen"] += 1
        self.stat["goed"] += bool(goed)
        self.s.status = f"Vandaag: {self.stat['goed']}/{self.stat['vragen']} juist"
        self.s.status_kort = f"{self.stat['goed']}/{self.stat['vragen']} juist"

    def bewaar(self):
        instellingen.bewaar(self.inst)

    # ---- schermen ------------------------------------------------------------

    def start(self):
        self.startscherm()
        if not self.inst.naam:
            naam = self.s.invoer([HOOFD], "Hallo! Hoe heet je?")
            if naam:
                self.inst.naam = naam
                self.bewaar()
        self.hoofdmenu()

    def startscherm(self):
        s = self.s
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw([HOOFD], [("Enter", "starten", 10), ("Esc", "stoppen", ESC)])
            h, w = s.maat()
            breedte = 50
            x = (w - breedte) // 2
            y = max(2, (h - 12) // 2)
            regels = [
                ("", ""),
                ("L E E R A V O N T U U R", "accent"),
                ("", ""),
                ("rekenen · taal · Frans", "info"),
                ("", ""),
                (f"Een gratis leerprogramma van {MAKER}", "bold"),
                (MOTTO, "dim"),
                ("", ""),
                ("Druk op een toets om te beginnen", "goed"),
                ("", ""),
            ]
            s.put(y, x, "┌" + "─" * (breedte - 2) + "┐", "accent2")
            for i, (tekst, rol) in enumerate(regels, 1):
                s.put(y + i, x, "│", "accent2")
                s.put(y + i, x + 1 + (breedte - 2 - len(tekst)) // 2, tekst, rol)
                s.put(y + i, x + breedte - 1, "│", "accent2")
            s.put(y + len(regels) + 1, x, "└" + "─" * (breedte - 2) + "┘", "accent2")
            s.put(y + len(regels) + 3, x, f"versie {VERSIE} · {LICENTIE}", "dim")
            s.zones.voeg(1, 0, h - 2, w, 10)
            k = s.toets()
            if k == curses.KEY_RESIZE:
                continue
            if k == ESC:
                raise SystemExit
            return

    def hoofdmenu(self):
        while True:
            try:
                naam = self.inst.naam
                k = self.s.menu([HOOFD], f"Hallo{' ' + naam if naam else ''}! Wat wil je doen?", [
                    ("Leren & oefenen", "wiskunde (taal en Frans volgen)"),
                    ("Spiekbrieven", "uitleg om terug te kijken"),
                    ("Opties", "leerjaar, kleuren (ook kleurenblind), muis …"),
                    ("Stoppen", "")],
                    onder=f"{MAKER} · gratis · {MOTTO.lower()}")
                if k is None or k == 3:
                    return
                if k == 0:
                    self.leren()
                elif k == 1:
                    self.spiekbrieven()
                elif k == 2:
                    self.opties()
            except TerugNaar:
                continue

    def leren(self):
        kr = [HOOFD, "Leren"]
        while True:
            try:
                k = self.s.menu(kr, "Welk vak?", [("Wiskunde", "eenheden (meer onderwerpen volgen)")])
                if k is None:
                    return
                self.wiskunde(kr + ["Wiskunde"])
            except TerugNaar as t:
                if t.niveau < 1:
                    raise

    def wiskunde(self, kr):
        while True:
            try:
                k = self.s.menu(kr, "Welk onderwerp?", [("Eenheden", "lengte en massa omzetten")])
                if k is None:
                    return
                Eenheden(self, kr + ["Eenheden"]).menu()
            except TerugNaar as t:
                if t.niveau < len(kr) - 1:
                    raise

    def spiekbrieven(self):
        kr = [HOOFD, "Spiekbrieven"]
        while True:
            try:
                k = self.s.menu(kr, "Welke spiekbrief?", [("Eenheden", "lengte en massa omzetten")])
                if k is None:
                    return
                Eenheden(self, kr).spiekbrief(kr + ["Eenheden"])
            except TerugNaar as t:
                if t.niveau < 1:
                    raise

    def opties(self):
        s, inst = self.s, self.inst
        kr = [HOOFD, "Opties"]
        themas = list(instellingen.THEMAS)
        sel = 0
        knoppen = [("↑↓", "kiezen", None), ("Enter", "wijzigen", 10), ("Esc", "klaar", ESC)]
        while True:
            items = [
                ("Naam", inst.naam or "(nog geen naam)"),
                ("Leerjaar", leerjaren.NAMEN[inst.leerjaar]),
                ("Kleuren", instellingen.THEMAS[inst.thema]),
                ("Eenvoudige tekens", {None: "automatisch", True: "aan (ASCII)", False: "uit"}[inst.ascii]),
                ("Muis", "aan" if inst.muis else "uit"),
                ("Typrichting in tabellen", "→ naar rechts" if inst.typrichting == 1 else "← naar links"),
            ]
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr, knoppen)
            h, w = s.maat()
            s.put(2, 4, "Kies een optie en druk Enter (of klik) om ze te wijzigen.", "bold")
            for i, (label, waarde) in enumerate(items):
                y = 4 + 2 * i
                s.put(y, 6, f" {label:<24} ", "cursor" if i == sel else "")
                s.put(y, 33, waarde, "accent")
                s.zones.voeg(y, 4, 1, w - 6, ("kies", i))
            y = 5 + 2 * len(items)
            s.put(y, 4, "Voorbeeld:", "dim")
            s.put(y, 15, "✔ juist", "goed")
            s.put(y, 25, "✘ fout", "fout")
            s.put(y, 34, "  5  ", "goedvak")
            s.put(y, 40, "! 6  ", "foutvak")
            s.put(y, 46, " actief ", "cursor")
            s.put(y + 2, 4, "Bij het starten kan het ook: --kleurenblind, --contrast, --geen-kleur,", "dim")
            s.put(y + 3, 4, "--ascii, --geen-muis   (zie python3 oefeningen.py --help)", "dim")
            k = s.toets()
            if isinstance(k, tuple):
                if k[0] == "kies":
                    sel = k[1]
                    k = 10
                elif k[0] == "scroll":
                    sel = (sel + k[1]) % len(items)
                    continue
                else:
                    continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(items)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(items)
            elif k in (ESC, ord("q")):
                self.bewaar()
                return
            elif k in ENTER or k in (curses.KEY_RIGHT, ord(" ")):
                if sel == 0:
                    naam = s.invoer(kr + ["Naam"], "Hoe heet je?", inst.naam)
                    if naam is not None:
                        inst.naam = naam
                elif sel == 1:
                    inst.leerjaar = leerjaren.LEERJAREN[
                        (leerjaren.LEERJAREN.index(inst.leerjaar) + 1) % len(leerjaren.LEERJAREN)]
                elif sel == 2:
                    inst.thema = themas[(themas.index(inst.thema) + 1) % len(themas)]
                elif sel == 3:
                    inst.ascii = {None: True, True: False, False: None}[inst.ascii]
                elif sel == 4:
                    inst.muis = not inst.muis
                elif sel == 5:
                    inst.typrichting = -inst.typrichting
                s.pas_toe()
                self.bewaar()
