"""Leerlijnen: per vaardigheid de parameters per leerjaar, als JSON in inhoud/leerlijnen/.

Een leerlijn ziet er zo uit:

    {"vaardigheid": "wiskunde.eenheden.omzetten",
     "omschrijving": "...",
     "doelen": [],
     "parameters": {"max_stap": "int", "cijfers": "lijst"},
     "leerlijn": {"4": {"max_stap": 3, "cijfers": [1, 2]}, "5": {...}}}

Een leerjaar dat ontbreekt, neemt de parameters over van het dichtstbijzijnde lagere leerjaar
(of het eerste dat bestaat). Een leerjaar met de waarde null betekent: deze vaardigheid
wordt in dat leerjaar niet aangeboden.
"""

import json
from functools import lru_cache
from pathlib import Path

from .leerjaren import LEERJAREN

MAP = Path(__file__).resolve().parent.parent / "inhoud" / "leerlijnen"

TYPES = {"int": int, "getal": (int, float), "bool": bool, "tekst": str, "lijst": list}


class LeerlijnFout(ValueError):
    pass


def valideer(data):
    """Geeft een lijst met fouten terug (leeg = in orde)."""
    fouten = []
    for veld in ("vaardigheid", "omschrijving", "doelen", "parameters", "leerlijn"):
        if veld not in data:
            fouten.append(f"veld '{veld}' ontbreekt")
    if fouten:
        return fouten
    params = data["parameters"]
    for naam, soort in params.items():
        if soort not in TYPES:
            fouten.append(f"parameter '{naam}': onbekend type '{soort}'")
    if not data["leerlijn"]:
        fouten.append("de leerlijn is leeg")
    for jaar, waarden in data["leerlijn"].items():
        if jaar not in LEERJAREN:
            fouten.append(f"onbekend leerjaar '{jaar}'")
            continue
        if waarden is None:
            continue
        for naam, soort in params.items():
            if naam not in waarden:
                fouten.append(f"leerjaar {jaar}: parameter '{naam}' ontbreekt")
            elif soort in TYPES and (not isinstance(waarden[naam], TYPES[soort])
                                     or (soort != "bool" and isinstance(waarden[naam], bool))):
                fouten.append(f"leerjaar {jaar}: '{naam}' moet van type {soort} zijn")
        for naam in waarden:
            if naam not in params:
                fouten.append(f"leerjaar {jaar}: onbekende parameter '{naam}'")
    return fouten


@lru_cache(maxsize=None)
def laad(vaardigheid):
    pad = MAP / f"{vaardigheid}.json"
    try:
        data = json.loads(pad.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise LeerlijnFout(f"geen leerlijn voor '{vaardigheid}'") from None
    fouten = valideer(data)
    if fouten:
        raise LeerlijnFout(f"{pad.name}: " + "; ".join(fouten))
    return data


def alle():
    """Namen van alle vaardigheden met een leerlijn."""
    return sorted(p.stem for p in MAP.glob("*.json"))


def parameters(vaardigheid, leerjaar):
    """De parameters van deze vaardigheid voor dit leerjaar, of None als ze er niet aangeboden wordt."""
    lijn = laad(vaardigheid)["leerlijn"]
    if leerjaar in lijn:
        return lijn[leerjaar]
    i = LEERJAREN.index(leerjaar)
    for jaar in reversed(LEERJAREN[:i]):
        if jaar in lijn:
            return lijn[jaar]
    for jaar in LEERJAREN[i + 1:]:
        if jaar in lijn:
            return lijn[jaar]
    return None
