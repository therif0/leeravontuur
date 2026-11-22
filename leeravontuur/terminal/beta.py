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
from . import vak
from .kladblad import LEEG_ENTER, Kladblad
from ..kern import avatar as A
from .oefenaar import INVOER, KORT_HULP, LOF, Oefenaar, vraagtekst
from .scherm import ENTER, ESC, HULP, teken_van

DOMEINEN = {"Cijferen"}       # waar de beta geldt (het label van het domein in het leerplan)
INVOER_BETA = {"rooster", "staart"}
RECHTS = 20                   # de rechterkolom: het maatje
MAATJE_H = 11                 # 8 rijen pixels, het tekstje en de rand
TIP_H, UITLEG_H = 6, 14       # hoogstens zo hoog als de spiekbrief eronder past
KLAD_MIN, KLAD_MAX = 24, 34   # de kolom van het klad: zoveel kolommen moeten over zijn, en hoogstens zo breed
SPIEK_MIN = 4                 # de spiekbrief komt onderaan als er zoveel rijen over zijn (anders: scrollen)
GROOT_H = 30                  # vanaf zoveel rijen: de reeks in een vak en lucht rond de vraag
TAB, KLAD, OBJECT = 9, "klad", "object"
STAPPEN = "deel → maal → min → neer"  # staat bij de staartdeling in de rand van het vak
VERSCHUIF = {"rooster": -6, "staart": -3}  # het object tekent op vaste kolommen: zo komt het in het vak
KORTER = {"uitkomst  (typrichting ←)": "uitkomst", "uitkomst  (typrichting →)": "uitkomst"}  # de richting staat in de rand
RUSTIG = {"bold": "", "cursor": "b_cursor"}  # de cijfers in het rooster gewoon (de vraag valt op), de cursor donkergeel
GEEN_TIP = {"rooster": "F1 = een tip voor dit vakje.", "staart": "F1 = een tip voor deze stap."}


def aan():
    return os.environ.get("LEERAVONTUUR_BETA") == "1"


def oefenaar_klasse(domein):
    """De Oefenaar voor een domein: de beta voor Cijferen als ze aan staat, anders de gewone."""
    return BetaOefenaar if aan() and domein in DOMEINEN else Oefenaar


class InVak:
    """Het scherm zoals een invoer-object het ziet: verschoven met dx en afgeknipt aan de rand van het vak."""

    def __init__(self, s, dx, links, rechts, rollen=None):
        self.s, self.dx, self.links, self.rechts = s, dx, links, rechts
        self.rollen = rollen or {}  # andere rollen dan het object vraagt (bv. een rustiger rooster)
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        tekst = KORTER.get(tekst, tekst)
        rol = self.rollen.get(rol, rol)
        if tekst.startswith(STAPPEN[:6]):  # "deel → maal …": in de rand van het vak
            return
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


class Meter:
    """Een nepscherm dat alleen meet hoe breed een invoer-object tekent (om het vak Vraag zo breed te maken)."""

    def __init__(self):
        self.rechts = 0
        self.zones = self

    def put(self, y, x, tekst, rol=""):
        if tekst.strip():
            self.rechts = max(self.rechts, x + len(tekst.rstrip()))

    def voeg(self, *_):
        pass

    def tekstvak(self, y, x, tekst, breedte, rol, actie=None):
        self.rechts = max(self.rechts, x + breedte + 2)


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
        self.kb, self.focus = Kladblad(), OBJECT  # het klad naast de som (alleen waar het past)
        self.kb_plek = None
        self.spiek_top, self.spiek_zicht = None, None  # None = bij het stuk van de vraag; zicht = (top, plaats, n)
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
            elif self.focus == KLAD:
                knoppen = [("Tab", "naar de som", TAB), ("Enter", "regel nakijken", 10), ("F1", "tip", HULP),
                           ("Esc", "stoppen", ESC)]
            else:
                knoppen = obj.knoppen()
            if not self.hulp.tips:  # zonder hulp (een examen): geen F1
                knoppen = [kn for kn in knoppen if kn[2] != HULP]
            s.nieuw(kr, knoppen)
            self.teken(o, v, obj, soort, ses, nr, resultaten, vrij, goed, tip, spiek, kop, rol, uitleg,
                       gezicht, ballon, spring)
            if goed is None and self.focus == OBJECT and self.kb_plek:  # pas na het tekenen weten we of het klad past
                s.voet([("Tab", "klad", TAB)] + [kn for kn in knoppen if kn[0] != "r"])  # r staat ook in de rand
            if spring:
                s.pauze(170)
                spring = False
                continue
            self.open = goed is None  # voor de bewaker: nog niet nagekeken
            k = s.toets()
            if k == curses.KEY_RESIZE:
                continue
            if self.spiek_zicht and (k in (curses.KEY_PPAGE, curses.KEY_NPAGE) or
                                     (isinstance(k, tuple) and k[0] == "scroll")):  # de spiekbrief scrollen
                top, plaats, n = self.spiek_zicht
                stap = k[1] * 3 if isinstance(k, tuple) else (plaats - 1) * (-1 if k == curses.KEY_PPAGE else 1)
                self.spiek_top = max(0, min(n - plaats, top + stap))
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
            if self.kb_plek and isinstance(k, tuple) and k[0] in ("klad", "focus"):  # een klik in het klad
                self.focus = KLAD
                if k[0] == "klad":
                    self.kb.haal_terug(k[1])
                continue
            if self.focus == KLAD and k != HULP:
                if isinstance(k, tuple):  # een klik op de som: terug naar de som
                    self.kb.rond_af()
                    self.focus = OBJECT
                elif k == TAB or self.kb.toets(k, teken_van(k), self.kb_plek[2]) == LEEG_ENTER:
                    self.kb.rond_af()
                    self.focus = OBJECT
                    continue
                else:
                    continue
            elif self.kb_plek and k == TAB:  # Tab = het klad, zoals in elke oefening
                self.focus = KLAD
                continue
            elif self.kb_plek and v.invoer == "rooster" and k == curses.KEY_DOWN and \
                    0 <= obj.rij < len(obj.r.invul) - 1:
                k = TAB  # ↓ = de volgende rij, rechts beginnen (wat Tab in het rooster deed)
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
            self.kb.rond_af()
            self.focus = OBJECT
            goed = o.nakijken(v, getal) and not obj.fouten
            d = (obj.diagnose or o.diagnose_rijen(v, obj.rijen())) or o.diagnose(v, getal)
            self.laatste_d = d
            ses.antwoord(v.sleutel, vraagtekst(v), buf.strip(), goed, d[0] if d else None, hulp=tip_gebruikt,
                         extra={k_: w for k_, w in (("stapfouten", obj.fouten), ("klad", self.kb.teksten)) if w}
                         or None, verwacht=v.verwacht, vaardigheid=o.id, leerjaar=v.leerjaar)
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
    # bovenaan de reeks; links Vraag, Tip (of de uitleg) en de Spiekbrief; ernaast het klad van boven tot onder;
    # rechts het maatje

    def teken(self, o, v, obj, soort, ses, nr, resultaten, vrij, goed, tip, spiek, kop, rol, uitleg,
              gezicht, ballon, spring):
        s = self.s
        h, w = s.maat()
        rechts = RECHTS if self.app.inst.avatar else 0
        links = w - rechts  # tot hier: reeks, vraag, tip, spiekbrief en klad
        bezig = goed is None
        groot = h >= GROOT_H
        ry = self.teken_reeks(links, groot, ses, nr, resultaten, vrij, goed)
        # het vak Vraag zo breed als nodig; wat overblijft (genoeg?) is voor het klad
        vraag = ruim(v.tekst)
        meter = Meter()
        obj.teken(InVak(meter, VERSCHUIF[v.invoer], 0, 10 ** 4), 5, goed, tip)
        vb = max(meter.rechts + 3, len(vraag) + 6, 36)
        if links - vb < KLAD_MIN:
            vb = links
        vb = max(vb, links - KLAD_MAX)
        tw = vb - 6
        pw = 1 if getattr(obj, "toont_plaatswaarden", lambda: False)() else 0
        vy = ry + 1 + groot           # de vraag, op een band (op een groot scherm 3 rijen hoog)
        oy = vy + 2 + groot + pw      # het object
        onder = oy + obj.hoogte(not bezig)  # de eerste rij onder het object: daar komt de rand (of de melding)
        mel = regels(obj.melding, tw)[:2] if bezig and obj.melding else []
        tekst_hint = obj.hint.replace("Tab = volgende rij", "↓ = volgende rij") if vb < links else obj.hint
        hint = hint_regels(tekst_hint, tw)[:2] if bezig else []
        while hint and onder + 1 + max(1, len(mel)) + len(hint) + 3 > h - 1:  # het vak Tip heeft 3 rijen nodig
            hint.pop()
        if bezig:  # een lege rij onder het object, dan de melding en de hint
            onder += 1
            for i, stuk in enumerate(mel):
                s.put(onder + i, 3, stuk, obj.melding_rol)
            for i, stuk in enumerate(hint):
                s.put(onder + max(1, len(mel)) + i, 3, stuk, "dim")
            onder += max(1, len(mel)) + len(hint)
        titel = (f"Vrij oefenen: {self.vrij_goed + bool(goed)} van {self.vrij_aantal + (goed is not None)} juist"
                 if vrij else f"Vraag {nr + 1} van {self.totaal}")
        niveau = soort.split(" · ")[-1]  # het onderwerp staat al in de broodkruimel
        if len(niveau) + len(titel) + 14 > vb:
            niveau = niveau.split(" (")[0]
        richting = getattr(obj, "links", None)
        onder_label = (("typrichting ←" if richting else "typrichting →") if richting is not None else
                       STAPPEN if v.invoer == "staart" else "")
        vak.teken(s, ry, 0, onder - ry + 1, vb, titel, niveau, onder_label if bezig else "",
                  ord("r") if bezig and richting is not None else None)
        for r in range(vy - groot, vy + groot + 1):  # de band: één spatie van de rand
            s.put(r, 2, " " * (vb - 4), "b_band")
        s.put(vy, 4, vraag[:vb - 8], "b_vraag")
        obj.teken(InVak(s, VERSCHUIF[v.invoer], 2, vb - 2, RUSTIG), oy, goed, tip)
        # het klad: een kolom van de vraag tot onderaan
        self.kb_plek, plek = None, None
        if vb < links:
            kx, kw, kh = vb, links - vb, h - 1 - ry
            actief = bezig and self.focus == KLAD
            vak.teken(s, ry, kx, kh, kw, "▸ Klad" if actief else "Klad", "",
                      ("Tab = naar de som" if actief else "Tab") if bezig else "", TAB)
            self.kb_plek = (kx + 2, kh, kw - 4)
            plek = self.kb.teken(s, ry + 1, kx + 2, kw - 4, max(1, kh - 4), actief, ("focus", KLAD) if bezig else None)
            if actief and self.kb.melding:
                for i, stuk in enumerate(regels(self.kb.melding, kw - 4)[:2]):
                    s.put(ry + kh - 3 + i, kx + 2, stuk, self.kb.melding_rol or "dim")
        # eronder: de tip tijdens het rekenen, de uitleg na het nakijken
        ty = onder + 1
        th = min(h - 1 - ty, TIP_H if bezig else UITLEG_H)
        if not spiek:  # geen spiekbrief (een examen): een groot scherm krijgt geen groot leeg vak
            th = min(h - 1 - ty, 8 if bezig else UITLEG_H)
        elif h - 1 - ty - th < SPIEK_MIN:  # te weinig plaats: de tip krijgt 3 rijen, de spiekbrief de rest
            th = max(3, h - 1 - ty - SPIEK_MIN) if h - 1 - ty >= 3 + SPIEK_MIN else h - 1 - ty
        if bezig:
            vak.teken(s, ty, 0, th, vb, "Tip", "", "F1" if self.hulp.tips else "", HULP)
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
            vak.teken(s, ty, 0, th, vb, "Goed!" if goed else "Wat ging er mis?" if rol == "fout" else "Uitleg")
            uit = [(stuk, rol) for stuk in regels(kop, tw)] + [("", "")]
            for regel in uitleg:
                tekst, r = regel if isinstance(regel, tuple) else (regel, "accent")
                uit += [(stuk, r) for stuk in regels(tekst, tw, "  " if r == "" else "")]
            plaats = th - 2
            if len(uit) > plaats:
                uit = uit[:plaats - 1] + [("…", "dim")]
            for i, (stuk, r) in enumerate(uit):
                s.put(ty + 1 + i, 3, stuk, r)
        sy = ty + th
        self.spiek_zicht = None
        if spiek and h - 1 - sy >= SPIEK_MIN:  # de spiekbrief, altijd open (de vader, 22/11); in een examen niet
            self.teken_spiek(o, v, sy, h - 1 - sy, vb)
        if rechts:
            self.teken_maatje(links, h, goed, tip, gezicht, ballon, spring)
        if plek and bezig and self.focus == KLAD:
            s.cursor(True, *plek)
        elif bezig and obj.cursor_pos:
            y, x = obj.cursor_pos
            s.cursor(True, y, x + VERSCHUIF[v.invoer])
        else:
            s.cursor(False)

    def teken_reeks(self, breed, groot, ses, nr, resultaten, vrij, goed):
        """Bovenaan, onder de broodkruimel: hoe ver je bent. Op een groot scherm in een vak, anders één regel.
        Geeft de eerste vrije rij."""
        s = self.s
        if vrij:
            delen = [f"juist {self.vrij_goed + bool(goed)} van {self.vrij_aantal + (goed is not None)}"]
            bolletjes = []
        else:
            bolletjes = []
            for i in range(self.totaal):
                if i < len(resultaten) or (i == nr and goed is not None):
                    bolletjes.append(("✔", "goed") if (resultaten[i]["goed"] if i < len(resultaten) else goed)
                                     else ("✘", "fout"))
                else:
                    bolletjes.append(("◉", "accent") if i == nr else ("○", "dim"))
            juist, gedaan = sum(r["goed"] for r in resultaten) + bool(goed), len(resultaten) + (goed is not None)
            delen = [f"vraag {nr + 1} van {self.totaal}"] + ([f"juist {juist} van {gedaan}"] if gedaan else [])
        if ses.met_punten:
            delen.append(f"punten +{ses.punten}")
        if ses.op_rij >= 2:
            delen.append(f"{ses.op_rij} op rij")
        y = 2 if groot else 1
        x = 3 if groot else 1
        if groot:
            vak.teken(s, 1, 0, 3, breed, "Vrij oefenen" if vrij else "Reeks")
        else:
            s.put(y, x, "Vrij oefenen" if vrij else "Reeks", "accent")
            x += 8 if not vrij else 14
        for i, (ch, r) in enumerate(bolletjes[:20]):
            s.put(y, x + i, ch, r)
        x += len(bolletjes[:20]) + (3 if bolletjes else 0)
        s.put(y, x, "  ·  ".join(delen)[:max(0, breed - x - 2)], "dim")
        return 4 if groot else 2

    def teken_spiek(self, o, v, y, h, breed):
        """De spiekbrief in een vak, met het stuk van deze vraag in het licht (de rest gedimd). Past ze niet: PgUp,
        PgDn of het scrollwiel."""
        s = self.s
        kop = o.kop_op_spiekbrief(v)
        brief, i_kop = [], None  # de regels, gebroken op de breedte van het vak (met dezelfde inspringing)
        for tekst, r in o.spiekbrief():
            if tekst == kop:
                i_kop = len(brief)
            inspring = " " * (len(tekst) - len(tekst.lstrip()))
            brief += [(stuk, r) for stuk in (textwrap.wrap(tekst, breed - 6, initial_indent="",
                                                           subsequent_indent=inspring + "  ") if tekst.strip()
                                             else [""])]
        plaats = h - 2
        top = self.spiek_top if self.spiek_top is not None else (i_kop or 0)
        top = max(0, min(len(brief) - plaats, top))
        meer = len(brief) > plaats
        vak.teken(s, y, 0, h, breed, "Spiekbrief", o.naam,
                  f"{'▲' if top else ' '}{'▼' if top + plaats < len(brief) else ' '} PgUp PgDn" if meer else "")
        if meer:
            self.spiek_zicht = (top, plaats, len(brief))
            s.zones.voeg(y + h - 1, breed - 13, 1, 4, curses.KEY_PPAGE)  # "PgUp" en "PgDn" in de rand
            s.zones.voeg(y + h - 1, breed - 8, 1, 4, curses.KEY_NPAGE)
        stuk = False
        for i, (tekst, r) in enumerate(brief):
            if i_kop is not None:  # het stuk van de vraag: van het kopje tot de volgende lege regel
                stuk = i >= i_kop and (stuk or i == i_kop) and not (i > i_kop and not tekst.strip())
            if top <= i < top + plaats:
                voor = "▸ " if i == i_kop else "  "
                s.put(y + 1 + i - top, 2, (voor + tekst)[:breed - 4],
                      (r or "") if stuk or i_kop is None else "dim")

    def teken_maatje(self, x, h, goed, tip, gezicht, ballon, spring):
        """De rechterkolom: het maatje, van boven tot onder."""
        s = self.s
        vak.teken(s, 1, x, h - 2, RECHTS, "Maatje")
        uitdrukking = "denken" if tip and goed is None else gezicht
        if AV.kan_pixels(s):
            AV.teken(s, 2 - spring, x + 2, self.app.avatar_config(), uitdrukking)
        else:
            s.put(5, x + 2, A.TEKSTGEZICHT.get(uitdrukking, A.TEKSTGEZICHT["normaal"]), "accent")
        if ballon:
            for i, stuk in enumerate(regels(ballon, RECHTS - 4)[:3]):
                s.put(MAATJE_H - 1 + i, x + 2, stuk, "accent")
