"""Mijn avatar, de winkel en de kast (paskamer)."""

import curses
import textwrap

from ...kern import avatar as A
from ...kern import winkel as W
from ...kern.instellingen import STRAFFEN
from .. import avatar as AV
from ..scherm import BACKSPACE, ENTER, ESC

HOOFD = "Leeravontuur"


class AvatarSchermen:
    def __init__(self, app):
        self.app = app
        self.s = app.s
        self.o = app.opslag

    @property
    def kind(self):
        return self.app.kind

    def saldo(self):
        return self.o.punten_saldo(self.kind.id)

    def config(self):
        return self.app.avatar_config()

    def melding(self, kr, regels, gezicht="blij"):
        rollen = [(r, "fout" if r.startswith("✘") else "goed" if r.startswith("✔") else "") for r in regels]
        self.s.lezer(kr, rollen, [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})

    # ---- Mijn avatar ----------------------------------------------------------------

    def hub(self):
        s = self.s
        kr = [HOOFD, "Mijn avatar"]
        gezichten = list(A.onderdelen()["uitdrukkingen"])
        i = gezichten.index("blij")
        knoppen = [("W", "winkel", ord("w")), ("K", "kast", ord("k")), ("←→", "gezichtje", None),
                   ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr, knoppen)
            AV.teken_groot(s, 3, 4, self.config(), gezichten[i])
            s.zones.voeg(3, 4, 16, 32, curses.KEY_RIGHT)
            x = 40
            s.put(3, x, self.kind.naam, "accent")
            s.put(5, x, f"★ {self.saldo()} punten", "bold")
            s.put(7, x, f"Gezichtje: {gezichten[i]}", "")
            s.put(8, x, "(klik op je avatar of gebruik ← →)", "dim")
            y = 10
            for b in W.onderweg(self.o, self.kind.id):
                item = W.zoek(b["laag"], b["sleutel"])
                gedaan, nodig, eenheid = W.voortgang(self.o, self.kind.id, b)
                s.put(y, x, f"Pakje onderweg: {item.naam if item else b['sleutel']}", "info")
                s.put(y + 1, x + 2, f"{'█' * gedaan}{'░' * (nodig - gedaan)} {gedaan}/{nodig} {eenheid}", "dim")
                y += 3
            s.put(max(y, 14), x, "[W] naar de winkel: koop iets nieuws", "")
            s.zones.voeg(max(y, 14), x, 1, 36, ord("w"))
            s.put(max(y, 14) + 1, x, "[K] naar je kast: trek iets anders aan", "")
            s.zones.voeg(max(y, 14) + 1, x, 1, 38, ord("k"))
            k = s.toets()
            if k in (ESC, ord("q")):
                return
            if k == curses.KEY_RIGHT:
                i = (i + 1) % len(gezichten)
            elif k == curses.KEY_LEFT:
                i = (i - 1) % len(gezichten)
            elif k in (ord("w"), ord("W")):
                self.winkel()
            elif k in (ord("k"), ord("K")):
                self.kast()

    # ---- de winkel --------------------------------------------------------------------

    def winkel(self):
        kr = [HOOFD, "Mijn avatar", "Winkel"]
        lagen = list(W.LAGEN)
        while True:
            k = self.s.menu(kr, f"Wat wil je bekijken? (je hebt {self.saldo()} punten)",
                            [(W.LAGEN[l], f"{len(W.catalogus(l))} items") for l in lagen])
            if k is None:
                return
            self.rek(kr + [W.LAGEN[lagen[k]]], lagen[k])

    def status(self, item, kast, bezit):
        if (item.laag, item.sleutel) in kast:
            return "✔ in je kast", "goed"
        if (item.laag, item.sleutel) in bezit:
            return "pakje onderweg", "info"
        return f"{item.prijs} ★", "accent" if item.prijs <= self.saldo() else "dim"

    def rek(self, kr, laag):
        s = self.s
        items = W.catalogus(laag)
        sel = 0
        knoppen = [("↑↓", "kiezen", None), ("Enter", "kopen of aantrekken", 10), ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            kast, bezit = W.in_kast(self.o, self.kind.id), W.gekocht(self.o, self.kind.id)
            s.cursor(False)
            s.nieuw(kr, knoppen)
            h, w = s.maat()
            s.put(2, 4, f"Je hebt ★ {self.saldo()} punten. Kies iets om het te passen.", "bold")
            for i, item in enumerate(items):
                y = 4 + i
                status, rol = self.status(item, kast, bezit)
                s.put(y, 4, f" {item.naam:<18} ", "cursor" if i == sel else "")
                s.put(y, 26, status, rol)
                s.zones.voeg(y, 2, 1, 40, ("kies", i))
            pas = dict(self.config(), **{laag: items[sel].sleutel})
            AV.teken(s, 5, w - AV.BREEDTE - 6, pas, "blij")
            s.put(5 + AV.HOOGTE + 1, w - AV.BREEDTE - 8, "zo zie je eruit", "dim")
            k = s.toets()
            if isinstance(k, tuple):
                if k[0] == "kies":
                    if sel == k[1]:
                        self.koop(kr, items[sel])
                    sel = k[1]
                elif k[0] == "scroll":
                    sel = (sel + k[1]) % len(items)
                continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(items)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(items)
            elif k in ENTER:
                self.koop(kr, items[sel])
            elif k in (ESC, ord("q")):
                return

    def vraag(self, kr, tekst, gezicht="denken", extra=()):
        """Een rekenvraag met een antwoordvak (alleen cijfers). Geeft het getal of None (Esc)."""
        s = self.s
        buf = ""
        knoppen = [("Enter", "ok", 10), ("Esc", "toch niet kopen", ESC)]
        while True:
            if s.te_klein():
                continue
            s.nieuw(kr, knoppen)
            h, w = s.maat()
            AV.teken(s, 2, w - AV.BREEDTE - 3, self.config(), gezicht)
            y = 3
            for regel in extra:
                s.put(y, 4, regel, "accent")
                y += 1
            y += 1
            for stuk in textwrap.wrap(tekst, 52):
                s.put(y, 4, stuk, "bold")
                y += 1
            s.put(y + 1, 4, "Antwoord:", "bold")
            s.tekstvak(y + 1, 15, buf, 8, "veld")
            s.cursor(True, y + 1, 16 + len(buf))
            k = s.toets()
            if k == ESC:
                s.cursor(False)
                return None
            if k in ENTER and buf:
                s.cursor(False)
                return int(buf)
            if isinstance(k, int):
                if k in BACKSPACE:
                    buf = buf[:-1]
                elif ord("0") <= k <= ord("9") and len(buf) < 7:
                    buf += chr(k)

    def koop(self, kr, item):
        kast, bezit = W.in_kast(self.o, self.kind.id), W.gekocht(self.o, self.kind.id)
        if (item.laag, item.sleutel) in kast:
            W.draag(self.o, self.kind.id, item.laag, item.sleutel)
            self.melding(kr + [item.naam], [f"✔ Je draagt nu: {item.naam}."])
            return
        if (item.laag, item.sleutel) in bezit:
            gedaan, nodig, eenheid = W.voortgang(self.o, self.kind.id, bezit[(item.laag, item.sleutel)])
            self.melding(kr + [item.naam], [f"Je pakje met {item.naam} is onderweg.",
                                            f"Nog {nodig - gedaan} {eenheid}, dan komt het aan."])
            return
        saldo = self.saldo()
        if saldo < item.prijs:
            ch = W.spaar_vraag(saldo, item.prijs)
            antw = self.vraag(kr + [item.naam], ch.vraag, "denken", ["Dat is nog te duur."])
            if antw is None:
                return
            if antw == ch.antwoord:
                self.melding(kr + [item.naam], [f"✔ Juist! Nog {ch.antwoord} punten sparen.", "",
                                                ch.lesje[1], "Oefenen maar!"])
            else:
                self.melding(kr + [item.naam], [f"✘ Niet helemaal: het is {ch.antwoord}.", "", *ch.lesje])
            return
        ch = W.challenge(saldo, item.prijs, self.app.inst.leerjaar)
        antw = self.vraag(kr + [item.naam], ch.vraag, "blij", [f"{item.naam} kopen? Reken eerst even mee."])
        if antw is None:
            return
        tweede = False
        if antw != ch.antwoord:
            antw = self.vraag(kr + [item.naam], ch.vraag, "verrast", ["Ben je zeker? Kijk nog eens goed."])
            if antw is None:
                return
            tweede = True
        juist = antw == ch.antwoord
        levering = W.koop(self.o, self.kind.id, item, ch.betalen, juist, self.app.inst.winkel_straf)
        if juist:
            lof = "Goed dat je het nakeek!" if tweede else "Goed gerekend!"
            regels = [f"✔ {lof} Je hebt nog {ch.antwoord} punten.", "", f"{item.naam} zit in je kast."]
            k = self.s.menu(kr + [item.naam], f"Gekocht: {item.naam}! Meteen aantrekken?",
                            [("Ja, aantrekken", ""), ("Nee, later", "")], info=regels)
            if k == 0:
                W.draag(self.o, self.kind.id, item.laag, item.sleutel)
            return
        regels = [f"✘ Het juiste antwoord was {ch.antwoord}. Zo reken je het uit:", "", *ch.lesje, ""]
        straf = self.app.inst.winkel_straf
        if levering and levering["soort"] == "pakje":
            regels += ["Oei, de koerier is verdwaald!",
                       f"Je pakje met {item.naam} komt aan na {levering['nodig']} juiste antwoorden."]
        elif levering and levering["soort"] == "tijd":
            regels += ["Oei, de koerier is verdwaald!",
                       f"Je pakje met {item.naam} komt aan na {levering['minuten']} minuten oefenen."]
        elif straf == "kosten":
            regels += [f"Je krijgt {item.naam} meteen, maar je betaalt {W.VERZENDKOSTEN} punten verzendkosten."]
        else:
            regels += [f"{item.naam} zit toch in je kast. Probeer de volgende som goed te maken!"]
        self.melding(kr + [item.naam, "Lesje"], regels, "aanmoedigend")

    # ---- de kast (paskamer) -----------------------------------------------------------

    def kast(self):
        s = self.s
        kr = [HOOFD, "Mijn avatar", "Kast"]
        lagen = list(W.LAGEN)
        sel = 0
        knoppen = [("↑↓", "laag", None), ("←→", "wisselen", None), ("B", "bewaren", ord("b")),
                   ("C", "combinaties", ord("c")), ("Esc", "klaar", ESC)]
        while True:
            if s.te_klein():
                continue
            kast = W.in_kast(self.o, self.kind.id)
            config = self.config()
            s.cursor(False)
            s.nieuw(kr, knoppen)
            s.put(2, 4, "Kies wat je aantrekt. (← → om te wisselen)", "bold")
            for i, laag in enumerate(lagen):
                y = 4 + 2 * i
                naam = A.opties(laag).get(config[laag], "—") if config[laag] else "niets"
                aantal = len(self.keuzes(laag, kast))
                s.put(y, 4, f" {W.LAGEN[laag]:<12} ", "cursor" if i == sel else "")
                s.put(y, 19, f"◀ {naam} ▶", "accent")
                s.put(y, 38, f"({aantal})", "dim")
                s.zones.voeg(y, 2, 1, 16, ("kies", i))
                s.zones.voeg(y, 19, 1, 2, ("links", i))
                s.zones.voeg(y, 21 + len(naam), 1, 2, ("rechts", i))
            AV.teken_groot(s, 3, 44, config, "blij")
            k = s.toets()
            richting = 0
            if isinstance(k, tuple):
                if k[0] == "kies":
                    sel = k[1]
                elif k[0] in ("links", "rechts"):
                    sel, richting = k[1], -1 if k[0] == "links" else 1
                elif k[0] == "scroll":
                    sel = (sel + k[1]) % len(lagen)
            elif k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(lagen)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(lagen)
            elif k == curses.KEY_LEFT:
                richting = -1
            elif k in (curses.KEY_RIGHT, *ENTER, ord(" ")):
                richting = 1
            elif k in (ord("b"), ord("B")):
                naam = s.invoer(kr + ["Bewaren"], "Hoe noem je deze combinatie?", max_lengte=16)
                if naam:
                    self.o.bewaar_outfit(self.kind.id, naam, config)
            elif k in (ord("c"), ord("C")):
                self.combinaties(kr)
            elif k in (ESC, ord("q")):
                return
            if richting:
                laag = lagen[sel]
                keuzes = self.keuzes(laag, kast)
                nu = keuzes.index(config[laag]) if config[laag] in keuzes else 0
                W.draag(self.o, self.kind.id, laag, keuzes[(nu + richting) % len(keuzes)])

    @staticmethod
    def keuzes(laag, kast):
        uit = [s for (l, s) in sorted(kast) if l == laag]
        if A.STANDAARD[laag] is None:
            uit = [None] + uit
        return uit

    def combinaties(self, kr):
        outfits = self.o.outfits(self.kind.id)
        if not outfits:
            self.melding(kr + ["Combinaties"], ["Je hebt nog geen combinaties bewaard.",
                                                "Druk B in de kast om je huidige kleren te bewaren."])
            return
        k = self.s.menu(kr + ["Combinaties"], "Welke combinatie wil je aantrekken?",
                        [(o["naam"], "") for o in outfits] + [("Een combinatie weggooien", "")])
        if k is None:
            return
        if k == len(outfits):
            w = self.s.menu(kr + ["Weggooien"], "Welke combinatie gooi je weg?", [(o["naam"], "") for o in outfits])
            if w is not None:
                self.o.verwijder_outfit(outfits[w]["id"])
            return
        kast = W.in_kast(self.o, self.kind.id)
        for laag, sleutel in outfits[k]["config"].items():
            if laag in W.LAGEN and (sleutel is None or (laag, sleutel) in kast):
                W.draag(self.o, self.kind.id, laag, sleutel)


def straf_tekst(straf):
    return STRAFFEN.get(straf, straf)
