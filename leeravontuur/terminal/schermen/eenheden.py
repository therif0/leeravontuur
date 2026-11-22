"""Eenheden omzetten (Maten): de Oefenaar met de eenhedentabel (terminal/tabel.py).

Vrij oefenen, de reeks van 10, de tabel-oefening, het resultaat, fouten opnieuw en de herhaalbak doet de gewone
Oefenaar. Hier staat alleen wat Maten anders heeft: zelf eenheden kiezen, de keuze van het niveau, en in het resultaat
de tabel (juist antwoord, maar een fout in de tabel telt ook als fout).
"""

import curses

from ...kern import leerjaren
from ...kern.getal import fmt, lees_getal
from ...kern.wiskunde import eenheden as E
from ..oefenaar import Oefenaar
from ..scherm import ENTER, ESC
from ..tabel import TABEL_X, TABEL_Y  # noqa: F401 (de tests klikken in de tabel)


class MatenOefenaar(Oefenaar):
    FG_UITLEG = "Met F probeer je dezelfde vragen opnieuw, met G gelijkaardige vragen met nieuwe getallen."
    rapport_toetsen = {ord("m"): "menu", ord("M"): "menu"}

    def __init__(self, app, kruimel):
        super().__init__(app, kruimel, [], "Meten")  # kruimel: tot en met het onderwerp (bv. Meten › Lengte (m))

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
        self.speel_vorm(vorm, *self.keuze(gekozen, niveau, soort))
        return True

    def hervat(self, data):
        """'Verder waar je was': dezelfde oefening als de vorige keer."""
        self.speel_vorm(data["vorm"], *self.keuze(data["eenheden"], data["niveau"], data["soort"]))

    def speel_vorm(self, vorm, gekozen, jaar, soort):
        if vorm == "vrij":
            self.vrij_oefenen(E.Maten(gekozen), jaar, soort)
        elif vorm == "tabel":
            self.reeks(E.Maten(gekozen, tabel=True), jaar, soort, modus="tabel", naam="Tabel-oefening")
        else:
            self.reeks(E.Maten(gekozen), jaar, soort)

    def keuze(self, gekozen, niveau, soort):
        jaar = leerjaren.leerjaar_voor_niveau(self.app.inst.leerjaar, niveau)
        if gekozen == "alles":
            gekozen = E.eenheden_voor(jaar)
        return gekozen, jaar, f"{soort} · {leerjaren.NIVEAUS[niveau][0]} ({leerjaren.NAMEN[jaar]})"

    def kies_niveau(self, kr, o=None):
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

    # ---- het resultaat -------------------------------------------------

    @staticmethod
    def is_fout(r):
        return not r["goed"] or r.get("tabel") is False

    @staticmethod
    def fout_regels(i, r):
        om = E.omzetting(r["v"])
        regels = [(f"Vraag {i + 1}:  {fmt(om.getal)} {om.van} = ? {om.naar}", "bold")]
        if r["goed"]:
            regels.append(("   Je antwoord was juist, maar in de tabel (cijfers of komma) stonden foutjes.", "accent"))
        else:
            regels.append((f"   ✘ Jij schreef: {r['antw'].strip()}    Juist is: {fmt(om.antwoord)} {om.naar}", "fout"))
            d = E.diagnose(om, lees_getal(r["antw"]))
            if d:
                regels.append(("   " + d[1], "accent"))
        regels += [("   " + l, "") for l in E.regel_uitleg(om)]
        regels += [("   " + l, "info") for l in E.tabel_uitleg(om)]
        return regels + [("", "")]


def herhalen(app, kr, items):
    """Vragen uit de herhaalbak (met nieuwe getallen), op het eigen leerjaar van het kind; altijd als gewone vraag."""
    return MatenOefenaar(app, kr).herhalen(kr, items, {E.OMZETTEN.id: E.Maten()}, soort="Herhalen · eenheden")


def spiekbrief(app, kr):
    MatenOefenaar(app, kr).spiekbrief(kr, E.Maten())
