"""De nagekeken zinnen (inhoud/taal/zinnen.json): met de hand geschreven, voor wat de zinnenmachine niet goed maakt.

Twee lijsten: `zinnen` (volledig ontleed, per leerjaar 4, 5 of 6) en `twee` (zinnen met meer dan één persoonsvorm:
alleen pv en o). De leerlijn zegt welke leerjaren van de lijst meedoen en hoe vaak (kern/taal/zinsontleding.py).
"""

import json
from functools import lru_cache
from pathlib import Path

from . import zinnenmachine as M
from .zinnen import lees_haakjes

PAD = Path(__file__).resolve().parent.parent.parent / "inhoud" / "taal" / "zinnen.json"
JAREN = ("4", "5", "6")


@lru_cache(maxsize=None)
def _lijst():
    return json.loads(PAD.read_text(encoding="utf-8"))


def _zin(item, zinsbouw):
    """Het item uit de lijst als Zin, met de gegevens voor de proefjes (zoals de zinnenmachine ze geeft)."""
    zin = lees_haakjes(item["zin"], M.soort_van)
    eerste = zin.woorden[0].tekst
    zin.data.update({"zinsbouw": zinsbouw, "tijd": item["tijd"], "pv_andere_tijd": item.get("anders"),
                     "lv_wie": bool(item.get("wie")), "mv_vz": item.get("vz"),
                     "eerste": eerste if item.get("naam") else eerste[0].lower() + eerste[1:]})
    return zin


@lru_cache(maxsize=None)
def zinnen(jaar):
    """De volledig ontlede zinnen van dit leerjaar van de lijst ("4", "5" of "6")."""
    return tuple(_zin(i, "nagekeken") for i in _lijst()["zinnen"] if i["jaar"] == jaar)


@lru_cache(maxsize=None)
def twee():
    """De zinnen met meer dan één persoonsvorm."""
    return tuple(_zin(i, "twee_lijst") for i in _lijst()["twee"])


def kies(rng, jaren):
    """Een nagekeken zin uit een van deze leerjaren van de lijst, of None als er geen zijn."""
    alle = [z for j in jaren for z in zinnen(str(j))]
    return rng.choice(alle) if alle else None
