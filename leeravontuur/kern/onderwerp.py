"""Het gemeenschappelijke model voor een oefenonderwerp (vraag → antwoord).

Een onderwerp hoort bij één vaardigheid en weet: hoe het een vraag maakt (volgens de leerlijn van een
leerjaar), hoe het nakijkt, welke denkfouten het herkent, hoe het uitlegt en hoe het een gelijkaardige vraag
maakt voor de herhaalbak. De terminal (terminal/oefenaar.py) gebruikt alleen deze methodes.
"""

import random
from dataclasses import dataclass, field
from decimal import Decimal

from . import leerlijnen
from .getal import fmt, lees_getal
from .vaardigheden import DENKFOUTEN, Vaardigheid, registreer

ONDERWERPEN = {}  # vaardigheid-id -> Onderwerp


@dataclass
class Vraag:
    vaardigheid: str
    sleutel: str           # uniek per vraag (bv. "wiskunde.hoofdrekenen.tafels:7x8")
    tekst: str             # zoals getoond, bv. "7 × 8 ="
    antwoord: Decimal
    eenheid: str = ""      # achter het antwoordvak (bv. "cm")
    data: dict = field(default_factory=dict)   # om uitleg en herhaling te maken
    leerjaar: str = "5"
    invoer: str = "getal"  # "getal", "janee" (typ ja of nee), "lijn" (aanduiden op de getallenlijn),
    #                        "rooster" (cijferen onder elkaar) of "staart" (staartdeling stap voor stap)
    model: object = None   # een visueel model (bv. kern.modellen.Getallenlijn)
    verwacht_tekst: str = ""  # zo tonen we het juiste antwoord, als het anders is dan het getal (bv. "64 rest 4")

    @property
    def verwacht(self):
        if self.verwacht_tekst:
            return self.verwacht_tekst
        tekst = self.antwoord if isinstance(self.antwoord, str) else fmt(self.antwoord)
        return tekst + (f" {self.eenheid}" if self.eenheid else "")


class Onderwerp:
    """Basis: een subklasse vult id, naam, omschrijving en maak_met() in (en liefst uitleg en diagnose)."""

    id = ""
    naam = ""
    omschrijving = ""
    denkfouten = {}

    def __init__(self):
        self.vaardigheid = registreer(Vaardigheid(self.id, self.naam, self.omschrijving))
        DENKFOUTEN.update(self.denkfouten)
        ONDERWERPEN[self.id] = self

    # ---- te overschrijven ------------------------------------------------------
    def maak_met(self, p, rng, data=None):
        """Maak een vraag met de parameters p van de leerlijn. data = vaste kenmerken (herhaling)."""
        raise NotImplementedError

    def uitleg(self, v):
        return [f"Het juiste antwoord is {v.verwacht}."]

    def tip(self, v):
        uitleg = self.uitleg(v)
        return uitleg[0] if len(uitleg) > 1 else "Denk rustig na en reken stap voor stap."

    def diagnose(self, v, getal):
        return None

    def diagnose_rijen(self, v, rijen):
        """Bij een rooster: diagnose uit alle ingevulde rijen (tekst of None per rij). None = gebruik diagnose()."""
        return None

    def kolom_hulp(self, v, rij, kolom):
        """Bij een rooster: hulp voor één vakje (rij = index in model.invul, −1 = onthouden-rij)."""
        return self.tip(v)

    def onderwerp(self, v):
        """Groepje voor herhaling en gewichten (bv. 'tafel 7')."""
        return v.data.get("onderwerp", v.sleutel.split(":", 1)[-1])

    def herhaal_data(self, v):
        return {"onderwerp": self.onderwerp(v), **{k: w for k, w in v.data.items() if k in self.vast}}

    vast = ()  # welke data-velden een gelijkaardige vraag behoudt

    def spiekbrief(self):
        return []

    # ---- algemeen ----------------------------------------------------------------
    def parameters(self, leerjaar):
        return leerlijnen.parameters(self.id, leerjaar)

    def aangeboden(self, leerjaar):
        return self.parameters(leerjaar) is not None

    def maak(self, leerjaar, vermijd=(), gewichten=None, rng=random, data=None):
        p = self.parameters(leerjaar)
        laatste = None
        for poging in range(400):
            v = self.maak_met(p, rng, data or (self.kies_onderwerp(gewichten, p, rng) if gewichten else None))
            v.leerjaar = leerjaar
            laatste = v
            if v.sleutel not in vermijd:
                return v
        return laatste

    def kies_onderwerp(self, gewichten, p, rng):
        """Met gewichten {onderwerp: gewicht}: kies een moeilijk onderwerp vaker. None = vrij."""
        return None

    def maak_herhaling(self, data, leerjaar, vermijd=()):
        return self.maak(leerjaar, vermijd, data=data)

    def lees(self, tekst):
        return lees_getal(tekst)

    def lees_vraag(self, v, tekst):
        """Leest het antwoord voor deze vraag (getal, of ja/nee)."""
        if v.invoer == "janee":
            t = tekst.strip().lower()
            return {"ja": "ja", "j": "ja", "nee": "nee", "n": "nee", "neen": "nee"}.get(t)
        return self.lees(tekst)

    def onderwerp_van_sleutel(self, sleutel):
        return None
