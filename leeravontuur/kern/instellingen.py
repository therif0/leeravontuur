"""Instellingen (naam, leerjaar, kleuren, muis …), bewaard als JSON in de datamap.

In een volgende fase komen die per kind in de databank. Tot dan is er één instellingenbestand.
"""

import json
from dataclasses import asdict, dataclass, fields

from .leerjaren import LEERJAREN
from .paden import data_map

THEMAS = {
    "standaard": "standaard",
    "rood-groen": "kleurenblind (rood-groen)",
    "blauw-geel": "kleurenblind (blauw-geel)",
    "contrast": "hoog contrast",
    "geen-kleur": "geen kleur",
}


@dataclass
class Instellingen:
    naam: str = ""
    leerjaar: str = "5"
    thema: str = "standaard"
    ascii: bool | None = None  # None = automatisch kiezen
    muis: bool = True
    typrichting: int = 1  # in roosters: 1 = naar rechts, -1 = naar links

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
        return self


def pad():
    return data_map() / "instellingen.json"


def laad():
    try:
        data = json.loads(pad().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Instellingen()
    namen = {f.name for f in fields(Instellingen)}
    return Instellingen(**{k: v for k, v in data.items() if k in namen}).gecontroleerd()


def bewaar(inst):
    p = pad()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(inst), indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False
