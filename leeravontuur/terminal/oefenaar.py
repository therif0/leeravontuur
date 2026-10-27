"""Het algemene oefenscherm voor onderwerpen uit kern/onderwerp.py (vraag → antwoord).

Vrij oefenen, reeks van 10 met rapport, fouten opnieuw, gelijkaardige vragen, herhaalbak, spiekbrief,
punten en het oefenmaatje: voor elk onderwerp hetzelfde.
"""

import curses
import random
import textwrap
from decimal import Decimal

from ..kern import avatar as A
from ..kern import herhaling, leerjaren, selectie
from ..kern import punten as P
from ..kern.getal import fmt
from ..kern.klad import analyseer
from ..kern.modellen import Getallenlijn
from ..kern.wiskunde.grootheden import klok_cijfers
from . import digitaal as DG
from . import maatje
from . import modellen as M
from . import balk as B
from . import rooster as R
from . import vraagstuk as VI
from .kladblad import LEEG_ENTER, Kladblad
from .scherm import ENTER, ESC, teken_van, wil_stoppen

REEKS = 10
LOF = ["Goed zo!", "Super!", "Knap gedaan!", "Prima!", "Helemaal juist!", "Top!"]
HINTS = {"getal": "Kommagetal? Gebruik een komma: 0,25. Negatief? Typ een min: -5",
         "janee": "Typ ja of nee en druk Enter.",
         "lijn": "Pijl ▼ op het juiste streepje en Enter. Ligt het ertussen? Zoom in met +",
         "breuk": "Typ een breuk met /: 3/4 · een gemengd getal met een spatie: 1 3/4",
         "vergelijk": "Typ < (kleiner dan), > (groter dan) of = (gelijk aan) en druk Enter.",
         "duur": "Typ uren en minuten, bv. 2 u 15 min (of 2u15).",
         "klok": "Typ zoals altijd: 11.15 of 1115 (de : komt vanzelf). Backspace = terug.",
         "woord": "Typ scherp, recht, stomp, gestrekt of vol en druk Enter.",
         "plek": "Eerst de letter (of x), dan het getal (of y): bv. C4 of (3, −2).",
         "klokwoord": "Typ in woorden, bv. kwart over drie of vijf voor half vier."}
ONLEESBAAR = {"janee": "Typ ja of nee.", "breuk": "Typ een breuk, bv. 3/4 (of 1 3/4).",
              "vergelijk": "Typ <, > of =.",
              "duur": "Typ uren en minuten, bv. 2 u 15 min. Minuten: hoogstens 59.",
              "klok": "Typ een tijdstip, bv. 11.15 u. Minuten: hoogstens 59.",
              "woord": "Typ scherp, recht, stomp, gestrekt of vol.",
              "plek": "Typ bv. C4 (of (3, −2) in een assenstelsel).",
              "klokwoord": "Typ bv. kwart over drie, half vier of vijf voor half vier."}
VAK = {"klokwoord": 22}  # breedte van het antwoordvak (standaard 12)
LINKS = 60  # met een klokvenster blijft de tekst links van deze kolom (het venster is hoogstens een kwart breed)
INVOER = {**R.INVOER, **B.INVOER, **VI.INVOER}  # invoersoorten met een eigen invoer-object
# de vaste werkwijze: geen tweede kans waar raden te makkelijk is, of waar het object zelf stap voor stap nakijkt
GEEN_TWEEDE_KANS = {"janee", "vergelijk", "keuze", "rooster", "staart", "vraagstuk", "speur"}
TAB, KLAD, ANTWOORD = 9, "klad", "antwoord"
KLAD_BREED, KLAD_HOOG = 54, 6
KLAD_HINT = "Rekenregel + Enter (bv. 70 : 7 = 10) · lege regel of Tab = antwoord"
MEER_HULP = " Nog hulp nodig? Druk nog eens ?/F1: je spiekbrief."  # na de laatste tip (#20)
KORT_HULP = " Nog eens ?/F1: je spiekbrief."  # na de hulp van een invoer-object


def vraagtekst(v):
    """De vraag zoals in het rapport ('7 × 8 = ?'; een vraagstuk eindigt zelf al op een vraagteken)."""
    return v.tekst if v.tekst.endswith("?") else v.tekst + " ?"


class Oefenaar:
    def __init__(self, app, kruimel, onderwerpen, domein):
        self.app = app
        self.s = app.s
        self.kruimel = list(kruimel)   # tot en met de naam van het domein
        self.onderwerpen = list(onderwerpen)
        self.domein = domein
        self.totaal = REEKS
        self.verdiend = 0
        self.vrij_goed = self.vrij_aantal = 0
        self.laatste_d = None
        self.herkansing = False  # het laatste antwoord was pas juist na een tweede kans (telt als fout om te herhalen)

    # ---- niveau en start ------------------------------------------------------------

    def kies_niveau(self, kr, o):
        """Hoe moeilijk? Een niveau waarvan het leerjaar het onderwerp nog niet kent (bv. Snelheid pas vanaf het
        6de), kan niet: de keuze start dan op het dichtste niveau dat wel kan, en kiezen zegt waarom (#27)."""
        eigen = self.app.inst.leerjaar
        jaren = [leerjaren.leerjaar_voor_niveau(eigen, i) for i in range(len(leerjaren.NIVEAUS))]
        kan = [o.aangeboden(j) for j in jaren]
        vanaf = next((j for j in leerjaren.LEERJAREN if o.aangeboden(j)), None)
        opties = [(naam, leerjaren.NAMEN[j] + ("" if kan[i] else f"  (pas vanaf het {leerjaren.NAMEN[vanaf]})"))
                  for i, ((naam, _), j) in enumerate(zip(leerjaren.NIVEAUS, jaren))]
        start = min((i for i in range(len(kan)) if kan[i]), key=lambda i: (abs(i - 1), -i), default=1)
        info = [f"Jouw leerjaar: {leerjaren.NAMEN[eigen]}"]
        while True:
            k = self.s.menu(kr, "Hoe moeilijk?", opties, start=start, info=info)
            if k is None or kan[k] or not any(kan):
                return k
            info = info[:1] + ["", f"Dit oefen je pas vanaf het {leerjaren.NAMEN[vanaf]}. "
                                   f"Kies {leerjaren.NIVEAUS[start][0]}."]

    def start(self, o, vorm, niveau):
        jaar = leerjaren.leerjaar_voor_niveau(self.app.inst.leerjaar, niveau)
        soort = f"{o.naam} · {leerjaren.NIVEAUS[niveau][0]} ({leerjaren.NAMEN[jaar]})"
        if vorm == "vrij":
            self.vrij_oefenen(o, jaar, soort)
        else:
            self.reeks(o, jaar, soort)

    def spiekbrief(self, kr, o, v=None):
        """De spiekbrief. Met een vraag v (vanuit de oefening, #20): bij het kopje van die vraag, en Esc = terug naar
        de vraag."""
        regels = []
        for x in (o if isinstance(o, (list, tuple)) else [o]):  # een domein kan meer spiekbrieven hebben
            regels += ([("", "")] if regels else []) + (x.spiekbrief() or [(x.naam, "accent"), ("", ""),
                                                                            (x.omschrijving, "")])
        self.s.lezer(kr, regels, [("Esc", "terug naar je vraag" if v else "terug", ("terug",))],
                     {k: None for k in (ESC, ord("q"), *ENTER, ("terug",))},
                     begin=o.kop_op_spiekbrief(v) if v is not None else None)

    # ---- één vraag ------------------------------------------------------------------

    def voortgang(self, y, nr, resultaten, soort):
        s = self.s
        s.put(y, 4, f"Vraag {nr + 1} van {self.totaal}", "bold")
        for i in range(min(self.totaal, 10)):
            if i < len(resultaten):
                ch, rol = "●", "goed" if resultaten[i]["goed"] else "fout"
            else:
                ch, rol = ("◉", "accent") if i == nr else ("○", "dim")
            s.put(y, 22 + 2 * i, ch, rol)
        s.put(y, 46, f"Punten: {sum(r['goed'] for r in resultaten)}", "bold")
        s.put(y + 1, 4, soort, "dim")

    def stel_vraag(self, kr, o, v, soort, ses, nr=None, resultaten=None, vrij=False):
        """Eén vraag volgens de vaste werkwijze: lees, reken in het klad (Tab), antwoord. ? = de volgende tip,
        fout = één tweede kans. Geeft (getypt antwoord, goed?, stoppen?) of None bij Esc."""
        s = self.s
        buf, melding, melding_rol, goed, tip = "", "", "fout", None, False
        tip_gebruikt, extra, getal, d = False, "", None, None
        gezicht, ballon, spring = "normaal", "", False
        lijnen, cursor = ([v.model], 0) if v.invoer == "lijn" else (None, None)  # aanduiden: zoomstapel + pijl
        obj = INVOER[v.invoer](v, o) if v.invoer in INVOER else None          # rooster, staartdeling, balk …
        if hasattr(obj, "plaatswaarden"):  # het rooster: de keuze van het kind (#18)
            obj.plaatswaarden = self.app.inst.plaatswaarden
        digi = v.invoer == "klok"  # een tijdstip typ je op een digitaal klokje (#21)
        eigen = bool(obj and getattr(obj, "eigen_tekst", False))  # het object tekent zelf de vraag (vraagstuk)
        # de vaste werkwijze: klad (bij een gewoon antwoordvak), getrapte tips, een tweede kans
        kb = Kladblad() if not obj and not lijnen and o.klad_voor(v) else None
        verplicht = kb is not None and o.klad_voor(v) == "verplicht"
        focus = KLAD if verplicht else ANTWOORD
        tips, tip_nr, tiptekst = (o.tips(v) if not obj else []), 0, ""
        # na de laatste tip: de spiekbrief (#20); daarna begint het weer bij tip 1
        spiek = bool(o.spiekbrief())
        periode = max(1, len(tips) + (kb is not None)) + spiek
        laatste_hulp = None  # bij een invoer-object: nog eens ? op dezelfde plek = de spiekbrief
        tweede = v.invoer not in GEEN_TWEEDE_KANS
        eerste_fout, kans_melding, klad_ok, analyse = None, "", False, None
        self.herkansing = False
        ses.vraag_getoond()
        lof = random.choice(LOF)
        while True:
            if s.te_klein():
                continue
            tip_knop = "spiekbrief" if spiek and tip_nr % periode == periode - 1 else "tip"
            if goed is not None:
                laatste = not vrij and nr == self.totaal - 1
                knoppen = [("Enter", "naar je resultaat" if laatste else "volgende vraag", 10),
                           ("Esc", "stoppen", ESC)]
            elif obj:
                knoppen = obj.knoppen()
            elif lijnen:
                knoppen = [("←→", "pijl", None), ("+", "zoom in", ord("+")), ("−", "zoom uit", ord("-")),
                           ("Enter", "hier!", 10), ("?/F1", tip_knop, ord("?")), ("Esc", "stoppen", ESC)]
            else:
                knoppen = ([("Tab", "naar je antwoord" if focus == KLAD else "naar het klad", TAB)] if kb else []) + [
                    ("Enter", "regel nakijken" if focus == KLAD else "controleren", 10), ("?/F1", tip_knop, ord("?")),
                    ("Esc", "stoppen", ESC)]
            s.nieuw(kr, knoppen)
            if vrij:
                s.put(2, 4, f"Vrij oefenen: {self.vrij_goed + bool(goed)} van "
                            f"{self.vrij_aantal + (goed is not None)} juist", "bold")
                s.put(3, 4, soort, "dim")
            else:
                self.voortgang(2, nr, resultaten, soort)
            y, x = 6, 6
            vy, vx = y, x + len(v.tekst) + 2  # waar het antwoordvak staat
            onder = y + 1  # de eerste vrije rij onder de vraag
            if eigen:
                pass
            elif lijnen or obj or (len(v.tekst) <= 54 if digi else
                                   vx + VAK.get(v.invoer, 12) + 2 + len(v.eenheid) <= 62):  # past (links van het maatje)
                s.put(y, x, v.tekst + "  ", "bold")
            else:  # lange vraag: over meer regels, het antwoordvak eronder
                regels = textwrap.wrap(v.tekst, 54)
                for i, regel in enumerate(regels):
                    s.put(y - 1 + i, x, regel, "bold")
                vy, vx = y - 1 + len(regels), x
                onder = vy
            if not lijnen and not obj and not digi:
                rol = ("veld" if focus == ANTWOORD else "dim") if goed is None else ("goedvak" if goed else "foutvak")
                s.tekstvak(vy, vx, buf, VAK.get(v.invoer, 12), rol, ("focus", ANTWOORD) if kb and goed is None else None)
                if v.eenheid:
                    s.put(vy, vx + 15, v.eenheid, "bold")
            fb, fx, breed = y + 3, x, 70  # waar de feedback begint (rij, kolom) en hoe breed ze mag zijn
            hint_y = None
            hoog = False  # een hoog model: de feedback (en het klad) komen ernaast
            model_h = 0
            if eigen:
                obj.teken(s, 4, goed, tip)
                fb, fx = 4 + obj.hoogte(goed is not None), 4
                hint_y = min(fb + 2, s.maat()[0] - 2)
                melding = obj.melding
            elif obj:
                obj.teken(s, 8, goed, tip)
                if getattr(obj, "naast", None):  # hoog invoer-object: de feedback komt ernaast
                    fb, fx = obj.naast
                    breed, hint_y = 78 - fx, min(9 + obj.hoogte() + 1, s.maat()[0] - 2)
                else:
                    fb = 8 + obj.hoogte(goed is not None) + 1
                melding, melding_rol = kans_melding or obj.melding, "fout" if kans_melding else obj.melding_rol
            elif lijnen:
                lijn = lijnen[-1]
                fout_bij = v.antwoord if goed is False else None
                M.teken_getallenlijn(s, 9, lijn, cursor, "cursor" if goed is None else ("goed" if goed else "fout"),
                                     fout_bij, (lambda i: ("lijn", i)) if goed is None else None)
                if len(lijnen) > 1:
                    s.put(8, 4, f"Ingezoomd ({len(lijnen) - 1}×): tussen {fmt(lijn.van)} en {fmt(lijn.tot)}", "info")
                fb = 14
            elif (model := v.model if goed is None else (v.model_na or v.model)) is not None:
                if isinstance(model, Getallenlijn):
                    M.teken_getallenlijn(s, 9, model, goed_bij=v.antwoord if goed is False else None)
                    fb = 14
                else:
                    h, b = M.teken_model(s, 9, model, uitslag=goed, tekst=v.tekst)  # rij 9: onder het maatje
                    model_h = h
                    if h > 7:  # hoog model: de feedback komt ernaast
                        fb, fx, hoog = 10, 8 + b + 3, True
                        breed, hint_y = 78 - fx, min(9 + h + 1, s.maat()[0] - 2)
                    else:
                        fb = max(fb, 9 + h + 1)
            if digi:  # het digitale klokje: onder de vraag, of naast een hoog model (de klok in de terminal)
                dy, dx = (9, fx) if hoog else (9 + model_h + 1 if model_h else onder + 1, x + 2)
                DG.teken(s, dy, dx, klok_cijfers(buf), "bold" if goed is None else ("goed" if goed else "fout"),
                         "accent" if goed is None and focus == ANTWOORD else "dim",
                         ("focus", ANTWOORD) if kb and goed is None else None, compact=hoog)
                fb = dy + DG.COMPACT_H if hoog else max(fb, dy + DG.HOOGTE + 1)
            if s.klokvenster is not None and s.klokvenster.toont():  # het klokvenster staat rechts: tekst links
                breed = min(breed, LINKS - fx)
            if kb and goed is None:  # het klad: onder het antwoord, of naast een hoog model
                kx, kw = (fx, min(KLAD_BREED, 78 - fx)) if hoog else (x, min(KLAD_BREED, breed))
                ky = fb + 1 if hoog else max(vy + 2, fb)
                kh = max(2, min(KLAD_HOOG, s.maat()[0] - 2 - ky - 4))
                label = "▸ Klad" if focus == KLAD else "Klad (Tab)"
                s.put(ky - 1, kx, label, "accent" if focus == KLAD else "dim")
                s.zones.voeg(ky - 1, kx, 1, len(label), ("focus", KLAD))
                plek = kb.teken(s, ky, kx, kw, kh, focus == KLAD, ("focus", KLAD))
                fb = ky + kh + 1
            maatje.teken(self.app, "denken" if tip and goed is None else gezicht, ballon, ruim=True, hoog=spring)
            if goed is None:
                if eigen:  # de melding mag over 3 regels (dan valt de hint weg)
                    stukken = textwrap.wrap(melding, 74)[:3]
                    for i, stuk in enumerate(stukken):
                        s.put(fb + i, fx, stuk, obj.melding_rol)
                    if len(stukken) > 2:
                        hint_y = s.maat()[0]  # buiten het scherm
                else:
                    for i, stuk in enumerate(textwrap.wrap(melding, breed)[:2]):
                        s.put(fb + i, fx, stuk, melding_rol)
                if tip and not eigen:
                    tekst = ("Hulp: " + obj.hulp(o)) if obj else tiptekst
                    tw = min(breed, 70 if lijnen or obj else 54)  # naast een hoog object is er plaats voor 4 regels
                    tn = (4 if getattr(obj, "naast", None) else 2) if obj else 3
                    if tekst.endswith(MEER_HULP):  # de wenk naar de spiekbrief alleen als hij helemaal past
                        tekst = tekst[:-len(MEER_HULP)]
                    if spiek and (obj or tip_knop == "spiekbrief") and \
                            len(textwrap.wrap(tekst + (KORT_HULP if obj else MEER_HULP), tw)) <= tn:
                        tekst += KORT_HULP if obj else MEER_HULP
                    van = fb + (2 if len(melding) > breed else 1) if obj or melding else fb
                    for i, stuk in enumerate(textwrap.wrap(tekst, tw)[:tn]):
                        s.put(van + i, fx, stuk, "accent")
                hint = (obj.hint if obj else KLAD_HINT if kb and focus == KLAD else
                        HINTS.get(v.invoer, HINTS["getal"]))
                s.put(hint_y or min(fb + 3, s.maat()[0] - 2), x, hint, "dim")
                if obj and obj.cursor_pos:
                    s.cursor(True, *obj.cursor_pos)
                elif lijnen or obj:
                    s.cursor(False)
                elif focus == KLAD and plek:
                    s.cursor(True, *plek)
                elif digi:
                    s.cursor(False)
                else:
                    s.cursor(True, vy, vx + 1 + len(buf))
            else:
                s.cursor(False)
                if eigen:
                    kop, rol = (("✔ " + lof + extra, "goed") if goed else
                                (f"✘ Niet juist. Het juiste antwoord is {v.verwacht}.{extra}", "fout"))
                    uitleg = ([] if goed or not d else [d[1]]) + (obj.uitleg_na if goed is False or vrij else
                                                                 obj.uitleg_na[:1])
                elif goed:
                    kop, rol = "✔ " + lof + extra, "goed"
                    uitleg = (["Je klad is helemaal juist. Netjes gewerkt!"] if klad_ok else []) + (
                        self.uitwerking(o, v) if vrij else [])
                elif obj and obj.fouten and getal == v.antwoord:
                    kop, rol = f"! De uitkomst klopt, maar onderweg ging het {obj.fouten} keer mis.{extra}", "accent"
                    uitleg = ([d[1]] if d else []) + o.uitleg(v)
                else:
                    kop, rol = f"✘ Niet juist. Het juiste antwoord is {v.verwacht}.{extra}", "fout"
                    eerste_klad = analyse["eerste"] if analyse else None
                    in_klad = ([] if not eerste_klad else
                               [f"Dat zie je in je klad, regel {eerste_klad[0]} (!)."] if d and eerste_klad[1] == d[0] else
                               [f"In je klad: {eerste_klad[2]}"])
                    uitleg = ([d[1]] if d else []) + in_klad + self.uitwerking(o, v)
                # het klad blijft staan (#22): rechtsonder naast de uitleg, of eronder als rechts geen plaats is
                n = min(3, len(kb.regels)) if kb and not eigen else 0
                naast = n and not hoog and not (s.klokvenster is not None and s.klokvenster.toont())
                kw = 38 if naast else min(38, 78 - fx)
                kader = (s.maat()[0] - 4 - n, 78 - kw) if naast else None

                def stukken(tekst, y, inspring=""):  # tekst die tot naast het kader komt, stopt ervoor
                    uit = textwrap.wrap(tekst, breed, subsequent_indent=inspring)
                    if kader and y + len(uit) > kader[0]:
                        uit = textwrap.wrap(tekst, min(breed, kader[1] - fx - 2), subsequent_indent=inspring)
                    return uit
                yy = fb
                for stuk in stukken(kop, yy):
                    s.put(yy, fx, stuk, rol)
                    yy += 1
                yy += 1
                for regel in uitleg:
                    tekst, rol = regel if isinstance(regel, tuple) else (regel, "accent")
                    for stuk in stukken(tekst, yy, "  " if rol == "" else ""):
                        if yy < s.maat()[0] - 1:
                            s.put(yy, fx, stuk, rol)
                        yy += 1
                status = analyse["status"] if analyse else None
                if kader:
                    kb.teken_kader(s, *kader, kw, n, status)
                elif n and yy + n + 2 <= s.maat()[0] - 2:
                    kb.teken_kader(s, yy + 1, fx, kw, n, status)
            if spring:
                s.pauze(170)
                spring = False
                continue
            k = s.toets()
            if k == curses.KEY_F1:  # F1 = ? (op een AZERTY-klavier is ? Shift + komma, #14)
                k = ord("?")
            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return buf, goed, False
                if k == ESC:
                    return buf, goed, True
                continue
            if k == ESC:  # midden in een vraag: eerst vragen of het kind echt wil stoppen (#33)
                if not wil_stoppen(s, ses):
                    continue
                s.cursor(False)
                return None
            eigen_tip = obj is not None and getattr(obj, "eigen_tip", False)
            if k == ord("?") and (not eigen_tip or (spiek and getattr(obj, "tips_op", False))):  # ook in het klad
                tip = tip_gebruikt = True
                if eigen_tip:  # het object gaf al zijn tips: nu de spiekbrief
                    getattr(obj, "spiekbrief_bekeken", lambda: None)()
                    self.spiekbrief(kr + ["Spiekbrief"], o, v)
                elif obj:
                    hulp = obj.hulp(o)
                    if spiek and hulp == laatste_hulp:
                        laatste_hulp, tip = None, False
                        self.spiekbrief(kr + ["Spiekbrief"], o, v)
                    else:
                        laatste_hulp = hulp
                else:
                    tip_nr += 1
                    tiptekst = self.volgende_tip(o, v, tips, tip_nr, kb, spiek)
                    if tiptekst is None:
                        tip = False
                        self.spiekbrief(kr + ["Spiekbrief"], o, v)
                continue
            if kb and isinstance(k, tuple) and k[0] in ("focus", "klad"):  # een klik op het klad of het antwoord
                if k[0] == "klad":
                    focus = KLAD
                    kb.haal_terug(k[1])
                else:
                    focus = k[1]
                if focus != KLAD:
                    kb.rond_af()
                continue
            if kb and k == TAB:
                melding = ""
                if focus == KLAD:  # een regel zonder Enter verdwijnt niet: eerst nakijken (#22)
                    kb.melding = ""
                    kb.rond_af()
                    melding, melding_rol = kb.melding, kb.melding_rol or "fout"
                focus = ANTWOORD if focus == KLAD else KLAD
                continue
            if kb and focus == KLAD:
                kb.melding = ""
                if kb.toets(k, teken_van(k), KLAD_BREED) == LEEG_ENTER:
                    focus = ANTWOORD
                melding, melding_rol = kb.melding, kb.melding_rol or "fout"
                continue
            if obj:
                uit = obj.toets(k)
                if getattr(obj, "plaatswaarden", None) not in (None, self.app.inst.plaatswaarden):
                    self.app.inst.plaatswaarden = obj.plaatswaarden  # p: onthouden voor dit kind
                    self.app.bewaar()
                if uit is None:
                    kans_melding = ""
                    continue
                buf, getal = uit
            elif lijnen:
                cursor, klaar = self.lijn_toets(lijnen, cursor, k, v)
                if not klaar:
                    continue
                buf = fmt(lijnen[-1].streepjes()[cursor])
                getal = o.lees_vraag(v, buf)
            elif k not in ENTER:
                if digi and (ch := teken_van(k)) is not None and klok_cijfers(buf + ch) is None:
                    continue  # het klokje neemt alleen wat een tijdstip kan worden
                buf = s.bewerk(buf, k, VAK.get(v.invoer, 12))
                melding = ""
                continue
            else:
                getal = o.lees_vraag(v, buf)
            if verplicht and getal is not None:  # eerst het klad: zien hoe het kind het aanpakt
                ok, nodig = o.klad_klaar(v, kb.gelezen)
                if not ok:
                    melding, melding_rol, focus = nodig, "accent", KLAD
                    continue
            if getal is None:
                tip = False
                melding, melding_rol = ("Typ eerst je antwoord." if not buf.strip() else ONLEESBAAR.get(
                    v.invoer, "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25.")), "fout"
                continue
            goed = o.nakijken(v, getal) and not (obj and obj.fouten)
            d = (obj and (obj.diagnose or o.diagnose_rijen(v, obj.rijen()))) or o.diagnose(v, getal)
            opl = o.oplossing_of_niets(v) if kb else None
            if kb and kb.regels and opl:
                analyse = analyseer(opl.stappen, opl.paden, kb.gelezen)
                klad_ok = analyse["eerste"] is None and analyse["compleet"]
            if not goed and tweede and eerste_fout is None and not (obj and getattr(obj, "eigen_tip", False)):
                # de tweede kans: een hulpje (als de denkfout herkend is) en de vraag om klad te maken
                eerste_fout = buf.strip()
                hulp = d[1] if d else "Nog niet juist."
                if kb:
                    hulp += (" Maak eens klad (Tab): reken stap voor stap." if not kb.regels else
                             " Kijk je klad nog eens na." + (f" {analyse['eerste'][2]}" if analyse and
                                                             analyse["eerste"] else ""))
                else:
                    hulp += " Probeer nog eens."
                goed, d, getal = None, None, None
                if obj:
                    kans_melding = hulp
                else:
                    melding, melding_rol = hulp, "fout"
                    if not lijnen:
                        buf = ""
                gezicht, ballon = "denken", "Probeer nog eens!"
                continue
            extra_data = {"stapfouten": obj.fouten} if obj and obj.fouten else None
            if obj and getattr(obj, "extra", None):
                extra_data = {**(extra_data or {}), **obj.extra}
                tip_gebruikt = tip_gebruikt or bool(obj.extra.get("tips"))
                self.herkansing = obj.extra.get("eerste_fout") is not None
                if goed:
                    d = None
            elif not eigen:
                werkwijze = {"tips": tip_nr, "eerste_fout": eerste_fout}
                if kb:
                    werkwijze.update(klad=kb.teksten, klad_ok=klad_ok)
                extra_data = {**(extra_data or {}), **{k_: w for k_, w in werkwijze.items() if w not in (None, 0, [])}}
                self.herkansing = eerste_fout is not None
            self.laatste_d = d
            ses.antwoord(v.sleutel, vraagtekst(v), buf.strip(), goed, d[0] if d else None, hulp=tip_gebruikt,
                         extra=extra_data or None, verwacht=v.verwacht, vaardigheid=o.id, leerjaar=v.leerjaar)
            extra = self.tijd_tekst(ses) + (f"  +{ses.laatste_punten} punten" if ses.laatste_punten else "")
            gezicht, ballon = A.reactie(goed, ses.op_rij, d[0] if d else None)
            spring = goed and self.app.inst.animaties and self.app.inst.avatar

    @classmethod
    def volgende_tip(cls, o, v, tips, nr, kb, spiek=False):
        """Tip nr (vanaf 1): de vaste tips van het onderwerp (de aanpak, het begin van het klad), dan hulp bij het
        klad, dan (spiek) de spiekbrief (#20): dan geeft dit None. Daarna opnieuw van voren af aan (#15).
        Nooit het antwoord."""
        aantal = max(1, len(tips) + (kb is not None))
        i = (nr - 1) % (aantal + spiek) + 1
        if i > aantal:
            return None
        tekst = cls._tip(o, v, tips, i, aantal, kb)
        return tekst + MEER_HULP if spiek and i == aantal else tekst

    @staticmethod
    def _tip(o, v, tips, i, aantal, kb):
        if not tips and kb is None:
            return "Tip: lees de vraag nog eens rustig."
        kop = f"Tip {i} van {aantal}" if aantal > 1 else "Tip"
        if i <= len(tips):
            return f"{kop}: {tips[i - 1]}"
        opl = o.oplossing_of_niets(v)
        if not kb.regels:
            return f"{kop}: schrijf je eerste stap in het klad (Tab)."
        a = analyseer(opl.stappen, opl.paden, kb.gelezen) if opl else None
        if a and a["eerste"]:
            return f"{kop}: {a['eerste'][2]}"
        return f"{kop}: je klad ziet er goed uit. Reken verder, of vul je antwoord in (Tab)."

    @staticmethod
    def uitwerking(o, v):
        """Na het nakijken: "Zo kan het:" met de oplossing in klad-regels, en daaronder het waarom."""
        opl = o.oplossing_of_niets(v) if o.klad_voor(v) else None
        if not opl or not opl.stappen:
            return o.uitleg(v)
        regels = [("Zo kan het:", "bold")] + [("  " + st.reken, "") for st in opl.stappen]
        waarom = [st.waarom for st in opl.stappen if st.waarom]
        return regels + (waarom or o.uitleg(v)[:2])

    @staticmethod
    def lijn_toets(lijnen, cursor, k, v):
        """Een toets of klik op de getallenlijn. Geeft (nieuwe cursor, gekozen?). lijnen = zoomstapel."""
        lijn = lijnen[-1]
        laatste = len(lijn.streepjes()) - 1
        minste = Decimal(v.data.get("minste", "1"))
        if k == curses.KEY_LEFT:
            return max(0, cursor - 1), False
        if k == curses.KEY_RIGHT:
            return min(laatste, cursor + 1), False
        if k == ("scroll", -1):  # wiel omhoog = inzoomen, omlaag = uitzoomen (zoals op een kaart)
            k = ord("+")
        elif k == ("scroll", 1):
            k = ord("-")
        if isinstance(k, tuple) and k[0] == "lijn":
            return k[1], False
        if k in (ord("+"), ord("=")) and lijn.kan_inzoomen(minste):
            links = min(cursor, laatste - 1)
            lijnen.append(lijn.inzoomen(lijn.streepjes()[links]))
            return (0 if cursor == links else len(lijnen[-1].streepjes()) - 1), False
        if k in (ord("-"), ord("−")) and len(lijnen) > 1:
            weg = lijnen.pop()
            return lijnen[-1].streepjes().index(lijnen[-1].dichtst(weg.van)), False
        return cursor, k in ENTER

    def tijd_tekst(self, ses):
        if not self.app.inst.timer_zichtbaar:
            return ""
        return f"  ({round(ses.laatste_tijd_ms / 1000)} s)"

    # ---- reeksen ------------------------------------------------------------------------

    def verwerk(self, o, v, goed, item=None):
        opslag, kind = self.app.opslag, self.app.kind
        if item is not None:
            if goed:
                if herhaling.juist(opslag, item):
                    opslag.punten_bij(kind.id, P.BONUS_BEHEERST, "onderwerp beheerst in de herhaalbak")
            else:
                herhaling.fout(opslag, kind.id, item["vaardigheid"], item["onderwerp"], item["data"])
        elif not goed:
            herhaling.fout(opslag, kind.id, o.id, o.onderwerp(v), o.herhaal_data(v))

    def gewichten(self, o):
        recent = self.app.opslag.recente_antwoorden(self.app.kind.id, o.id, 100)
        onderwerpen = {o.onderwerp_van_sleutel(a["sleutel"]) for a in recent} - {None}
        return selectie.gewichten(recent, o.onderwerp_van_sleutel, onderwerpen) if onderwerpen else None

    def speel(self, kr, soort, modus, jaar, vragen, items=None, vaardigheid=None):
        """vragen = [(onderwerp, vraag)]. Geeft (resultaten, gestopt?)."""
        resultaten = []
        self.totaal = len(vragen)
        self.verdiend = 0
        with self.app.sessie(modus, vaardigheid or vragen[0][0].id, jaar) as ses:
            for nr, (o, v) in enumerate(vragen):
                uit = self.stel_vraag(kr, o, v, soort, ses, nr, resultaten)
                if uit is None:
                    return resultaten, True
                resultaten.append(dict(o=o, v=v, antw=uit[0], goed=uit[1], tijd=ses.laatste_tijd_ms,
                                       d=self.laatste_d))
                self.verwerk(o, v, uit[1] and not self.herkansing, items[nr] if items else None)
                if uit[-1]:
                    return resultaten, True
            if modus == "reeks" and len(vragen) == REEKS and all(r["goed"] for r in resultaten):
                ses.bonus(P.BONUS_PERFECT, "reeks van 10 zonder fout")
            self.verdiend = ses.punten
        return resultaten, False

    def nieuwe_vragen(self, o, jaar, aantal=REEKS):
        vermijd = selectie.recent_gezien(self.app.opslag, self.app.kind.id, o.id)
        gew = self.gewichten(o)
        uit = []
        for _ in range(aantal):
            v = o.maak(jaar, vermijd, gew)
            vermijd.add(v.sleutel)
            uit.append((o, v))
        return uit

    def reeks(self, o, jaar, soort):
        kr = self.kruimel + ([o.naam] if len(self.onderwerpen) > 1 else []) + ["Reeks van 10"]
        while True:
            res, gestopt = self.speel(kr, soort, "reeks", jaar, self.nieuwe_vragen(o, jaar))
            if gestopt or not self.na_reeks(kr, soort, jaar, res):
                return

    def na_reeks(self, kr, soort, jaar, res):
        while True:
            keuze = self.rapport(kr, soort, res)
            fouten = [r for r in res if not r["goed"]]
            if keuze == "fouten" and fouten:
                res, gestopt = self.speel(kr + ["Fouten opnieuw"], soort, "fouten_opnieuw", jaar,
                                          [(r["o"], r["v"]) for r in fouten])
            elif keuze == "gelijkaardig" and fouten:
                vermijd = {r["v"].sleutel for r in res}
                vragen = [(r["o"], r["o"].maak_herhaling(r["o"].herhaal_data(r["v"]), jaar, vermijd)) for r in fouten]
                res, gestopt = self.speel(kr + ["Gelijkaardige vragen"], soort, "gelijkaardig", jaar, vragen)
            else:
                return keuze == "nieuw"
            if gestopt:
                return False

    def rapport(self, kr, soort, resultaten):
        naam = self.app.inst.naam
        totaal = len(resultaten)
        goed = sum(r["goed"] for r in resultaten)
        if goed == totaal:
            bericht, rol = f"Perfect{', ' + naam if naam else ''}! Alles juist!", "goed"
        elif goed >= 0.8 * totaal:
            bericht, rol = "Heel goed gedaan!", "goed"
        elif goed >= 0.6 * totaal:
            bericht, rol = "Goed bezig! Lees de uitleg bij je fouten en probeer ze opnieuw.", "accent"
        else:
            bericht, rol = "Blijf oefenen, je kan het! Lees de uitleg hieronder rustig na.", "fout"
        n, j = self.app.vandaag()
        regels = [(f"Je score: {goed} / {totaal}", rol), (bericht, rol), (soort, "dim")]
        if self.verdiend:
            regels.append((f"★ Je verdiende {self.verdiend} punten. Je hebt er nu "
                           f"{self.app.opslag.punten_saldo(self.app.kind.id)}.", "accent"))
        if self.app.inst.timer_zichtbaar and totaal:
            regels.append((f"Gemiddeld {round(sum(r['tijd'] for r in resultaten) / totaal / 1000)} seconden "
                           "per vraag.", "info"))
        regels += [("", ""), (f"Vandaag in totaal: {j} van {n} juist.", "info"), ("", "")]
        fouten = [(i, r) for i, r in enumerate(resultaten) if not r["goed"]]
        if not fouten:
            regels.append(("Geen enkele fout. Proficiat!", "goed"))
        else:
            regels += [("Wat ging er mis? Lees de uitleg goed:", "accent"),
                       ("Met F probeer je dezelfde vragen opnieuw, met G gelijkaardige vragen.", "dim"), ("", "")]
        for i, r in fouten:
            o, v = r["o"], r["v"]
            regels.append((f"Vraag {i + 1}:  {vraagtekst(v)}", "bold"))
            regels.append((f"   ✘ Jij schreef: {r['antw'].strip()}    Juist is: {v.verwacht}", "fout"))
            d = r.get("d") or o.diagnose(v, o.lees_vraag(v, r["antw"]))
            if d:
                regels.append(("   " + d[1], "accent"))
            regels += [("   " + l, "") for l in o.uitleg(v)]
            regels.append(("", ""))
        toetsen = {ord("n"): "nieuw", ord("N"): "nieuw", ESC: "menu", ("nieuw",): "nieuw", ("menu",): "menu"}
        toetsen.update({k: "nieuw" for k in ENTER})
        knoppen = [("Enter", "nieuw", ("nieuw",))]
        if fouten:
            toetsen.update({ord("f"): "fouten", ord("F"): "fouten", ("fouten",): "fouten",
                            ord("g"): "gelijkaardig", ord("G"): "gelijkaardig", ("gelijk",): "gelijkaardig"})
            knoppen = [("F", "fouten opnieuw", ("fouten",)), ("G", "gelijkaardig", ("gelijk",))] + knoppen
        knoppen.append(("Esc", "menu", ("menu",)))
        return self.s.lezer(kr + ["Resultaat"], regels, knoppen, toetsen, scroll_uitleg="")

    def vrij_oefenen(self, o, jaar, soort):
        kr = self.kruimel + ([o.naam] if len(self.onderwerpen) > 1 else []) + ["Vrij oefenen"]
        self.vrij_goed = self.vrij_aantal = 0
        fouten = []
        vermijd = selectie.recent_gezien(self.app.opslag, self.app.kind.id, o.id)
        gew = self.gewichten(o)
        with self.app.sessie("vrij", o.id, jaar) as ses:
            while True:
                v = o.maak(jaar, vermijd, gew)
                vermijd.add(v.sleutel)
                uit = self.stel_vraag(kr, o, v, soort, ses, vrij=True)
                if uit is None:
                    break
                self.vrij_aantal += 1
                self.vrij_goed += uit[1]
                self.verwerk(o, v, uit[1] and not self.herkansing)
                if not uit[1]:
                    fouten.append(dict(o=o, v=v, antw=uit[0], goed=False, tijd=ses.laatste_tijd_ms))
                if uit[2]:
                    break
        if fouten:
            k = self.s.menu(kr, f"Je had {len(fouten)} {'fout' if len(fouten) == 1 else 'fouten'}. "
                                "Wil je ze nog eens proberen?",
                            [("Dezelfde vragen", "precies dezelfde vragen opnieuw"),
                             ("Gelijkaardige vragen", "dezelfde soort, met nieuwe getallen"), ("Nee, stoppen", "")])
            if k in (0, 1):
                vragen = ([(r["o"], r["v"]) for r in fouten] if k == 0 else
                          [(r["o"], r["o"].maak_herhaling(r["o"].herhaal_data(r["v"]), jaar, vermijd)) for r in fouten])
                res, gestopt = self.speel(kr + ["Fouten opnieuw"], soort, "fouten_opnieuw" if k == 0 else "gelijkaardig",
                                          jaar, vragen)
                if not gestopt:
                    self.na_reeks(kr, soort, jaar, res)

    def herhalen(self, kr, items, onderwerp_van):
        """Herhaalbak-items (met nieuwe getallen), op het eigen leerjaar."""
        jaar = self.app.inst.leerjaar
        vragen = []
        for i in items:
            o = onderwerp_van[i["vaardigheid"]]
            vragen.append((o, o.maak_herhaling(i["data"], jaar)))
        return self.speel(kr, "Herhalen", "herhaalbak", jaar, vragen, items)
