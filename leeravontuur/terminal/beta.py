"""Beta van de schermen 1.0 (werk/schermen.md): Cijferen in vakken, zoals btop. Alleen met LEERAVONTUUR_BETA=1.

De gewone schermen blijven zoals ze zijn. BetaOefenaar tekent alleen een vraag met een rooster of een staartdeling
anders; al de rest (niveau, reeks, rapport, herhaalbak, punten) is de gewone Oefenaar. Het nakijken en bewaren gebeurt
zoals in Oefenaar._stel_vraag voor een invoer-object (rooster en staartdeling hebben geen tweede kans).
"""

import curses
import os
import random
import textwrap

from . import avatar as AV
from . import vak
from ..kern import avatar as A
from .oefenaar import INVOER, KORT_HULP, LOF, Oefenaar, vraagtekst
from .scherm import ENTER, ESC, HULP

DOMEINEN = {"Cijferen"}       # waar de beta geldt (het label van het domein in het leerplan)
INVOER_BETA = {"rooster", "staart"}
RECHTS = 20                   # de rechterkolom: het maatje en de reeks
MAATJE_H = 11                 # het vak van het maatje: 8 rijen pixels, het tekstje en de rand
TIP_H, UITLEG_H = 8, 14     # hoogstens zo hoog op een groot scherm (anders een groot leeg vak)
VERSCHUIF = {"rooster": -6, "staart": -3}  # het object tekent op vaste kolommen: zo komt het in het vak
KORTER = {"uitkomst  (typrichting ←)": "uitkomst", "uitkomst  (typrichting →)": "uitkomst"}  # de richting staat in de rand
GEEN_TIP = {"rooster": "F1 = een tip voor dit vakje.", "staart": "F1 = een tip voor deze stap."}


def aan():
    return os.environ.get("LEERAVONTUUR_BETA") == "1"


def oefenaar_klasse(domein):
    """De Oefenaar voor een domein: de beta voor Cijferen als ze aan staat, anders de gewone."""
    return BetaOefenaar if aan() and domein in DOMEINEN else Oefenaar


class InVak:
    """Het scherm zoals een invoer-object het ziet: verschoven met dx en afgeknipt aan de rand van het vak."""

    def __init__(self, s, dx, links, rechts):
        self.s, self.dx, self.links, self.rechts = s, dx, links, rechts
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        tekst = KORTER.get(tekst, tekst)
        x += self.dx
        if x < self.links:
            tekst, x = tekst[self.links - x:], self.links
        self.s.put(y, x, tekst[:max(0, self.rechts - x)], rol)

    def voeg(self, y, x, h, w, actie):
        self.s.zones.voeg(y, x + self.dx, h, w, actie)

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.s.tekstvak(y, x + self.dx, tekst, breedte, rol, actie)

    def __getattr__(self, naam):
        return getattr(self.s, naam)


def regels(tekst, breed, inspring=""):
    return textwrap.wrap(tekst, breed, subsequent_indent=inspring) or [""]


def hint_regels(tekst, breed):
    """Een hint met " · " ertussen: een nieuwe regel tussen de stukken, niet midden in een stuk."""
    uit = [""]
    for stuk in tekst.split(" · "):
        if uit[-1] and len(uit[-1]) + 3 + len(stuk) > breed:
            uit.append("")
        uit[-1] += (" · " if uit[-1] else "") + stuk
    return [r for u in uit for r in regels(u, breed)]


class BetaOefenaar(Oefenaar):
    def _stel_vraag(self, kr, o, v, soort, ses, nr, resultaten, vrij):
        if v.invoer not in INVOER_BETA:
            return super()._stel_vraag(kr, o, v, soort, ses, nr, resultaten, vrij)
        s = self.s
        obj = INVOER[v.invoer](v, o)
        if hasattr(obj, "plaatswaarden"):  # het rooster: de keuze van het kind (#18)
            obj.plaatswaarden = self.app.inst.plaatswaarden
        spiek = bool(o.spiekbrief()) and self.hulp.spiekbrief
        goed, buf, getal, d, extra = None, "", None, None, ""
        tip = tip_gebruikt = False
        laatste_hulp = None  # nog eens F1 op dezelfde plek = de spiekbrief
        gezicht, ballon, spring = "normaal", "", False
        kop, rol, uitleg = "", "", []
        self.herkansing = False
        ses.vraag_getoond()
        lof = random.choice(LOF)
        while True:
            if s.te_klein():
                continue
            if goed is not None:
                laatste = not vrij and nr == self.totaal - 1
                knoppen = [("Enter", "naar je resultaat" if laatste else "volgende vraag", 10),
                           ("Esc", "stoppen", ESC)]
            else:
                knoppen = obj.knoppen()
            if not self.hulp.tips:  # zonder hulp (een examen): geen F1
                knoppen = [kn for kn in knoppen if kn[2] != HULP]
            s.nieuw(kr, knoppen)
            self.teken(o, v, obj, soort, ses, nr, resultaten, vrij, goed, tip, spiek, kop, rol, uitleg,
                       gezicht, ballon, spring)
            if spring:
                s.pauze(170)
                spring = False
                continue
            self.open = goed is None  # voor de bewaker: nog niet nagekeken
            k = s.toets()
            if k == curses.KEY_RESIZE:
                continue
            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return buf, goed, False
                if k == ESC:
                    return buf, goed, True
                continue
            if k == ESC:  # al bevestigd in het kader (Scherm.bewaak, #33)
                s.cursor(False)
                return None
            if k == HULP:
                if not self.hulp.tips:
                    continue
                tip = tip_gebruikt = True
                hulp = obj.hulp(o)
                if spiek and hulp == laatste_hulp:
                    laatste_hulp, tip = None, False
                    self.spiekbrief(kr + ["Spiekbrief"], o, v)
                else:
                    laatste_hulp = hulp
                continue
            uit = obj.toets(k)
            if getattr(obj, "plaatswaarden", None) not in (None, self.app.inst.plaatswaarden):
                self.app.inst.plaatswaarden = obj.plaatswaarden  # p: onthouden voor dit kind
                self.app.bewaar()
            if uit is None:
                continue
            buf, getal = uit
            goed = o.nakijken(v, getal) and not obj.fouten
            d = (obj.diagnose or o.diagnose_rijen(v, obj.rijen())) or o.diagnose(v, getal)
            self.laatste_d = d
            ses.antwoord(v.sleutel, vraagtekst(v), buf.strip(), goed, d[0] if d else None, hulp=tip_gebruikt,
                         extra={"stapfouten": obj.fouten} if obj.fouten else None, verwacht=v.verwacht,
                         vaardigheid=o.id, leerjaar=v.leerjaar)
            extra = self.tijd_tekst(ses) + (f"  +{ses.laatste_punten} punten" if ses.laatste_punten else "")
            gezicht, ballon = A.reactie(goed, ses.op_rij, d[0] if d else None)
            spring = goed and self.app.inst.animaties and self.app.inst.avatar
            if goed:
                kop, rol, uitleg = "✔ " + lof + extra, "goed", self.uitwerking(o, v) if vrij else []
            elif obj.fouten and getal == v.antwoord:
                kop, rol = f"! De uitkomst klopt, maar onderweg ging het {obj.fouten} keer mis.{extra}", "accent"
                uitleg = ([d[1]] if d else []) + o.uitleg(v)
            else:
                kop, rol = f"✘ Niet juist. Het juiste antwoord is {v.verwacht}.{extra}", "fout"
                uitleg = ([d[1]] if d else []) + self.uitwerking(o, v)
            if not self.hulp.uitleg_na:  # zonder hulp (een examen): niet zeggen of het juist was
                gezicht, ballon, spring = "normaal", "", False
                kop, rol, uitleg = "Je antwoord is bewaard.", "info", []

    # ---- tekenen in vakken -------------------------------------------------------------

    def teken(self, o, v, obj, soort, ses, nr, resultaten, vrij, goed, tip, spiek, kop, rol, uitleg,
              gezicht, ballon, spring):
        s = self.s
        h, w = s.maat()
        links = w - RECHTS  # de breedte van de linkerkolom
        tw = links - 6      # tekst in een vak
        bezig = goed is None
        # het vak Vraag: de opgave, het rooster (of de staartdeling), de melding en de hint
        pw = 1 if getattr(obj, "toont_plaatswaarden", lambda: False)() else 0
        oy = 4 + pw
        onder = oy + obj.hoogte(not bezig)  # de eerste rij onder het object: daar komt de rand (of de melding)
        mel = regels(obj.melding, tw)[:2] if bezig and obj.melding else []
        hint = hint_regels(obj.hint, tw)[:2] if bezig else []
        while hint and onder + max(1, len(mel)) + len(hint) + 3 > h - 1:  # het vak Tip heeft 3 rijen nodig
            hint.pop()
        if bezig:
            for i, stuk in enumerate(mel):
                s.put(onder + i, 3, stuk, obj.melding_rol)
            for i, stuk in enumerate(hint):
                s.put(onder + max(1, len(mel)) + i, 3, stuk, "dim")
            onder += max(1, len(mel)) + len(hint)
        titel = (f"Vrij oefenen: {self.vrij_goed + bool(goed)} van {self.vrij_aantal + (goed is not None)} juist"
                 if vrij else f"Vraag {nr + 1} van {self.totaal}")
        niveau = soort.split(" · ")[-1]  # het onderwerp staat al in de broodkruimel
        if len(niveau) + len(titel) + 14 > links:
            niveau = niveau.split(" (")[0]
        richting = getattr(obj, "links", None)
        vak.teken(s, 1, 0, onder, links, titel, niveau,
                  ("typrichting ←" if richting else "typrichting →") if bezig and richting is not None else "",
                  ord("r") if bezig and richting is not None else None)
        s.put(2, 3, v.tekst, "bold")
        obj.teken(InVak(s, VERSCHUIF[v.invoer], 2, links - 2), oy, goed, tip)
        # het vak eronder: de tip tijdens het rekenen, de uitleg na het nakijken
        ty = onder + 1
        th = min(h - 1 - ty, TIP_H if bezig else UITLEG_H)
        if bezig:
            vak.teken(s, ty, 0, th, links, "Tip", "", "F1" if self.hulp.tips else "", HULP)
            if not self.hulp.tips:
                tekst, trol = "Geen tips in deze reeks.", "dim"
            elif tip:
                tekst, trol = obj.hulp(o), "accent"
                if spiek and len(regels(tekst + KORT_HULP, tw)) <= th - 2:
                    tekst += KORT_HULP
            else:
                tekst, trol = GEEN_TIP[v.invoer], "dim"
            for i, stuk in enumerate(regels(tekst, tw)[:th - 2]):
                s.put(ty + 1 + i, 3, stuk, trol)
        else:
            vak.teken(s, ty, 0, th, links, "Goed!" if goed else "Wat ging er mis?" if rol == "fout" else "Uitleg")
            uit = [(stuk, rol) for stuk in regels(kop, tw)] + [("", "")]
            for regel in uitleg:
                tekst, r = regel if isinstance(regel, tuple) else (regel, "accent")
                uit += [(stuk, r) for stuk in regels(tekst, tw, "  " if r == "" else "")]
            plaats = th - 2
            if len(uit) > plaats:
                uit = uit[:plaats - 1] + [("…", "dim")]
            for i, (stuk, r) in enumerate(uit):
                s.put(ty + 1 + i, 3, stuk, r)
        self.teken_rechts(links, h, ses, nr, resultaten, vrij, goed, tip, gezicht, ballon, spring)
        if bezig and obj.cursor_pos:
            y, x = obj.cursor_pos
            s.cursor(True, y, x + VERSCHUIF[v.invoer])
        else:
            s.cursor(False)

    def teken_rechts(self, x, h, ses, nr, resultaten, vrij, goed, tip, gezicht, ballon, spring):
        """De rechterkolom: het maatje (als het aan staat) en de reeks."""
        s, inst = self.s, self.app.inst
        y = 1
        if inst.avatar:
            vak.teken(s, 1, x, MAATJE_H, RECHTS, "Maatje")
            uitdrukking = "denken" if tip and goed is None else gezicht
            if AV.kan_pixels(s):
                AV.teken(s, 2 - spring, x + 2, self.app.avatar_config(), uitdrukking)
            else:
                s.put(5, x + 2, A.TEKSTGEZICHT.get(uitdrukking, A.TEKSTGEZICHT["normaal"]), "accent")
            if ballon:
                s.put(MAATJE_H - 1, x + max(1, (RECHTS - len(ballon)) // 2), ballon[:RECHTS - 2], "accent")
            y = 1 + MAATJE_H
        vak.teken(s, y, x, h - 1 - y, RECHTS, "Vrij" if vrij else "Reeks")
        if vrij:
            regels_ = [(f"juist   {self.vrij_goed + bool(goed)} van {self.vrij_aantal + (goed is not None)}", "")]
        else:
            for i in range(min(self.totaal, RECHTS - 4)):
                if i < len(resultaten) or (i == nr and goed is not None):
                    ch, r = ("✔", "goed") if (resultaten[i]["goed"] if i < len(resultaten) else goed) else ("✘", "fout")
                else:
                    ch, r = ("◉", "accent") if i == nr else ("○", "dim")
                s.put(y + 1, x + 2 + i, ch, r)
            juist, gedaan = sum(r["goed"] for r in resultaten) + bool(goed), len(resultaten) + (goed is not None)
            regels_ = [("", ""), (f"vraag   {nr + 1} van {self.totaal}", "")]
            if gedaan:
                regels_.append((f"juist   {juist} van {gedaan}", ""))
            y += 1
        if ses.met_punten:
            regels_.append((f"punten  +{ses.punten}", ""))
        if ses.op_rij >= 2:
            regels_.append((f"op rij  {ses.op_rij}", "accent"))
        for i, (tekst, r) in enumerate(regels_[:max(0, h - 3 - y)]):
            s.put(y + 1 + i, x + 2, tekst, r)
