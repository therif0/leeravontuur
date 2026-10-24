"""De terminal-app: startscherm, hoofdmenu, menu's per vak en domein, en opties."""

import curses
from dataclasses import replace

from .. import LICENTIE, MAKER, MOTTO, VERSIE
from ..kern import instellingen, klok, leerjaren
from ..kern.instellingen import Instellingen
from ..kern.sessie import Sessie
from .scherm import ENTER, ESC, Scherm, TerugNaar
from .schermen.eenheden import Eenheden
from .schermen.kinderen import kies_kind

HOOFD = "Leeravontuur"


class App:
    def __init__(self, win, opslag, voorrang=None, kleuren=True):
        """voorrang = instellingen uit de argumenten bij het starten (bv. {"thema": "contrast"})."""
        self.opslag = opslag
        self.voorrang = dict(voorrang or {})
        self.kind = None
        laatste = opslag.kind(opslag.algemeen("laatste_kind") or "")
        self.basis = opslag.instellingen_van(laatste.id) if laatste else Instellingen()
        self.inst = replace(self.basis, **self.voorrang)
        self.s = Scherm(win, self.inst, kleuren)

    # ---- het actieve kind ------------------------------------------------------

    def activeer(self, kind):
        self.kind = kind
        self.basis = self.opslag.instellingen_van(kind.id)
        self.inst = replace(self.basis, **self.voorrang)
        self.s.inst = self.inst
        self.s.pas_toe()
        self.opslag.zet_algemeen("laatste_kind", kind.id)
        self.ververs_status()

    def herlaad_kind(self):
        """Na wijzigingen in het ouderdeel: het actieve kind opnieuw laden (of loslaten als het gewist is)."""
        if self.kind is None:
            return
        kind = self.opslag.kind(self.kind.id)
        if kind is None:
            self.kind = None
            self.s.status = self.s.status_kort = ""
        else:
            self.activeer(kind)

    def vandaag(self):
        """(aantal, juist) van vandaag voor het actieve kind."""
        return self.opslag.telling(self.kind.id, klok.dag()) if self.kind else (0, 0)

    def ververs_status(self):
        n, j = self.vandaag()
        self.s.status = f"Vandaag: {j}/{n} juist" if n else ""
        self.s.status_kort = f"{j}/{n} juist" if n else ""

    def bewaar(self):
        """Bewaart de instellingen van het kind. Wat enkel via een startargument geldt, wordt niet bewaard."""
        if not self.kind:
            return
        te_bewaren = replace(self.inst)
        for veld, waarde in list(self.voorrang.items()):
            if getattr(self.inst, veld) == waarde:
                setattr(te_bewaren, veld, getattr(self.basis, veld))
            else:
                del self.voorrang[veld]  # zelf aangepast in Opties: vanaf nu gewoon bewaren
        self.opslag.bewaar_instellingen(self.kind.id, te_bewaren)
        self.basis = te_bewaren
        self.kind = self.opslag.kind(self.kind.id) or self.kind

    def sessie(self, modus, vaardigheid, leerjaar):
        return Sessie(self.opslag, self.kind.id, modus, vaardigheid, leerjaar, na_antwoord=self.ververs_status)

    # ---- schermen ------------------------------------------------------------

    def start(self, ouder=False):
        self.startscherm()
        if ouder:
            from .schermen.ouder import Ouderdeel
            Ouderdeel(self).open()
            return
        kind = kies_kind(self)
        if kind is None:
            return
        self.activeer(kind)
        self.hoofdmenu()

    def wissel_van_kind(self):
        kind = kies_kind(self)
        if kind is not None:
            self.activeer(kind)

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
            if self.kind is None:  # bv. gewist in het ouderdeel
                kind = kies_kind(self)
                if kind is None:
                    return
                self.activeer(kind)
            try:
                naam = self.inst.naam
                n, j = self.vandaag()
                info = []
                if n:
                    lof = " Goed bezig!" if j >= 0.6 * n else ""
                    info.append(f"Vandaag al {n} {'vraag' if n == 1 else 'vragen'} geoefend, {j} juist.{lof}")
                if self.opslag.probleem:
                    info.append(self.opslag.probleem)
                k = self.s.menu([HOOFD], f"Hallo{' ' + naam if naam else ''}! Wat wil je doen?", [
                    ("Leren & oefenen", "wiskunde (taal en Frans volgen)"),
                    ("Spiekbrieven", "uitleg om terug te kijken"),
                    ("Opties", "leerjaar, kleuren (ook kleurenblind), muis …"),
                    ("Wissel van kind", "iemand anders wil oefenen"),
                    ("Stoppen", "")], info=info,
                    onder=f"{MAKER} · gratis · {MOTTO.lower()}")
                if k is None or k == 4:
                    return
                if k == 0:
                    self.leren()
                elif k == 1:
                    self.spiekbrieven()
                elif k == 2:
                    self.opties()
                elif k == 3:
                    self.wissel_van_kind()
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
        sel, melding = 0, ""
        knoppen = [("↑↓", "kiezen", None), ("Enter", "wijzigen", 10), ("Esc", "klaar", ESC)]
        while True:
            items = [
                ("Naam", inst.naam or "(nog geen naam)"),
                ("Leerjaar", leerjaren.NAMEN[inst.leerjaar] + "  (wijzigen: ouders)"),
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
            s.put(y + 5, 4, melding, "info")
            k = s.toets()
            melding = ""
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
                    if naam:
                        inst.naam = naam
                elif sel == 1:
                    melding = "Het leerjaar kan een ouder wijzigen: Wissel van kind → Ouders → Kinderen."
                    continue
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
