"""Het gemeenschappelijke model voor een oefenonderwerp (vraag → antwoord).

Een onderwerp hoort bij één vaardigheid en weet: hoe het een vraag maakt (volgens de leerlijn van een
leerjaar), hoe het nakijkt, welke denkfouten het herkent, hoe het uitlegt en hoe het een gelijkaardige vraag
maakt voor de herhaalbak. De terminal (terminal/oefenaar.py) gebruikt alleen deze methodes.
"""

import random
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction

from . import foutlog, leerlijnen
from .leerjaren import LEERJAREN
from .getal import GetypteBreuk, fmt, fmt_breuk, lees_breuk, lees_getal
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
    #                        "rooster" (cijferen onder elkaar), "staart" (staartdeling stap voor stap),
    #                        "breuk" (typ een breuk), "vergelijk" (<, > of =), "balk" (arceren op de breukbalk)
    #                        "veld" (kleuren in het honderdveld), "duur" (typ 2 u 15 min), "klok" (typ 11.15),
    #                        "woord" (een hoek benoemen), "plek" (typ C4) of "coord" (kruisje op de schatkaart)
    model: object = None   # een visueel model (bv. kern.modellen.Getallenlijn)
    verwacht_tekst: str = ""  # zo tonen we het juiste antwoord, als het anders is dan het getal (bv. "64 rest 4")
    model_na: object = None   # een model dat pas na het nakijken getoond wordt (uitleg die het antwoord verklapt)

    @property
    def verwacht(self):
        if self.verwacht_tekst:
            return self.verwacht_tekst
        if isinstance(self.antwoord, str):
            tekst = self.antwoord
        elif isinstance(self.antwoord, Fraction):
            tekst = fmt_breuk(self.antwoord)
        else:
            tekst = fmt(self.antwoord)
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

    def nakijken(self, v, getal):
        """Is het (gelezen) antwoord juist? Een GetypteBreuk telt op zijn waarde, tenzij de vraag de
        eenvoudigste vorm eist (data["vereenvoudigd"])."""
        if isinstance(getal, GetypteBreuk):
            if getal.waarde != v.antwoord:
                return False
            return getal.eenvoudigst or not v.data.get("vereenvoudigd")
        return getal == v.antwoord

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

    def jaar_voor(self, leerjaar):
        """Het leerjaar om een vraag te maken: dit leerjaar, of (als het onderwerp daar nog niet bestaat) het
        eerste hogere leerjaar waar het wel bestaat, anders het dichtste lagere."""
        if self.aangeboden(leerjaar):
            return leerjaar
        i = LEERJAREN.index(leerjaar) if leerjaar in LEERJAREN else 0
        for jaar in LEERJAREN[i + 1:] + LEERJAREN[:i][::-1]:
            if self.aangeboden(jaar):
                return jaar
        return leerjaar

    def maak(self, leerjaar, vermijd=(), gewichten=None, rng=random, data=None):
        leerjaar = self.jaar_voor(leerjaar)
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
        """Een gelijkaardige vraag. Mag nooit crashen: past de bewaarde data niet (meer), bv. uit een oudere
        versie, dan komt er een gewone vraag van dit onderwerp (en een melding in het foutenlogboek)."""
        try:
            return self.maak(leerjaar, vermijd, data=data)
        except Exception as e:
            foutlog.schrijf(f"herhaling {self.id} met {data!r}", e)
            return self.maak(leerjaar, vermijd)

    def lees(self, tekst):
        return lees_getal(tekst)

    def lees_vraag(self, v, tekst):
        """Leest het antwoord voor deze vraag (getal, of ja/nee)."""
        if v.invoer == "janee":
            t = tekst.strip().lower()
            return {"ja": "ja", "j": "ja", "nee": "nee", "n": "nee", "neen": "nee"}.get(t)
        if v.invoer == "vergelijk":
            t = tekst.strip()
            return t if t in ("<", ">", "=") else None
        if v.invoer in ("breuk", "balk"):
            return lees_breuk(tekst)
        return self.lees(tekst)

    def onderwerp_van_sleutel(self, sleutel):
        return None
