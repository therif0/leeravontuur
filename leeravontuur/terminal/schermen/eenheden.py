"""Schermen voor eenheden omzetten: vrij oefenen, reeks van 10, tabel-oefening en spiekbrief."""

import curses
import random
import textwrap

from ...kern import avatar as A
from ...kern import herhaling, leerjaren, selectie
from ...kern import punten as P
from .. import maatje
from ...kern.getal import fmt, lees_getal
from ...kern.wiskunde import eenheden as E
from ..scherm import BACKSPACE, ENTER, ESC

REEKS = 10
LOF = ["Goed zo!", "Super!", "Knap gedaan!", "Prima!", "Helemaal juist!", "Top!"]
TABEL_X, TABEL_Y = 12, 7


class Eenheden:
    def __init__(self, app, kruimel):
        self.app = app
        self.s = app.s
        self.kruimel = list(kruimel)  # tot en met het onderwerp (bv. Meten › Lengte (m))
        self.totaal = REEKS           # aantal vragen in de lopende reeks
        self.verdiend = 0             # punten in de laatste reeks

    # ---- keuzes --------------------------------------------------------

    def oefen(self, vorm, maat, kr):
        """Eén eenheden-oefening: vorm 'vrij', 'reeks' of 'tabel'; maat = een soort (E.SOORTEN), 'alles' of 'zelf'.
        Eerst (bij 'zelf') de eenheden aanduiden, dan het niveau. False als het kind onderweg terugging."""
        if maat == "zelf":
            gekozen = self.kies_zelf(kr)
            if gekozen is None:
                return False
            soort = "Zelf gekozen"
        elif maat == "alles":
            gekozen, soort = "alles", "Door elkaar"
        else:
            gekozen, soort = E.EENHEDEN[maat], E.NAMEN[maat]
        niveau = self.kies_niveau(kr)
        if niveau is None:
            return False
        self.app.onthoud_oefening({"onderwerp": "eenheden", "vorm": vorm, "eenheden": gekozen,
                                   "niveau": niveau, "soort": soort})
        gekozen, jaar, soort = self.keuze(gekozen, niveau, soort)
        if vorm == "vrij":
            self.vrij_oefenen(gekozen, jaar, soort)
        else:
            self.reeks(gekozen, jaar, soort, tabel=vorm == "tabel")
        return True

    def keuze(self, gekozen, niveau, soort):
        jaar = leerjaren.leerjaar_voor_niveau(self.app.inst.leerjaar, niveau)
        if gekozen == "alles":
            gekozen = E.eenheden_voor(jaar)
        return gekozen, jaar, f"{soort} · {leerjaren.NIVEAUS[niveau][0]} ({leerjaren.NAMEN[jaar]})"

    def kies_niveau(self, kr):
        eigen = self.app.inst.leerjaar
        opties = []
        for i, (naam, _) in enumerate(leerjaren.NIVEAUS):
            jaar = leerjaren.leerjaar_voor_niveau(eigen, i)
            opties.append((naam, leerjaren.NAMEN[jaar]))
        return self.s.menu(kr, "Hoe moeilijk?", opties, start=1,
                           info=[f"Jouw leerjaar: {leerjaren.NAMEN[eigen]} (aan te passen door je ouders)"])

    def kies_zelf(self, kr):
        s = self.s
        kolommen = [E.EENHEDEN[c] for c in E.SOORTEN]
        aan, kol, rij, melding = set(), 0, 0, ""
        knoppen = [("Spatie", "aan/uit", ord(" ")), ("Enter", "klaar", 10), ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr + ["Zelf kiezen"], knoppen)
            s.put(3, 4, "Duid minstens 2 eenheden van dezelfde soort aan.", "bold")
            for c, (kop, lijst) in enumerate(zip([E.NAMEN[c] for c in E.SOORTEN], kolommen)):
                x = 4 + c * 15
                s.put(5, x, kop, "accent")
                for r, u in enumerate(lijst):
                    vak = "[x]" if u in aan else "[ ]"
                    s.put(7 + r, x, f" {vak} {u:<4} ", "cursor" if (c, r) == (kol, rij) else "")
                    s.zones.voeg(7 + r, x, 1, 10, ("vink", c, r))
            s.put(19, 4, melding, "fout")
            k = s.toets()
            melding = ""
            if isinstance(k, tuple):
                if k[0] == "vink":
                    kol, rij = k[1], k[2]
                    aan ^= {kolommen[kol][rij]}
                continue
            if k == curses.KEY_UP:
                rij = max(0, rij - 1)
            elif k == curses.KEY_DOWN:
                rij = min(len(kolommen[kol]) - 1, rij + 1)
            elif k in (curses.KEY_LEFT, curses.KEY_RIGHT, 9):
                kol = (kol + (-1 if k == curses.KEY_LEFT else 1)) % len(kolommen)
                rij = min(rij, len(kolommen[kol]) - 1)
            elif k in (ord(" "), ord("x")):
                aan ^= {kolommen[kol][rij]}
            elif k in ENTER:
                if any(sum(u in aan for u in E.EENHEDEN[cat]) >= 2 for cat in E.SOORTEN):
                    return list(dict.fromkeys(u for lijst in kolommen for u in lijst if u in aan))
                melding = "Kies minstens 2 eenheden van dezelfde soort."
            elif k == ESC:
                return None

    # ---- hulpjes -------------------------------------------------------

    def tijd_tekst(self, ses):
        """' (7 s)' na het antwoord, als de ouder de timer zichtbaar zette."""
        if not self.app.inst.timer_zichtbaar:
            return ""
        return f"  ({round(ses.laatste_tijd_ms / 1000)} s)"

    def voortgang(self, y, nr, resultaten, soort):
        s = self.s
        totaal = self.totaal
        s.put(y, 4, f"Vraag {nr + 1} van {totaal}", "bold")
        for i in range(min(totaal, 10)):
            if i < len(resultaten):
                ch, rol = "●", "goed" if resultaten[i]["goed"] else "fout"
            else:
                ch, rol = ("◉", "accent") if i == nr else ("○", "dim")
            s.put(y, 22 + 2 * i, ch, rol)
        s.put(y, 46, f"Punten: {sum(r['goed'] for r in resultaten)}", "bold")
        s.put(y + 1, 4, soort, "dim")

    # ---- een gewone vraag ----------------------------------------------

    def stel_vraag(self, kr, v, soort, ses, nr=None, resultaten=None, vrij=False):
        """Toont één vraag. Geeft (getypt antwoord, goed?, stoppen?) of None bij Esc."""
        s = self.s
        buf, melding, goed, tip = "", "", None, False
        tip_gebruikt, tijd, punten = False, "", ""
        gezicht, ballon, spring = "normaal", "", False
        ses.vraag_getoond()
        lof = random.choice(LOF)
        while True:
            if s.te_klein():
                continue
            if goed is None:
                knoppen = [("Enter", "controleren", 10), ("Esc", "stoppen", ESC)]
                if vrij:
                    knoppen.insert(1, ("?", "tip", ord("?")))
            else:
                laatste = not vrij and nr == self.totaal - 1
                knoppen = [("Enter", "naar je resultaat" if laatste else "volgende vraag", 10),
                           ("Esc", "stoppen", ESC)]
            s.nieuw(kr, knoppen)
            if vrij:
                s.put(2, 4, f"Vrij oefenen: {self.vrij_goed + bool(goed)} van "
                            f"{self.vrij_aantal + (goed is not None)} juist", "bold")
                s.put(3, 4, soort, "dim")
            else:
                self.voortgang(2, nr, resultaten, soort)
            y, x = 6, 6
            links = f"{fmt(v.getal)} {v.van}  =  "
            s.put(y, x, links, "bold")
            vx = x + len(links)
            rol = "veld" if goed is None else ("goedvak" if goed else "foutvak")
            s.tekstvak(y, vx, buf, 14, rol)
            s.put(y, vx + 17, v.naar, "bold")
            maatje.teken(self.app, "denken" if tip and goed is None else gezicht, ballon, ruim=True, hoog=spring)
            if goed is None:
                s.put(y + 3, x, melding, "fout")
                if tip:
                    s.put(y + 3, x, "Tip: " + E.regel_uitleg(v)[0], "accent")
                    s.put(y + 4, x, "(Kijk ook eens in de spiekbrief.)", "dim")
                s.put(y + 6, x, "Kommagetal? Gebruik een komma: 0,25", "dim")
                s.cursor(True, y, vx + 1 + len(buf))
            else:
                s.cursor(False)
                if goed:
                    s.put(y + 3, x, "✔ " + lof + tijd + punten, "goed")
                    uitleg = E.regel_uitleg(v) + E.tabel_uitleg(v) if vrij else []
                else:
                    s.put(y + 3, x, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.{tijd}",
                          "fout")
                    d = E.diagnose(v, lees_getal(buf))
                    uitleg = ([d[1]] if d else []) + E.regel_uitleg(v)[:1]
                    if vrij:
                        uitleg += E.regel_uitleg(v)[1:] + E.tabel_uitleg(v)
                yy = y + 5
                for regel in uitleg:
                    for stuk in textwrap.wrap(regel, 70):
                        s.put(yy, x, stuk, "accent")
                        yy += 1
            if spring:
                s.pauze(170)
                spring = False
                continue
            k = s.toets()
            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return buf, goed, False
                if k == ESC:
                    return buf, goed, True
                continue
            if k == ESC:
                s.cursor(False)
                return None
            if k == ord("?") and vrij:
                tip = tip_gebruikt = True
            elif k in ENTER:
                getal = lees_getal(buf)
                if getal is None:
                    tip = False
                    melding = ("Typ eerst je antwoord." if not buf.strip()
                               else "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25.")
                    continue
                goed = getal == v.antwoord
                d = E.diagnose(v, getal)
                ses.antwoord(v.sleutel, v.tekst, buf.strip(), goed, d[0] if d else None, hulp=tip_gebruikt,
                             verwacht=f"{fmt(v.antwoord)} {v.naar}")
                tijd = self.tijd_tekst(ses)
                punten = f"  +{ses.laatste_punten} punten" if ses.laatste_punten else ""
                gezicht, ballon = A.reactie(goed, ses.op_rij, d[0] if d else None)
                spring = goed and self.app.inst.animaties and self.app.inst.avatar
            else:
                buf = s.bewerk(buf, k)
                melding = ""

    # ---- de tabel ------------------------------------------------------

    def teken_tabel(self, y, x, v, rijen, actief=None, klikbaar=False):
        s = self.s
        cols = E.TABELLEN[v.cat]
        cw = E.cw(v.cat)
        lijn = lambda l, m, r: l + m.join(["─" * cw] * len(cols)) + r
        s.put(y, x, lijn("┌", "┬", "┐"), "dim")
        s.put(y + 1, x, "│", "dim")
        for lab, begin, n in E.koppen(v.cat):  # een kop loopt over al de vakjes van zijn eenheid
            cx = x + 1 + begin * (cw + 1)
            breed = n * (cw + 1) - 1
            echt = lab in E.MACHT_IN[v.cat]
            rol = "accent" if lab == v.van else "accent2" if lab == v.naar else ("" if echt else "dim")
            s.put(y + 1, cx, lab.center(breed), rol)
            s.put(y + 1, cx + breed, "│", "dim")
        yy = y + 2
        if E.ALIASSEN.get(v.cat):  # tweede kopregel: ha a ca, of hl dal l dl cl ml
            s.put(yy, x, "│", "dim")
            namen = dict((i, lab) for lab, i in E.alias_kop(v.cat))
            for i in range(len(cols)):
                cx = x + 1 + i * (cw + 1)
                lab = namen.get(i, "")
                rol = "accent" if lab == v.van else "accent2" if lab == v.naar else "dim"
                s.put(yy, cx, lab.center(cw)[:max(cw, len(lab))], rol)
                s.put(yy, cx + cw, "│", "dim")
            yy += 1
        for r, (label, cellen, komma, oordeel, eigen, komma_fout) in enumerate(rijen):
            s.put(yy, x, lijn("├", "┼", "┤"), "dim")
            s.put(yy + 1, x - 7, label.rjust(5), "bold")
            s.put(yy + 1, x, "│", "dim")
            for i in range(len(cols)):
                cx = x + 1 + i * (cw + 1)
                fout = bool(oordeel) and oordeel[i] is False
                if r == 0 and actief == i:
                    rol = "cursor"
                elif oordeel and oordeel[i] is not None:
                    rol = "goedvak" if oordeel[i] else "foutvak"
                else:
                    rol = "goed" if r > 0 else ""
                s.put(yy + 1, cx, E.cel_tekst(cellen[i], i in (komma, eigen), fout, cw), rol)
                if komma_fout and i == (komma if eigen is None else eigen):
                    s.put(yy + 1, cx + cw - 1, ",", "foutvak")
                elif i in (komma, eigen) and rol in ("", "goed"):
                    s.put(yy + 1, cx + cw - 1, ",", "accent2" if i == eigen else "accent")
                s.put(yy + 1, cx + cw, "│", "dim")
                if klikbaar and r == 0:
                    s.zones.voeg(yy + 1, cx, 1, cw, ("cel", i))
                    s.zones.voeg(yy + 1, cx + cw, 1, 1, ("komma", i))
            yy += 2
        s.put(yy, x, lijn("└", "┴", "┘"), "dim")
        return yy + 1

    def tabel_vraag(self, kr, v, soort, ses, nr, resultaten):
        """Eén tabel-oefening. Geeft (antwoord, goed?, tabel goed?, stoppen?) of None bij Esc."""
        s = self.s
        inst = self.app.inst
        cols = E.TABELLEN[v.cat]
        n = len(cols)
        komma_van, komma_naar = E.kolom(v.cat, v.van), E.kolom(v.cat, v.naar)
        cw = E.cw(v.cat)
        kop_hoogte = 2 if E.ALIASSEN.get(v.cat) else 1
        verw = E.verwachte_cijfers(v)
        juist_rij = [verw.get(k) for _, k, _ in cols]
        cellen, antw, pos, laatste_cel = [None] * n, "", 0, 0
        ses.vraag_getoond()
        melding, oordeel, goed, eigen_komma = "", None, None, None
        net_getypt = None  # vakje van het laatst getypte cijfer: daar komt een , achter
        tabel_ok, tijd, punten = False, "", ""
        gezicht, ballon = "normaal", ""
        while True:
            if s.te_klein():
                continue
            if goed is None:
                knoppen = [("Tab", "verder", 9), ("←", "terug", curses.KEY_LEFT), (",", "komma", ord(",")),
                           ("↓", "antwoord", curses.KEY_DOWN), ("Enter", "nakijken", 10), ("Esc", "stop", ESC)]
            else:
                knoppen = [("Enter", "naar je resultaat" if nr == self.totaal - 1 else "volgende oefening", 10),
                           ("Esc", "stoppen", ESC)]
            s.nieuw(kr, knoppen)
            self.voortgang(2, nr, resultaten, soort)
            x = 4
            for stuk, rol in ((fmt(v.getal) + " ", "bold"), (v.van, "accent"),
                              ("  =  ?  ", "bold"), (v.naar, "accent2")):
                s.put(4, x, stuk, rol)
                x += len(stuk)
            s.put(5, 4, f"Komma achter {v.van} · nullen aanvullen tot {v.naar} · "
                        f"zet met , de komma achter {v.naar}", "dim")
            if goed is None:
                pijl = "→ naar rechts" if inst.typrichting == 1 else "← naar links"
                s.put(6, 4, "Typrichting: ", "dim")
                s.put(6, 17, pijl, "accent")
                s.put(6, 32, "(r = omdraaien)", "dim")
                s.zones.voeg(6, 4, 1, 43, ("richting",))
            komma_ok = eigen_komma == komma_naar
            rijen = [("Jij", cellen, komma_van, oordeel, eigen_komma, goed is not None and not komma_ok)]
            if goed is not None:
                rijen.append(("Juist", juist_rij, komma_naar, None, None, False))
            ya = self.teken_tabel(TABEL_Y, TABEL_X, v, rijen, pos if goed is None and pos < n else None,
                                  klikbaar=goed is None) + 1
            maatje.teken(self.app, gezicht, ballon)
            s.put(ya, 4, "Antwoord:", "bold")
            if goed is None:
                rol = "cursor" if pos == n else "veld"
            else:
                rol = "goedvak" if goed else "foutvak"
            s.tekstvak(ya, 15, antw, 14, rol, ("cel", n) if goed is None else None)
            s.put(ya, 33, v.naar, "accent2")
            if goed is None:
                if eigen_komma is not None:
                    gelezen = E.aflezen(cellen, eigen_komma)
                    plek = E.eenheid_bij(v.cat, eigen_komma) or "dit vakje"
                    if gelezen is None:
                        tekst = "Zet eerst cijfers in de tabel."
                    elif E.eenheid_bij(v.cat, eigen_komma):
                        tekst = f"Aflezen met de komma achter {plek}: {gelezen} {plek}"
                    else:
                        tekst = f"Aflezen: {gelezen}, maar bij {plek} hoort geen eenheid."
                    s.put(ya + 2, 4, tekst, "accent2")
                s.put(ya + 3, 4, melding, "fout")
                if pos < n:
                    s.cursor(True, TABEL_Y + 2 + kop_hoogte, TABEL_X + 1 + pos * (cw + 1) + cw // 2)
                else:
                    s.cursor(True, ya, 16 + len(antw))
            else:
                s.cursor(False)
                cijfers_ok = all(o is not False for o in oordeel)
                tabel_ok = cijfers_ok and komma_ok
                if goed:
                    s.put(ya + 2, 4, "✔ Je antwoord is juist!" + tijd + punten, "goed")
                else:
                    s.put(ya + 2, 4, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.{tijd}",
                          "fout")
                yy = ya + 3
                if tabel_ok:
                    s.put(yy, 4, "✔ Je tabel en je komma zijn juist.", "goed")
                    yy += 1
                if not cijfers_ok:
                    s.put(yy, 4, "✘ Kijk naar de vakjes met ! : de rij 'Juist' toont hoe het moet.", "fout")
                    yy += 1
                if eigen_komma is None:
                    s.put(yy, 4, f"✘ Je hebt de komma niet verzet: die moet achter {v.naar}.", "fout")
                    yy += 1
                elif not komma_ok:
                    s.put(yy, 4, f"✘ Je komma stond achter {E.eenheid_bij(v.cat, eigen_komma) or 'een leeg vakje'}, "
                          f"maar moest achter {v.naar}.",
                          "fout")
                    yy += 1
                s.put(yy, 4, E.regel_uitleg(v)[0], "accent")
                s.put(yy + 1, 4, f"De komma springt van {v.van} naar {v.naar}: "
                                 f"lees af → {fmt(v.antwoord)} {v.naar}.", "accent")
            k = s.toets()

            if goed is not None:
                if k in ENTER or k == ord(" "):
                    return antw, goed, tabel_ok, False
                if k == ESC:
                    return antw, goed, tabel_ok, True
                continue
            melding = ""
            vorig_getypt, net_getypt = net_getypt, None
            if isinstance(k, tuple):
                if k[0] == "cel":
                    pos = k[1]
                elif k[0] == "komma":
                    eigen_komma = None if eigen_komma == k[1] else k[1]
                elif k[0] == "richting":
                    inst.typrichting = -inst.typrichting
                    self.app.bewaar()
                if pos < n:
                    laatste_cel = pos
                continue
            if k == ESC:
                s.cursor(False)
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
                    oordeel = E.controleer_tabel(v, cellen)
                    d = E.diagnose(v, getal)
                    extra = {"cijfers_ok": all(o is not False for o in oordeel),
                             "komma_ok": eigen_komma == komma_naar,
                             "cellen": cellen, "komma": eigen_komma}
                    ses.antwoord(v.sleutel, v.tekst, antw.strip(), goed, d[0] if d else None, extra=extra,
                                 verwacht=f"{fmt(v.antwoord)} {v.naar}")
                    tijd = self.tijd_tekst(ses)
                    punten = f"  +{ses.laatste_punten} punten" if ses.laatste_punten else ""
                    gezicht, ballon = A.reactie(goed, ses.op_rij, d[0] if d else None)
            elif k in (ord("r"), ord("R")) and pos < n:
                inst.typrichting = -inst.typrichting
                self.app.bewaar()
            elif pos < n:
                if ord("0") <= k <= ord("9"):
                    cellen[pos] = k - ord("0")
                    net_getypt = pos
                    pos = max(0, min(pos + inst.typrichting, n - 1))
                elif k in BACKSPACE:
                    terug = pos - inst.typrichting
                    if cellen[pos] is None and 0 <= terug < n:
                        pos = terug
                    cellen[pos] = None
                elif k in (curses.KEY_DC, ord(" ")):
                    cellen[pos] = None
                elif k in (ord(","), ord(".")):
                    plek = pos if vorig_getypt is None else vorig_getypt
                    eigen_komma = None if eigen_komma == plek else plek
            else:
                antw = s.bewerk(antw, k)
            if pos < n:
                laatste_cel = pos

    # ---- reeksen, herhaling en rapport -----------------------------------

    def verwerk(self, v, goed, tabel, item=None):
        """Werkt de herhaalbak bij na een antwoord."""
        o, kind = self.app.opslag, self.app.kind
        if item is not None:
            if goed:
                if herhaling.juist(o, item):
                    o.punten_bij(kind.id, P.BONUS_BEHEERST, "onderwerp beheerst in de herhaalbak")
            else:
                herhaling.fout(o, kind.id, item["vaardigheid"], item["onderwerp"], item["data"])
        elif not goed:
            herhaling.fout(o, kind.id, E.OMZETTEN.id, E.onderwerp(v, tabel), E.herhaal_data(v, tabel))

    def gewichten(self):
        recent = self.app.opslag.recente_antwoorden(self.app.kind.id, E.OMZETTEN.id, 100)
        paren = {f"{a}>{b}" for c in E.SOORTEN for a in E.EENHEDEN[c] for b in E.EENHEDEN[c] if a != b}
        return selectie.gewichten(recent, E.onderwerp_van_sleutel, paren)

    def speel(self, kr, soort, modus, jaar, maker, aantal, tabel, items=None):
        """Speelt `aantal` vragen (maker(nr) maakt vraag nr). Geeft (resultaten, gestopt?)."""
        resultaten = []
        self.totaal = aantal
        with self.app.sessie(modus, E.OMZETTEN.id, jaar) as ses:
            for nr in range(aantal):
                v = maker(nr)
                if tabel:
                    uit = self.tabel_vraag(kr, v, soort, ses, nr, resultaten)
                else:
                    uit = self.stel_vraag(kr, v, soort, ses, nr, resultaten)
                if uit is None:
                    return resultaten, True
                resultaten.append(dict(v=v, antw=uit[0], goed=uit[1], tabel=uit[2] if tabel else None,
                                       tijd=ses.laatste_tijd_ms))
                self.verwerk(v, uit[1], tabel, items[nr] if items else None)
                if uit[-1]:
                    return resultaten, True
            if modus in ("reeks", "tabel") and aantal == REEKS and all(r["goed"] for r in resultaten):
                ses.bonus(P.BONUS_PERFECT, "reeks van 10 zonder fout")
            self.verdiend = ses.punten
        return resultaten, False

    def nieuwe_vragen(self, gekozen, jaar, tabel):
        """Een maker voor een reeks: slim gekozen (moeilijke omzettingen vaker) en niet recent al gezien."""
        vermijd = selectie.recent_gezien(self.app.opslag, self.app.kind.id, E.OMZETTEN.id)
        gew = self.gewichten()
        vorige = []

        def maker(nr):
            v = E.maak_vraag(gekozen, jaar, tabel, vorige[-1] if vorige else None, vermijd=vermijd, gewichten=gew)
            vermijd.add(v.sleutel)
            vorige.append(v)
            return v
        return maker

    def reeks(self, gekozen, jaar, soort, tabel):
        naam = "Tabel-oefening" if tabel else "Reeks van 10"
        while True:
            res, gestopt = self.speel(self.kruimel + [naam], soort, "tabel" if tabel else "reeks", jaar,
                                      self.nieuwe_vragen(gekozen, jaar, tabel), REEKS, tabel)
            if gestopt:
                return
            if not self.na_reeks(naam, soort, jaar, tabel, res):
                return

    def na_reeks(self, naam, soort, jaar, tabel, res):
        """Rapport tonen en eventueel fouten opnieuw of gelijkaardige vragen. True = nog een reeks."""
        while True:
            keuze = self.rapport(self.kruimel + [naam], soort, res)
            fouten = [r for r in res if not r["goed"] or r["tabel"] is False]
            if keuze == "fouten" and fouten:
                vragen = [r["v"] for r in fouten]
                res, gestopt = self.speel(self.kruimel + [naam, "Fouten opnieuw"], soort, "fouten_opnieuw", jaar,
                                          lambda nr: vragen[nr], len(vragen), tabel)
            elif keuze == "gelijkaardig" and fouten:
                vermijd = {r["v"].sleutel for r in res}
                vragen = [E.maak_herhaling(E.herhaal_data(r["v"], tabel), jaar, vermijd) for r in fouten]
                res, gestopt = self.speel(self.kruimel + [naam, "Gelijkaardige vragen"], soort, "gelijkaardig",
                                          jaar, lambda nr: vragen[nr], len(vragen), tabel)
            else:
                return keuze == "nieuw"
            if gestopt:
                return False

    def rapport(self, kr, soort, resultaten):
        """Toont de score en de uitleg. Geeft "nieuw", "menu", "fouten" of "gelijkaardig"."""
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
        regels = [(f"Je score: {goed} / {totaal}", rol), (bericht, rol), (soort, "dim"), ("", "")]
        if self.app.inst.timer_zichtbaar and totaal:
            regels.insert(3, (f"Gemiddeld {round(sum(r['tijd'] for r in resultaten) / totaal / 1000)} seconden "
                              "per vraag.", "info"))
        if self.verdiend:
            regels.insert(3, (f"★ Je verdiende {self.verdiend} punten. Je hebt er nu "
                              f"{self.app.opslag.punten_saldo(self.app.kind.id)}.", "accent"))
        regels += [(f"Vandaag in totaal: {j} van {n} juist.", "info"), ("", "")]
        fouten = [(i, r) for i, r in enumerate(resultaten) if not r["goed"] or r["tabel"] is False]
        if not fouten:
            regels.append(("Geen enkele fout. Proficiat!", "goed"))
        else:
            regels += [("Wat ging er mis? Lees de uitleg goed:", "accent"),
                       ("Met F probeer je dezelfde vragen opnieuw, met G gelijkaardige vragen met nieuwe getallen.",
                        "dim"), ("", "")]
        for i, r in fouten:
            v = r["v"]
            regels.append((f"Vraag {i + 1}:  {fmt(v.getal)} {v.van} = ? {v.naar}", "bold"))
            if r["goed"]:
                regels.append(("   Je antwoord was juist, maar in de tabel (cijfers of komma) stonden foutjes.",
                               "accent"))
            else:
                regels.append((f"   ✘ Jij schreef: {r['antw'].strip()}    Juist is: {fmt(v.antwoord)} {v.naar}",
                               "fout"))
                d = E.diagnose(v, lees_getal(r["antw"]))
                if d:
                    regels.append(("   " + d[1], "accent"))
            regels += [("   " + l, "") for l in E.regel_uitleg(v)]
            regels += [("   " + l, "info") for l in E.tabel_uitleg(v)]
            regels.append(("", ""))
        toetsen = {ord("n"): "nieuw", ord("N"): "nieuw", ESC: "menu", ord("m"): "menu", ord("M"): "menu",
                   ("nieuw",): "nieuw", ("menu",): "menu"}
        toetsen.update({k: "nieuw" for k in ENTER})
        knoppen = [("Enter", "nieuw", ("nieuw",))]
        if fouten:
            toetsen.update({ord("f"): "fouten", ord("F"): "fouten", ("fouten",): "fouten",
                            ord("g"): "gelijkaardig", ord("G"): "gelijkaardig", ("gelijk",): "gelijkaardig"})
            knoppen = [("F", "fouten opnieuw", ("fouten",)), ("G", "gelijkaardig", ("gelijk",))] + knoppen
        knoppen.append(("Esc", "menu", ("menu",)))
        return self.s.lezer(kr + ["Resultaat"], regels, knoppen, toetsen, scroll_uitleg="")

    def vrij_oefenen(self, gekozen, jaar, soort):
        kr = self.kruimel + ["Vrij oefenen"]
        self.vrij_goed = self.vrij_aantal = 0
        fouten = []
        vermijd = selectie.recent_gezien(self.app.opslag, self.app.kind.id, E.OMZETTEN.id)
        gew = self.gewichten()
        vorige = None
        with self.app.sessie("vrij", E.OMZETTEN.id, jaar) as ses:
            while True:
                v = E.maak_vraag(gekozen, jaar, vorige=vorige, vermijd=vermijd, gewichten=gew)
                vermijd.add(v.sleutel)
                vorige = v
                uit = self.stel_vraag(kr, v, soort, ses, vrij=True)
                if uit is None:
                    break
                self.vrij_aantal += 1
                self.vrij_goed += uit[1]
                self.verwerk(v, uit[1], False)
                if not uit[1]:
                    fouten.append(dict(v=v, antw=uit[0], goed=False, tabel=None, tijd=ses.laatste_tijd_ms))
                if uit[2]:
                    break
        if fouten:
            k = self.s.menu(kr, f"Je had {len(fouten)} {'fout' if len(fouten) == 1 else 'fouten'}. "
                                "Wil je ze nog eens proberen?",
                            [("Dezelfde vragen", "precies dezelfde vragen opnieuw"),
                             ("Gelijkaardige vragen", "dezelfde soort, met nieuwe getallen"),
                             ("Nee, stoppen", "")])
            keuze = {0: "fouten", 1: "gelijkaardig"}.get(k)
            if keuze:
                self.totaal = len(fouten)
                vragen = ([r["v"] for r in fouten] if keuze == "fouten" else
                          [E.maak_herhaling(E.herhaal_data(r["v"]), jaar, vermijd) for r in fouten])
                res, gestopt = self.speel(kr + ["Fouten opnieuw"], soort,
                                          "fouten_opnieuw" if keuze == "fouten" else "gelijkaardig",
                                          jaar, lambda nr: vragen[nr], len(vragen), False)
                if not gestopt:
                    self.na_reeks("Vrij oefenen", soort, jaar, False, res)

    def herhalen(self, kr, items):
        """Vragen uit de herhaalbak (met nieuwe getallen), op het eigen leerjaar van het kind."""
        jaar = self.app.inst.leerjaar
        vragen = [E.maak_herhaling(i["data"], jaar) for i in items]
        tabel = False  # herhalen gebeurt als gewone vraag; tabel-onderwerpen ook
        res, gestopt = self.speel(kr, "Herhalen · eenheden", "herhaalbak", jaar, lambda nr: vragen[nr],
                                  len(vragen), tabel, items)
        return res, gestopt

    def hervat(self, data):
        """'Verder waar je was': dezelfde oefening als de vorige keer."""
        gekozen, jaar, soort = self.keuze(data["eenheden"], data["niveau"], data["soort"])
        if data["vorm"] == "vrij":
            self.vrij_oefenen(gekozen, jaar, soort)
        else:
            self.reeks(gekozen, jaar, soort, tabel=data["vorm"] == "tabel")

    def spiekbrief(self, kr):
        toetsen = {k: None for k in (ESC, ord("q"), *ENTER)}
        toetsen[("terug",)] = None
        self.s.lezer(kr, E.spiekbrief(), [("Esc", "terug", ("terug",))], toetsen)
