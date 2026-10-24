"""Snelrekenen: 60 seconden zoveel mogelijk, of 20 sommen om het snelst. Met records en een verloop."""

import random

from . import klok
from .wiskunde import hoofdrekenen as H

SOORTEN = {
    "tafels": ("Tafels", [H.TAFELS]),
    "plusmin": ("Plus en min", [H.PLUSMIN]),
    "gemengd": ("Gemengd", [H.TAFELS, H.PLUSMIN, H.DUBBELHELFT]),
}
MODI = {"snel60": "60 seconden", "snel20": "20 sommen"}
SECONDEN = 60
SOMMEN = 20
BONUS_RECORD = 25
BONUS_DAG = 10   # eerste ronde van de dag met minstens 10 juist


def vaardigheid(soort):
    return f"snelrekenen.{soort}"


def vraag(soort, leerjaar, vermijd=(), rng=random):
    onderwerp = rng.choice(SOORTEN[soort][1])
    return onderwerp, onderwerp.maak(leerjaar, vermijd, rng=rng)


def score(modus, ronde):
    """Hoe goed een ronde was: hoger = beter. 60 s: aantal juist; 20 sommen: snel én juist."""
    if modus == "snel60":
        return ronde["juist"]
    if ronde["aantal"] < SOMMEN:
        return None
    # elke fout kost 5 seconden strafttijd; minder tijd = beter
    return -(ronde["tijd_ms"] + 5000 * (ronde["aantal"] - ronde["juist"]))


def record(opslag, kind_id, modus, soort):
    """De beste ronde tot nu toe (of None)."""
    rondes = [r for r in opslag.sessie_overzicht(kind_id, modus, vaardigheid(soort)) if score(modus, r) is not None]
    return max(rondes, key=lambda r: score(modus, r)) if rondes else None


def verloop(opslag, kind_id, modus, soort, aantal=8):
    return opslag.sessie_overzicht(kind_id, modus, vaardigheid(soort))[-aantal:]


def beloon(opslag, kind_id, modus, soort, ronde, vorig_record):
    """Bonuspunten na een ronde. Geeft [(punten, reden)]."""
    uit = []
    s = score(modus, ronde)
    if s is not None and vorig_record is not None and s > score(modus, vorig_record):
        uit.append((BONUS_RECORD, f"nieuw record snelrekenen ({SOORTEN[soort][0].lower()}, {MODI[modus]})"))
    vandaag = klok.dag()
    eerder = [r for r in opslag.sessie_overzicht(kind_id, modus, vaardigheid(soort))
              if r["start"][:10] == vandaag and r["juist"] >= 10]
    if ronde["juist"] >= 10 and len(eerder) <= 1:
        uit.append((BONUS_DAG, "eerste snelrekenronde van vandaag"))
    for p, reden in uit:
        opslag.punten_bij(kind_id, p, reden)
    return uit
