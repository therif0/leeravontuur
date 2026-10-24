"""Kleurenthema's. Schermen vragen een ROL ("goed", "fout", "accent" …), nooit een kleur.

Zo werkt elk thema overal: standaard, kleurenblind (rood-groen of blauw-geel), hoog contrast
en geen kleur. Juist en fout hebben op het scherm altijd ook een symbool (✔ ✘ !), zodat kleur
nooit de enige aanwijzing is.
"""

import curses

ROLLEN = ("titel", "voet", "knop", "bold", "dim", "goed", "fout", "accent", "accent2",
          "cursor", "goedvak", "foutvak", "veld", "info")

# kleur = naam (8 kleuren) of (nummer bij 256 kleuren, naam bij 8 kleuren); -1 = achtergrond van de terminal
_ZWART, _WIT = "zwart", "wit"

PALETTEN = {
    "standaard": {
        "titel": ("zwart", "cyaan", False), "voet": ("zwart", "cyaan", False),
        "knop": ("cyaan", "zwart", True),
        "goed": ("groen", -1, True), "fout": ("rood", -1, True),
        "accent": ("geel", -1, True), "accent2": ("cyaan", -1, True),
        "cursor": ("zwart", "geel", False), "goedvak": ("zwart", "groen", False),
        "foutvak": ("wit", "rood", True), "info": ("cyaan", -1, False),
    },
    # Okabe-Ito-kleuren: blauw en oranje blijven te onderscheiden bij rood-groen-kleurenblindheid
    "rood-groen": {
        "titel": (_WIT, (25, "blauw"), True), "voet": (_WIT, (25, "blauw"), False),
        "knop": ((117, "cyaan"), "zwart", True),
        "goed": ((33, "cyaan"), -1, True), "fout": ((208, "geel"), -1, True),
        "accent": (_WIT, -1, True), "accent2": ((117, "magenta"), -1, True),
        "cursor": ("zwart", (255, "wit"), False), "goedvak": (_WIT, (25, "blauw"), True),
        "foutvak": ("zwart", (208, "geel"), False), "info": ((117, "cyaan"), -1, False),
    },
    # bij blauw-geel-kleurenblindheid blijven rood en blauwgroen goed te onderscheiden
    "blauw-geel": {
        "titel": (_WIT, (124, "rood"), True), "voet": (_WIT, (124, "rood"), False),
        "knop": ((210, "rood"), "zwart", True),
        "goed": ((37, "cyaan"), -1, True), "fout": ((160, "rood"), -1, True),
        "accent": (_WIT, -1, True), "accent2": ((201, "magenta"), -1, True),
        "cursor": ("zwart", (255, "wit"), False), "goedvak": ("zwart", (37, "cyaan"), False),
        "foutvak": (_WIT, (160, "rood"), True), "info": ((37, "cyaan"), -1, False),
    },
    "contrast": {
        "titel": ("zwart", "wit", False), "voet": ("zwart", "wit", False),
        "knop": ("wit", "zwart", True),
        "goed": ("wit", -1, True), "fout": ("wit", -1, True),
        "accent": ("wit", -1, True), "accent2": ("wit", -1, True),
        "cursor": ("zwart", "wit", False), "goedvak": ("zwart", "wit", False),
        "foutvak": ("zwart", "wit", False), "info": ("wit", -1, False),
    },
}

# Zonder kleur: alleen vet, onderlijnd, omgekeerd (ook voor terminals zonder kleuren)
def _mono():
    A = curses
    return {
        "titel": A.A_REVERSE, "voet": A.A_REVERSE, "knop": A.A_REVERSE | A.A_BOLD,
        "bold": A.A_BOLD, "dim": A.A_DIM, "goed": A.A_BOLD, "fout": A.A_BOLD | A.A_UNDERLINE,
        "accent": A.A_BOLD, "accent2": A.A_UNDERLINE, "cursor": A.A_REVERSE,
        "goedvak": A.A_REVERSE, "foutvak": A.A_REVERSE | A.A_UNDERLINE,
        "veld": A.A_UNDERLINE, "info": 0, "": 0,
    }


_ACHT = {"zwart": "COLOR_BLACK", "rood": "COLOR_RED", "groen": "COLOR_GREEN", "geel": "COLOR_YELLOW",
         "blauw": "COLOR_BLUE", "magenta": "COLOR_MAGENTA", "cyaan": "COLOR_CYAN", "wit": "COLOR_WHITE"}


def _kleur(k, veel, standaard_achter):
    if k == -1:
        return standaard_achter
    if isinstance(k, tuple):
        nummer, naam = k
        return nummer if veel else getattr(curses, _ACHT[naam])
    return getattr(curses, _ACHT[k])


def maak(naam, kleuren=True):
    """Geeft {rol: curses-attribuut}. Zonder (mogelijke) kleuren: het mono-thema."""
    mono = _mono()
    if naam == "geen-kleur" or not kleuren:
        return mono
    try:
        if not curses.has_colors():
            return mono
        curses.start_color()
        try:
            curses.use_default_colors()
            achter = -1
        except curses.error:
            achter = curses.COLOR_BLACK
        veel = curses.COLORS >= 256
        attrs = dict(mono)
        for i, (rol, (vg, ag, vet)) in enumerate(PALETTEN.get(naam, PALETTEN["standaard"]).items(), 1):
            curses.init_pair(i, _kleur(vg, veel, achter), _kleur(ag, veel, achter))
            attrs[rol] = curses.color_pair(i) | (curses.A_BOLD if vet else 0)
        return attrs
    except curses.error:
        return mono
