"""De avatar: een blokje van 16x16 pixels, samengesteld uit lagen (vorm, oren, ogen, neus, mond, haar,
hoed, accessoire). Geeft gewone kleurdata terug; de terminal (of later een GUI) tekent ze.

Een uitdrukking (blij, oeps …) bepaalt de mond en soms de ogen, zodat de avatar reageert.
"""

import json
import random
from functools import lru_cache
from pathlib import Path

BESTAND = Path(__file__).resolve().parent.parent / "inhoud" / "avatar" / "onderdelen.json"
GROOTTE = 16
LAGEN = ("vorm", "kleur", "ogen", "oren", "haar", "hoed", "accessoire")
STANDAARD = {"vorm": "vierkant", "kleur": "blauw", "ogen": "gewoon", "oren": "rond",
             "haar": None, "hoed": None, "accessoire": None}


@lru_cache(maxsize=1)
def onderdelen():
    return json.loads(BESTAND.read_text(encoding="utf-8"))


def opties(laag):
    """{sleutel: naam} van alles wat er in een laag bestaat."""
    d = onderdelen()
    groep = {"vorm": "vormen", "kleur": "kleuren"}.get(laag, laag)
    return {k: v["naam"] for k, v in d[groep].items()}


def geldig(config):
    """Vult ontbrekende of onbekende onderdelen aan met de standaard."""
    d = onderdelen()
    uit = dict(STANDAARD)
    for laag in LAGEN:
        waarde = (config or {}).get(laag, STANDAARD[laag])
        groep = {"vorm": "vormen", "kleur": "kleuren"}.get(laag, laag)
        if waarde is None and STANDAARD[laag] is None:
            uit[laag] = None
        elif waarde in d[groep]:
            uit[laag] = waarde
    return uit


def _mix(hexkleur, factor):
    """Lichter (factor > 0, naar wit) of donkerder (factor < 0, naar zwart)."""
    r, g, b = (int(hexkleur[i:i + 2], 16) for i in (1, 3, 5))
    if factor >= 0:
        r, g, b = (round(c + (255 - c) * factor) for c in (r, g, b))
    else:
        r, g, b = (round(c * (1 + factor)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def _plaats(raster, patroon, y, x, kleuren, spiegel=False):
    for dy, rij in enumerate(patroon):
        if spiegel:
            rij = rij[::-1]
        for dx, ch in enumerate(rij):
            if ch == "." or ch == " ":
                continue
            yy, xx = y + dy, x + dx
            if 0 <= yy < GROOTTE and 0 <= xx < GROOTTE:
                raster[yy][xx] = kleuren[ch]


def teken(config=None, uitdrukking="normaal"):
    """Het raster: GROOTTE rijen van GROOTTE kleuren ('#rrggbb' of None = doorzichtig)."""
    d = onderdelen()
    c = geldig(config)
    lijf = d["kleuren"][c["kleur"]]["rgb"]
    kleuren = dict(d["palet"], K=lijf, D=_mix(lijf, -0.35), L=_mix(lijf, 0.35))
    vorm = d["vormen"][c["vorm"]]
    a = vorm["ankers"]
    uit = d["uitdrukkingen"].get(uitdrukking, d["uitdrukkingen"]["normaal"])
    raster = [[None] * GROOTTE for _ in range(GROOTTE)]

    _plaats(raster, vorm["pixels"], 0, 0, kleuren)
    oor = d["oren"][c["oren"]]["pixels"]
    oy, oxl, oxr = a["oren"]
    _plaats(raster, oor, oy, oxl, kleuren)
    _plaats(raster, oor, oy, oxr, kleuren, spiegel=True)

    oog = d["ogen"][c["ogen"]]
    gy, gxl, gxr = a["ogen"]
    links = uit.get("ogen") or oog["pixels"]
    rechts = uit.get("ogen") or oog.get("rechts") or oog["pixels"]
    _plaats(raster, links, gy, gxl, kleuren)
    _plaats(raster, rechts, gy, gxr, kleuren)

    ny, nx = a["neus"]
    _plaats(raster, d["neus"], ny, nx, kleuren)
    my, mx = a["mond"]
    _plaats(raster, uit["mond"], my, mx, kleuren)

    top = a["top"]
    if c["haar"]:
        haar = d["haar"][c["haar"]]["pixels"]
        _plaats(raster, haar, top - len(haar) + 1, 0, kleuren)
    if c["hoed"]:
        hoed = d["hoed"][c["hoed"]]["pixels"]
        _plaats(raster, hoed, top - len(hoed) + 1, 0, kleuren)
    if c["accessoire"]:
        acc = d["accessoire"][c["accessoire"]]
        if acc["anker"] == "top":
            y, x = top, acc.get("x", 0)
        else:
            y, x = a[acc["anker"]][:2]
        _plaats(raster, acc["pixels"], y + acc.get("dy", 0), x + acc.get("dx", 0), kleuren)
    return raster


# ---- reacties (oefenmaatje) -----------------------------------------------------

LOF = ["Top!", "Super!", "Yes!", "Knap!", "Goed zo!", "Prima!"]
TIPS = {
    "verkeerde_richting": "Andere kant op!",
    "factor_10": "Tel de kolommen!",
    "niet_omgezet": "Vergeet niet om te zetten!",
}


def reactie(juist, op_rij=0, diagnose=None, punten=0):
    """(uitdrukking, kort tekstje) na een antwoord."""
    if juist:
        if op_rij and op_rij % 5 == 0:
            return "trots", f"{op_rij} op rij!"
        return "blij", random.choice(LOF)
    if diagnose in TIPS:
        return "denken", "Psst… " + TIPS[diagnose]
    return "aanmoedigend", random.choice(["Bijna!", "Volgende lukt!", "Niet erg, probeer!"])


TEKSTGEZICHT = {
    "normaal": "[o_o]", "blij": "[^_^]", "trots": "[^o^]", "verrast": "[O_O]", "denken": "[o_~]",
    "oeps": "[x_x]", "aanmoedigend": "[^-^]", "geconcentreerd": "[-_-]",
}
