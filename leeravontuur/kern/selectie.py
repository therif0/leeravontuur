"""Slimme keuze van vragen: meer oefenen op wat moeilijk is, niets herhalen wat recent al kwam."""

import random
from datetime import timedelta

from . import klok

NIET_HERHALEN_DAGEN = 30


def recent_gezien(opslag, kind_id, vaardigheid, dagen=NIET_HERHALEN_DAGEN):
    """Vraagsleutels van de laatste `dagen` dagen: die proberen we niet opnieuw te geven."""
    sinds = klok.nu().date() - timedelta(days=dagen)
    return opslag.gezien_sleutels(kind_id, vaardigheid, sinds.isoformat())


def gewichten(antwoorden, onderwerp_van, alle_onderwerpen):
    """Gewicht per onderwerp: wat vaak fout gaat, komt vaker; wat nog nooit kwam, iets vaker.

    antwoorden: recente antwoorden (dicts met 'sleutel' en 'juist'); onderwerp_van(sleutel) -> onderwerp of None.
    """
    tel = {}
    for a in antwoorden:
        o = onderwerp_van(a["sleutel"])
        if o is None:
            continue
        n, f = tel.get(o, (0, 0))
        tel[o] = (n + 1, f + (0 if a["juist"] else 1))
    uit = {}
    for o in alle_onderwerpen:
        n, f = tel.get(o, (0, 0))
        uit[o] = 1.5 if n == 0 else 1.0 + 3.0 * f / n
    return uit


def kies(items, gewicht=None):
    """Willekeurig item, eventueel gewogen (gewicht: dict item -> getal)."""
    if not gewicht:
        return random.choice(items)
    return random.choices(items, weights=[gewicht.get(i, 1.0) for i in items], k=1)[0]
