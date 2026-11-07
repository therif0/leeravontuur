"""Herhalen › Gemengd oefenen: vragen uit verschillende thema's door elkaar, zodat het kind niets vergeet.

De keuze en de vragen komen uit de kern (kern/reeks.py); de thema's zijn de domeinen van het leerplan
(curriculum.gemengd_themas), dus Taal komt er later vanzelf bij. Het kind kiest de thema's, of de ouder legde ze vast
(Ouders › Kinderen › kind › Gemengd oefenen: vast, of één keer)."""

from dataclasses import replace

from ...kern import reeks
from .. import curriculum as CU
from ..oefenaar import Oefenaar
from ..scherm import ENTER, ESC

TITEL = "Gemengd oefenen"


def themas():
    """(items voor de afvinklijst zonder uitleg, kopjes, {thema: label}, {thema: ids}) uit het leerplan."""
    lijst = CU.gemengd_themas()
    koppen, items, vorige = {}, [], None
    for i, (v, d, _) in enumerate(lijst):
        if v is not vorige and len(CU.VAKKEN) > 1:  # één vak: geen kopje nodig
            koppen[i] = v.label.upper()
        vorige = v
        items.append((d.id, d.label))
    return items, koppen, {d.id: d.label for _, d, _ in lijst}, {d.id: ids for _, d, ids in lijst}


def labels():
    """{bewaarde id: het label in het menu} (bv. "Tafels", "Maten"), voor de regel boven elke vraag."""
    uit = {}
    for _, d, _ in CU.gemengd_themas():
        for o in d.onderwerpen:
            for i in o.opslag:
                uit.setdefault(i, CU.GROEPEN.get(i, o.label))
    return uit


def namen_tekst(namen, gekozen):
    return ", ".join(namen[t] for t in gekozen if t in namen)  # komma's: een label heeft zelf al "en"


class Gemengd:
    def __init__(self, app, kruimel):
        self.app = app
        self.s = app.s
        self.kruimel = list(kruimel)  # tot en met "Gemengd oefenen"

    def geoefend(self, ids):
        return any(reeks.bestaat(i) and reeks.stand(self.app.opslag, self.app.kind.id, i) for i in ids)

    def kies(self, items, koppen, ids, gekozen):
        """De afvinklijst voor het kind. Geeft de gekozen thema's (en bewaart ze), of None bij Esc."""
        lijst = [(t, label, "" if self.geoefend(ids[t]) else "nog niet geoefend") for t, label in items]
        k = self.s.afvink(self.kruimel, "Welke thema's oefen je door elkaar?", lijst, gekozen, koppen,
                          leeg="Kies minstens één thema.")
        if k is not None:
            alle = [t for t, _ in items]
            self.app.inst.gemengd_themas = None if k == alle else k
            self.app.bewaar()
        return k

    def ouder_koos(self, namen, gekozen):
        """De ouder legde de thema's vast: tonen, Enter = starten. False bij Esc."""
        regels = [(f"Vandaag oefen je: {namen_tekst(namen, gekozen)}.", "bold"), ("", ""),
                  ("Je ouder koos deze thema's.", "info"),
                  (f"Je krijgt {reeks.GEMENGD_AANTAL} vragen door elkaar.", "dim")]
        toetsen = {**{k: True for k in ENTER}, ("ok",): True, ESC: False, ("terug",): False}
        return self.s.lezer(self.kruimel, regels, [("Enter", "starten", ("ok",)), ("Esc", "terug", ("terug",))],
                            toetsen, scroll_uitleg="")

    def open(self):
        items, koppen, namen, ids = themas()
        alle = [t for t, _ in items]
        zelfde = None  # na "nog een reeks": dezelfde thema's, zonder opnieuw te kiezen
        while True:
            gekozen, mag_kiezen = reeks.themas_voor_reeks(self.app.inst, alle)
            if zelfde and mag_kiezen:
                gekozen = zelfde
            elif mag_kiezen:
                gekozen = self.kies(items, koppen, ids, gekozen)
                if gekozen is None:
                    return
            elif not self.ouder_koos(namen, gekozen):
                return
            plan = reeks.gemengd_plan(self.app.opslag, self.app.kind.id, {t: ids[t] for t in gekozen},
                                      self.app.inst.leerjaar, TITEL)
            if plan is None:
                self.s.lezer(self.kruimel, [("In deze thema's heb je nog niets geoefend.", "bold"), ("", ""),
                                            ("Oefen eerst in het menu van het vak; daarna komt het hier terug.", "")],
                             [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})
                if not mag_kiezen:
                    return
                zelfde = None
                continue
            self.app.onthoud_oefening({"onderwerp": "gemengd"})
            self.app.oefening_af(False)
            af, nog = Oefenaar(self.app, self.kruimel, [], TITEL).speel_plan(self.kruimel, plan, namen, labels())
            if af:
                self.app.oefening_af(True)
                na = reeks.na_reeks(self.app.inst)  # "één keer" van de ouder vervalt
                if na is not self.app.inst:
                    self.app.inst = self.app.s.inst = na
                    self.app.bewaar()
            if not nog:
                return
            zelfde = gekozen
