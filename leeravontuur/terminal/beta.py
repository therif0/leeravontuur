"""Beta van de schermen 1.0 (werk/schermen.md): Cijferen in vakken, zoals btop. Alleen met LEERAVONTUUR_BETA=1.

De gewone schermen blijven zoals ze zijn. BetaOefenaar tekent alleen een vraag met een rooster of een staartdeling
anders; al de rest (niveau, reeks, rapport, herhaalbak, punten) is de gewone Oefenaar. Het nakijken en bewaren gebeurt
zoals in Oefenaar._stel_vraag voor een invoer-object (rooster en staartdeling hebben geen tweede kans).
"""

import curses
import os
import random
import re
import textwrap

from . import avatar as AV
from . import indeling as I
from . import vak
from ..kern import avatar as A
from ..kern import overzicht as OZ
from .oefenaar import INVOER, KORT_HULP, LOF, Oefenaar, vraagtekst
from .scherm import ENTER, ESC, HULP

DOMEINEN = {"Cijferen"}       # waar de beta geldt (het label van het domein in het leerplan)
INVOER_BETA = {"rooster", "staart"}
GEEN_TIP = {"rooster": "F1 = een tip voor dit vakje.", "staart": "F1 = een tip voor deze stap."}


def aan():
    return os.environ.get("LEERAVONTUUR_BETA") == "1"


def oefenaar_klasse(domein):
    """De Oefenaar voor een domein: de beta voor Cijferen als ze aan staat, anders de gewone."""
    return BetaOefenaar if aan() and domein in DOMEINEN else Oefenaar


def ruim(tekst):
    """De vraag met meer lucht rond + − × : = (ze moet opvallen; groter kan niet in een terminal)."""
    return re.sub(r" ?([+−×:=]) ?", r"  \1  ", tekst).strip()


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
        self.spiek_top, self.spiek_zicht = None, None  # None = bij het stuk van de vraag; zicht = (top, plaats)
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
            if self.spiek_zicht and (top := vak.scroll_stap(k, *self.spiek_zicht)) is not None:  # de spiekbrief
                self.spiek_top = max(0, top)
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
                         extra={"stapfouten": obj.fouten} if obj.fouten else None, verwacht=v.verwacht, vaardigheid=o.id, leerjaar=v.leerjaar)
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
    # bovenaan de reeks; links Vraag, Tip (of de uitleg) en de Spiekbrief; rechts het maatje (terminal/indeling.py).
    # Cijferen heeft geen klad (de vader 22/11: het rooster is het rekenwerk).

    def indeling(self, obj):
        """De vakken voor deze vraag; het object krijgt zijn plaats links in het vak Vraag. Is het breder dan dat vak,
        dan krijgt het de volle breedte (zonder maatje)."""
        s = self.s
        h, w = s.maat()
        klok = s.klokvenster is not None and s.klokvenster.toont()
        ind = I.oefenscherm(h, w, maatje=self.app.inst.avatar, klokvenster=klok)
        obj.plaats(ind.links.binnen.x, ind.links.binnen.w)
        if ind.maatje and obj.breedte(s) > ind.links.binnen.w:
            ind = I.oefenscherm(h, w, maatje=False)
            obj.plaats(ind.links.binnen.x, ind.links.binnen.w)
        return ind

    def teken(self, o, v, obj, soort, ses, nr, resultaten, vrij, goed, tip, spiek, kop, rol, uitleg,
              gezicht, ballon, spring):
        s = self.s
        ind = self.indeling(obj)
        links, b, groot = ind.links, ind.links.binnen, ind.groot
        bezig = goed is None
        self.teken_reeks(ind, ses, nr, resultaten, vrij, goed)
        vy = links.y + 1 + groot      # de vraag, op een band (op een groot scherm 3 rijen hoog)
        oy = vy + 2 + groot           # het object, na een lege rij
        onder = oy + obj.hoogte(not bezig)  # de eerste rij onder het object: daar komt de rand (of de melding)
        mel = regels(obj.melding, b.w)[:2] if bezig and obj.melding else []
        hint = hint_regels(obj.hint, b.w)[:2] if bezig else []
        while hint and onder + 1 + max(1, len(mel)) + len(hint) + 3 > links.onder:  # Tip heeft 3 rijen nodig
            hint.pop()
        if bezig:  # een lege rij onder het object, dan de melding en de hint
            onder += 1
            for i, stuk in enumerate(mel):
                s.put(onder + i, b.x, stuk, obj.melding_rol)
            for i, stuk in enumerate(hint):
                s.put(onder + max(1, len(mel)) + i, b.x, stuk, "dim")
            onder += max(1, len(mel)) + len(hint)
        vraag_r, tip_r, spiek_r = I.verdeel(links, onder - links.y + 1, bezig, spiek)
        titel = (f"Vrij oefenen: {self.vrij_goed + bool(goed)} van {self.vrij_aantal + (goed is not None)} juist"
                 if vrij else f"Vraag {nr + 1} van {self.totaal}")
        niveau = soort.split(" · ")[-1]  # het onderwerp staat al in de broodkruimel
        if len(niveau) + len(titel) + 14 > links.w:
            niveau = niveau.split(" (")[0]
        richting = getattr(obj, "links", None)  # het rooster: een klik op de typrichting = r
        vak.teken(s, vraag_r.y, vraag_r.x, vraag_r.h, vraag_r.w, titel, niveau, obj.randtekst() if bezig else "",
                  ord("r") if bezig and richting is not None else None)
        for r in range(vy - groot, vy + groot + 1):  # de band: één spatie van de rand
            s.put(r, links.x + 2, " " * (links.w - 4), "band")
        s.put(vy, links.x + 4, ruim(v.tekst)[:links.w - 8], "vraag")
        obj.teken(s, oy, goed, tip)
        self.teken_tip(o, v, obj, tip_r, b.w, bezig, tip, spiek, kop, rol, uitleg)
        self.spiek_zicht = None
        if spiek_r:  # de spiekbrief, altijd open (de vader, 22/11); in een examen niet
            self.teken_spiek(o, v, spiek_r)
        if ind.maatje:
            self.teken_maatje(ind.maatje, goed, tip, gezicht, ballon, spring)
        if bezig and obj.cursor_pos:
            s.cursor(True, *obj.cursor_pos)
        else:
            s.cursor(False)

    def teken_tip(self, o, v, obj, r, tw, bezig, tip, spiek, kop, rol, uitleg):
        """Het vak onder de vraag: de tip tijdens het rekenen, de uitleg na het nakijken."""
        s, x = self.s, r.binnen.x
        if bezig:
            vak.teken(s, r.y, r.x, r.h, r.w, "Tip", "", "F1" if self.hulp.tips else "", HULP)
            if not self.hulp.tips:
                tekst, trol = "Geen tips in deze reeks.", "dim"
            elif tip:
                tekst, trol = obj.hulp(o), "accent"
                if spiek and len(regels(tekst + KORT_HULP, tw)) <= r.h - 2:
                    tekst += KORT_HULP
            else:
                tekst, trol = GEEN_TIP[v.invoer], "dim"
            vak.lijst(s, r.y + 1, x, r.h - 2, tw, [(stuk, trol) for stuk in regels(tekst, tw)])
            return
        titel = {"goed": "Goed!", "fout": "Wat ging er mis?"}.get(rol, "Uitleg")  # een examen ("info"): niets verklappen
        vak.teken(s, r.y, r.x, r.h, r.w, titel)
        uit = [(stuk, rol) for stuk in regels(kop, tw)] + [("", "")]
        for regel in uitleg:
            tekst, ro = regel if isinstance(regel, tuple) else (regel, "accent")
            uit += [(stuk, ro) for stuk in regels(tekst, tw, "  " if ro == "" else "")]
        if len(uit) > r.h - 2:
            uit = uit[:r.h - 3] + [("…", "dim")]
        vak.lijst(s, r.y + 1, x, r.h - 2, tw, uit)

    def teken_reeks(self, ind, ses, nr, resultaten, vrij, goed):
        """Bovenaan, onder de broodkruimel: hoe ver je bent (de regel komt uit kern/overzicht.py). Op een groot scherm
        in een vak, anders één regel."""
        s, r = self.s, ind.reeks
        naam = "Vrij oefenen" if vrij else "Reeks"
        goed_lijst = [x["goed"] for x in resultaten] + ([goed] if goed is not None else [])
        regel = OZ.reeks_regel(goed_lijst, nr, self.totaal, ses.punten if ses.met_punten else None, ses.op_rij,
                               (self.vrij_goed + bool(goed), self.vrij_aantal + (goed is not None)) if vrij else None)
        if ind.groot:
            vak.teken(s, r.y, r.x, r.h, r.w, naam)
            y, x = r.y + 1, r.x + 3
        else:
            s.put(r.y, r.x + 1, naam, "accent")
            y, x = r.y, r.x + 1 + len(naam) + 3
        for tekst, rol in regel:
            s.put(y, x, tekst[:max(0, r.rechts - 2 - x)], rol)
            x += len(tekst)

    def teken_spiek(self, o, v, r):
        """De spiekbrief in een vak, met het stuk van deze vraag in het licht (de rest gedimd). Past ze niet: PgUp,
        PgDn, het scrollwiel of een klik op PgUp/PgDn in de rand (vak.scroll_rand)."""
        s, b = self.s, r.binnen
        kop = o.kop_op_spiekbrief(v)
        brief, i_kop = [], None  # de regels, gebroken op de breedte van het vak (met dezelfde inspringing)
        for tekst, ro in o.spiekbrief():
            if tekst == kop:
                i_kop = len(brief)
            inspring = " " * (len(tekst) - len(tekst.lstrip()))
            brief += [(stuk, ro) for stuk in (textwrap.wrap(tekst, b.w + 2, subsequent_indent=inspring + "  ")
                                              if tekst.strip() else [""])]
        stuk, getoond = False, []
        for i, (tekst, ro) in enumerate(brief):
            if i_kop is not None:  # het stuk van de vraag: van het kopje tot de volgende lege regel
                stuk = i >= i_kop and (stuk or i == i_kop) and not (i > i_kop and not tekst.strip())
            getoond.append((("▸ " if i == i_kop else "  ") + tekst, (ro or "") if stuk or i_kop is None else "dim"))
        vak.teken(s, r.y, r.x, r.h, r.w, "Spiekbrief", o.naam)
        top = self.spiek_top if self.spiek_top is not None else (i_kop or 0)
        top, boven, onder = vak.lijst(s, r.y + 1, r.x + 2, r.h - 2, r.w - 4, getoond, top)
        if boven or onder:
            self.spiek_zicht = (top, r.h - 2)
            vak.scroll_rand(s, r.y, r.x, r.h, r.w, boven, onder)

    def teken_maatje(self, r, goed, tip, gezicht, ballon, spring):
        """De rechterkolom: het maatje, van boven tot onder."""
        s = self.s
        vak.teken(s, r.y, r.x, r.h, r.w, "Maatje")
        uitdrukking = "denken" if tip and goed is None else gezicht
        if AV.kan_pixels(s):
            AV.teken(s, r.y + 1 - spring, r.x + 2, self.app.avatar_config(), uitdrukking)
        else:
            s.put(r.y + 4, r.x + 2, A.TEKSTGEZICHT.get(uitdrukking, A.TEKSTGEZICHT["normaal"]), "accent")
        if ballon:
            for i, stuk in enumerate(regels(ballon, r.w - 4)[:3]):
                s.put(r.y + I.MAATJE_H - 2 + i, r.x + 2, stuk, "accent")
