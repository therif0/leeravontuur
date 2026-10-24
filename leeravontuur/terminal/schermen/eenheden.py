"""Schermen voor eenheden omzetten: vrij oefenen, reeks van 10, tabel-oefening en spiekbrief."""

import curses
import random
import textwrap

from ...kern import leerjaren
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
        self.kruimel = list(kruimel)  # tot en met "Eenheden"

    # ---- keuzes --------------------------------------------------------

    def kies_oefening(self, vorm):
        kr = self.kruimel + [vorm]
        while True:
            k = self.s.menu(kr, "Welke eenheden wil je oefenen?", [
                ("Massa", "t  kg  hg  dag  g  dg  cg  mg"),
                ("Lengte", "km  hm  dam  m  dm  cm  mm"),
                ("Allebei", "massa en lengte door elkaar"),
                ("Zelf kiezen", "duid zelf de eenheden aan")])
            if k is None:
                return None
            if k == 3:
                gekozen = self.kies_zelf(kr)
                if gekozen is None:
                    continue
                soort = "Zelf gekozen"
            else:
                gekozen = [E.EENHEDEN[E.MASSA], E.EENHEDEN[E.LENGTE],
                           E.EENHEDEN[E.MASSA] + E.EENHEDEN[E.LENGTE]][k]
                soort = ["Massa", "Lengte", "Massa + lengte"][k]
            niveau = self.kies_niveau(kr)
            if niveau is not None:
                jaar = leerjaren.leerjaar_voor_niveau(self.app.inst.leerjaar, niveau)
                return gekozen, jaar, f"{soort} · {leerjaren.NIVEAUS[niveau][0]} ({leerjaren.NAMEN[jaar]})"

    def kies_niveau(self, kr):
        eigen = self.app.inst.leerjaar
        opties = []
        for i, (naam, _) in enumerate(leerjaren.NIVEAUS):
            jaar = leerjaren.leerjaar_voor_niveau(eigen, i)
            opties.append((naam, leerjaren.NAMEN[jaar]))
        return self.s.menu(kr, "Hoe moeilijk?", opties, start=1,
                           info=[f"Jouw leerjaar: {leerjaren.NAMEN[eigen]} (aan te passen bij Opties)"])

    def kies_zelf(self, kr):
        s = self.s
        kolommen = [E.EENHEDEN[E.MASSA], E.EENHEDEN[E.LENGTE]]
        aan, kol, rij, melding = set(), 0, 0, ""
        knoppen = [("Spatie", "aan/uit", ord(" ")), ("Enter", "klaar", 10), ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr + ["Zelf kiezen"], knoppen)
            s.put(3, 4, "Duid minstens 2 eenheden van dezelfde soort aan.", "bold")
            for c, (kop, lijst) in enumerate(zip(("Massa", "Lengte"), kolommen)):
                x = 8 + c * 30
                s.put(5, x, kop, "accent")
                for r, u in enumerate(lijst):
                    vak = "[x]" if u in aan else "[ ]"
                    s.put(7 + r, x, f" {vak} {u:<4} ", "cursor" if (c, r) == (kol, rij) else "")
                    s.zones.voeg(7 + r, x, 1, 10, ("vink", c, r))
            s.put(17, 4, melding, "fout")
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
                kol = 1 - kol
                rij = min(rij, len(kolommen[kol]) - 1)
            elif k in (ord(" "), ord("x")):
                aan ^= {kolommen[kol][rij]}
            elif k in ENTER:
                if any(sum(E.CATEGORIE[u] == cat for u in aan) >= 2 for cat in (E.MASSA, E.LENGTE)):
                    return [u for lijst in kolommen for u in lijst if u in aan]
                melding = "Kies minstens 2 eenheden bij massa of bij lengte."
            elif k == ESC:
                return None

    # ---- hulpjes -------------------------------------------------------

    def voortgang(self, y, nr, resultaten, soort):
        s = self.s
        s.put(y, 4, f"Vraag {nr + 1} van {REEKS}", "bold")
        for i in range(REEKS):
            if i < len(resultaten):
                ch, rol = "●", "goed" if resultaten[i]["goed"] else "fout"
            else:
                ch, rol = ("◉", "accent") if i == nr else ("○", "dim")
            s.put(y, 22 + 2 * i, ch, rol)
        s.put(y, 46, f"Punten: {sum(r['goed'] for r in resultaten)}", "bold")
        s.put(y + 1, 4, soort, "dim")

    # ---- een gewone vraag ----------------------------------------------

    def stel_vraag(self, kr, v, soort, nr=None, resultaten=None, vrij=False):
        """Toont één vraag. Geeft (getypt antwoord, goed?, stoppen?) of None bij Esc."""
        s = self.s
        buf, melding, goed, tip = "", "", None, False
        lof = random.choice(LOF)
        while True:
            if s.te_klein():
                continue
            if goed is None:
                knoppen = [("Enter", "controleren", 10), ("Esc", "stoppen", ESC)]
                if vrij:
                    knoppen.insert(1, ("?", "tip", ord("?")))
            else:
                laatste = not vrij and nr == REEKS - 1
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
                    s.put(y + 3, x, "✔ " + lof, "goed")
                    uitleg = E.regel_uitleg(v) + E.tabel_uitleg(v) if vrij else []
                else:
                    s.put(y + 3, x, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.", "fout")
                    d = E.diagnose(v, lees_getal(buf))
                    uitleg = ([d[1]] if d else []) + E.regel_uitleg(v)[:1]
                    if vrij:
                        uitleg += E.regel_uitleg(v)[1:] + E.tabel_uitleg(v)
                yy = y + 5
                for regel in uitleg:
                    for stuk in textwrap.wrap(regel, 70):
                        s.put(yy, x, stuk, "accent")
                        yy += 1
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
                tip = True
            elif k in ENTER:
                getal = lees_getal(buf)
                if getal is None:
                    tip = False
                    melding = ("Typ eerst je antwoord." if not buf.strip()
                               else "Dat is geen getal. Gebruik een komma voor kommagetallen, bv. 0,25.")
                    continue
                goed = getal == v.antwoord
                self.app.tel(goed)
            else:
                buf = s.bewerk(buf, k)
                melding = ""

    # ---- de tabel ------------------------------------------------------

    def teken_tabel(self, y, x, v, rijen, actief=None, klikbaar=False):
        s = self.s
        cols = E.TABELLEN[v.cat]
        cw = E.CW
        lijn = lambda l, m, r: l + m.join(["─" * cw] * len(cols)) + r
        s.put(y, x, lijn("┌", "┬", "┐"), "dim")
        s.put(y + 1, x, "│", "dim")
        for i, (lab, _, echt) in enumerate(cols):
            cx = x + 1 + i * (cw + 1)
            rol = "accent" if lab == v.van else "accent2" if lab == v.naar else ("" if echt else "dim")
            s.put(y + 1, cx, lab.center(cw), rol)
            s.put(y + 1, cx + cw, "│", "dim")
        yy = y + 2
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
                s.put(yy + 1, cx, E.cel_tekst(cellen[i], i in (komma, eigen), fout), rol)
                if komma_fout and i == (komma if eigen is None else eigen):
                    s.put(yy + 1, cx + 4, ",", "foutvak")
                elif i in (komma, eigen) and rol in ("", "goed"):
                    s.put(yy + 1, cx + 4, ",", "accent2" if i == eigen else "accent")
                s.put(yy + 1, cx + cw, "│", "dim")
                if klikbaar and r == 0:
                    s.zones.voeg(yy + 1, cx, 1, cw, ("cel", i))
                    s.zones.voeg(yy + 1, cx + cw, 1, 1, ("komma", i))
            yy += 2
        s.put(yy, x, lijn("└", "┴", "┘"), "dim")
        return yy + 1

    def tabel_vraag(self, kr, v, soort, nr, resultaten):
        """Eén tabel-oefening. Geeft (antwoord, goed?, tabel goed?, stoppen?) of None bij Esc."""
        s = self.s
        inst = self.app.inst
        cols = E.TABELLEN[v.cat]
        n = len(cols)
        labels = [lab for lab, _, _ in cols]
        komma_van, komma_naar = labels.index(v.van), labels.index(v.naar)
        verw = E.verwachte_cijfers(v)
        juist_rij = [verw.get(k) for _, k, _ in cols]
        cellen, antw, pos, laatste_cel = [None] * n, "", 0, 0
        melding, oordeel, goed, eigen_komma = "", None, None, None
        net_getypt = None  # vakje van het laatst getypte cijfer: daar komt een , achter
        tabel_ok = False
        while True:
            if s.te_klein():
                continue
            if goed is None:
                knoppen = [("Tab", "verder", 9), ("←", "terug", curses.KEY_LEFT), (",", "komma", ord(",")),
                           ("↓", "antwoord", curses.KEY_DOWN), ("Enter", "nakijken", 10), ("Esc", "stop", ESC)]
            else:
                knoppen = [("Enter", "naar je resultaat" if nr == REEKS - 1 else "volgende oefening", 10),
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
                    plek = labels[eigen_komma]
                    if gelezen is None:
                        tekst = "Zet eerst cijfers in de tabel."
                    elif cols[eigen_komma][2]:
                        tekst = f"Aflezen met de komma achter {plek}: {gelezen} {plek}"
                    else:
                        tekst = f"Aflezen: {gelezen}, maar bij {plek} hoort geen eenheid."
                    s.put(ya + 2, 4, tekst, "accent2")
                s.put(ya + 3, 4, melding, "fout")
                if pos < n:
                    s.cursor(True, TABEL_Y + 3, TABEL_X + 1 + pos * (E.CW + 1) + 2)
                else:
                    s.cursor(True, ya, 16 + len(antw))
            else:
                s.cursor(False)
                cijfers_ok = all(o is not False for o in oordeel)
                tabel_ok = cijfers_ok and komma_ok
                if goed:
                    s.put(ya + 2, 4, "✔ Je antwoord is juist!", "goed")
                else:
                    s.put(ya + 2, 4, f"✘ Niet juist. Het juiste antwoord is {fmt(v.antwoord)} {v.naar}.", "fout")
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
                    s.put(yy, 4, f"✘ Je komma stond achter {labels[eigen_komma]}, maar moest achter {v.naar}.",
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
                    self.app.tel(goed)
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

    # ---- reeksen en rapport --------------------------------------------

    def reeks(self, gekozen, jaar, soort, tabel):
        kr = self.kruimel + ["Tabel-oefening" if tabel else "Reeks van 10"]
        while True:
            resultaten, vorige = [], None
            for nr in range(REEKS):
                v = E.maak_vraag(gekozen, jaar, tabel, vorige)
                vorige = v
                if tabel:
                    uit = self.tabel_vraag(kr, v, soort, nr, resultaten)
                else:
                    uit = self.stel_vraag(kr, v, soort, nr, resultaten)
                if uit is None:
                    return
                resultaten.append(dict(v=v, antw=uit[0], goed=uit[1], tabel=uit[2] if tabel else None))
                if uit[-1]:
                    return
            if not self.rapport(kr, soort, resultaten):
                return

    def rapport(self, kr, soort, resultaten):
        naam = self.app.inst.naam
        goed = sum(r["goed"] for r in resultaten)
        if goed == REEKS:
            bericht, rol = f"Perfect{', ' + naam if naam else ''}! Alles juist!", "goed"
        elif goed >= 8:
            bericht, rol = "Heel goed gedaan!", "goed"
        elif goed >= 6:
            bericht, rol = "Goed bezig! Lees de uitleg bij je fouten en probeer nog een reeks.", "accent"
        else:
            bericht, rol = "Blijf oefenen, je kan het! Lees de uitleg hieronder rustig na.", "fout"
        st = self.app.stat
        regels = [(f"Je score: {goed} / {REEKS}", rol), (bericht, rol), (soort, "dim"), ("", ""),
                  (f"Vandaag in totaal: {st['goed']} van {st['vragen']} juist.", "info"), ("", "")]
        fouten = [(i, r) for i, r in enumerate(resultaten) if not r["goed"] or r["tabel"] is False]
        if not fouten:
            regels.append(("Geen enkele fout. Proficiat!", "goed"))
        else:
            regels += [("Wat ging er mis? Lees de uitleg goed:", "accent"), ("", "")]
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
        toetsen = {ord("n"): True, ord("N"): True, ESC: False, ord("m"): False, ord("M"): False,
                   ("nieuw",): True, ("menu",): False}
        toetsen.update({k: True for k in ENTER})
        return self.s.lezer(kr + ["Resultaat"], regels,
                            [("Enter", "nieuwe reeks", ("nieuw",)), ("Esc", "menu", ("menu",))], toetsen)

    def vrij_oefenen(self, gekozen, jaar, soort):
        kr = self.kruimel + ["Vrij oefenen"]
        self.vrij_goed = self.vrij_aantal = 0
        vorige = None
        while True:
            v = E.maak_vraag(gekozen, jaar, vorige=vorige)
            vorige = v
            uit = self.stel_vraag(kr, v, soort, vrij=True)
            if uit is None:
                return
            self.vrij_aantal += 1
            self.vrij_goed += uit[1]
            if uit[2]:
                return

    def spiekbrief(self, kr):
        toetsen = {k: None for k in (ESC, ord("q"), *ENTER)}
        toetsen[("terug",)] = None
        self.s.lezer(kr, E.spiekbrief(), [("Esc", "terug", ("terug",))], toetsen)

    # ---- het menu van dit domein ----------------------------------------

    def menu(self):
        """Kiezen tussen de oefenvormen. Niveau in de broodkruimel = len(self.kruimel) - 1."""
        from ..scherm import TerugNaar
        mijn_niveau = len(self.kruimel) - 1
        vormen = [("Vrij oefenen", "zoveel vragen als je wil, met tip en uitleg"),
                  ("Reeks van 10", "10 vragen, daarna je score en uitleg"),
                  ("Tabel-oefening", "vul de eenhedentabel in met Tab, ook met de muis"),
                  ("Spiekbrief", "hoe werkt omzetten?")]
        while True:
            try:
                k = self.s.menu(self.kruimel, "Hoe wil je oefenen?", vormen)
                if k is None:
                    return
                if k == 3:
                    self.spiekbrief(self.kruimel + ["Spiekbrief"])
                    continue
                keuze = self.kies_oefening(vormen[k][0])
                if keuze is None:
                    continue
                if k == 0:
                    self.vrij_oefenen(*keuze)
                else:
                    self.reeks(*keuze, tabel=(k == 2))
            except TerugNaar as t:
                if t.niveau < mijn_niveau:
                    raise
