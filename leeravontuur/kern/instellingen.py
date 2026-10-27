"""Instellingen van een kind (naam, leerjaar, kleuren, muis …). Ze worden bewaard via kern/opslag.py."""

import json
from dataclasses import dataclass, fields

from .leerjaren import LEERJAREN
from .paden import data_map

THEMAS = {
    "standaard": "standaard",
    "rood-groen": "kleurenblind (rood-groen)",
    "blauw-geel": "kleurenblind (blauw-geel)",
    "contrast": "hoog contrast",
    "geen-kleur": "geen kleur",
}


STRAFFEN = {
    "pakje": "pakje komt na 10 juiste antwoorden",
    "tijd": "pakje komt na 15 minuten oefenen",
    "kosten": "5 punten verzendkosten",
    "geen": "geen straf",
}


@dataclass
class Instellingen:
    naam: str = ""
    leerjaar: str = "5"
    thema: str = "standaard"
    ascii: bool | None = None  # None = automatisch kiezen
    muis: bool = True
    typrichting: int = 1  # in roosters: 1 = naar rechts, -1 = naar links
    timer_zichtbaar: bool = True  # de ouder kiest of het kind zijn tijd ziet (bewaard wordt ze altijd)
    avatar: bool = True
    animaties: bool = True
    winkel_straf: str = "pakje"  # bij 2x een foute som in de winkel: pakje / tijd / kosten / geen
    klokvenster: bool = True  # de wijzerklok in een eigen venster (tkinter), als dat kan
    plaatswaarden: bool = False  # bij cijferen: E T H … boven de kolommen (#18; het kind zet ze aan met p)

    def gecontroleerd(self):
        """Zet ongeldige waarden terug op de standaard."""
        std = Instellingen()
        if not isinstance(self.naam, str):
            self.naam = std.naam
        self.naam = self.naam.strip()[:20]
        if self.leerjaar not in LEERJAREN:
            self.leerjaar = std.leerjaar
        if self.thema not in THEMAS:
            self.thema = std.thema
        if self.ascii not in (None, True, False):
            self.ascii = std.ascii
        if not isinstance(self.muis, bool):
            self.muis = std.muis
        if self.typrichting not in (1, -1):
            self.typrichting = std.typrichting
        if self.winkel_straf not in STRAFFEN:
            self.winkel_straf = std.winkel_straf
        for veld in ("timer_zichtbaar", "avatar", "animaties", "klokvenster", "plaatswaarden"):
            if not isinstance(getattr(self, veld), bool):
                setattr(self, veld, getattr(std, veld))
        return self


def pad():
    """Het instellingenbestand van fase 1. Wordt bij de eerste start overgezet naar de databank."""
    return data_map() / "instellingen.json"


def laad_json(bestand):
    try:
        data = json.loads(bestand.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Instellingen()
    namen = {f.name for f in fields(Instellingen)}
    return Instellingen(**{k: v for k, v in data.items() if k in namen}).gecontroleerd()
