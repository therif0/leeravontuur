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


# ---- pixels (avatar) ------------------------------------------------------------
# Kleurparen voor pixels worden pas gemaakt als ze nodig zijn, vanaf paarnummer _EERSTE.

_EERSTE = 32
_paren = {}
_ACHT_RGB = {"COLOR_BLACK": (0, 0, 0), "COLOR_RED": (205, 49, 49), "COLOR_GREEN": (13, 188, 121),
             "COLOR_YELLOW": (229, 229, 16), "COLOR_BLUE": (36, 114, 200), "COLOR_MAGENTA": (188, 63, 188),
             "COLOR_CYAN": (17, 168, 205), "COLOR_WHITE": (229, 229, 229)}


def _rgb(hexkleur):
    return tuple(int(hexkleur[i:i + 2], 16) for i in (1, 3, 5))


def _naar_256(hexkleur):
    r, g, b = _rgb(hexkleur)
    stap = lambda c: 0 if c < 48 else 1 if c < 115 else (c - 35) // 40
    ri, gi, bi = stap(r), stap(g), stap(b)
    kubus = 16 + 36 * ri + 6 * gi + bi
    niveaus = [0, 95, 135, 175, 215, 255]
    fout_kubus = sum((a - niveaus[i]) ** 2 for a, i in zip((r, g, b), (ri, gi, bi)))
    grijs = round((r + g + b) / 3)
    gi_ = max(0, min(23, round((grijs - 8) / 10)))
    gv = 8 + 10 * gi_
    fout_grijs = sum((a - gv) ** 2 for a in (r, g, b))
    return 232 + gi_ if fout_grijs < fout_kubus else kubus


def _naar_8(hexkleur):
    r, g, b = _rgb(hexkleur)
    beste = min(_ACHT_RGB, key=lambda n: sum((a - c) ** 2 for a, c in zip((r, g, b), _ACHT_RGB[n])))
    return getattr(curses, beste)


def pixels_mogelijk():
    """Kunnen we gekleurde pixels tekenen? (anders gebruikt de avatar een tekstgezichtje)"""
    try:
        return curses.has_colors() and curses.COLOR_PAIRS > _EERSTE + 8
    except curses.error:
        return False


# Pixels die een kleur van het thema volgen (bv. het cm²-rooster): pixelrol → rol in het palet, of een eigen kleur
PIXELROLLEN = {"vulling": "accent2", "rand": "accent", "lijn": ((240, "wit"),)}


def _pixelkleur(rol, thema_naam, veel):
    if rol is None:
        return -1
    bron = PIXELROLLEN[rol]
    spec = bron[0] if isinstance(bron, tuple) else PALETTEN.get(thema_naam, PALETTEN["standaard"])[bron][0]
    return _kleur(spec, veel, -1)


def rol_pixel(boven, onder=None, thema_naam="standaard"):
    """Curses-attribuut voor een halfblok met de kleuren van twee pixelrollen ("vulling", "rand", "lijn" of None)
    in dit thema. 0 als het niet kan (bv. de kleurparen zijn op)."""
    sleutel = ("rol", thema_naam, boven, onder)
    if sleutel in _paren:
        return _paren[sleutel]
    try:
        veel = curses.COLORS >= 256
        nummer = _EERSTE + len(_paren)
        if nummer >= curses.COLOR_PAIRS:
            return 0
        curses.init_pair(nummer, _pixelkleur(boven, thema_naam, veel), _pixelkleur(onder, thema_naam, veel))
        _paren[sleutel] = curses.color_pair(nummer)
    except curses.error:
        _paren[sleutel] = 0
    return _paren[sleutel]


def pixel(voor, achter=None):
    """Curses-attribuut voor een halfblok met deze voorgrond- en achtergrondkleur ('#rrggbb' of None)."""
    sleutel = (voor, achter)
    if sleutel in _paren:
        return _paren[sleutel]
    try:
        veel = curses.COLORS >= 256
        omzet = _naar_256 if veel else _naar_8
        nummer = _EERSTE + len(_paren)
        if nummer >= curses.COLOR_PAIRS:
            return 0
        curses.init_pair(nummer, omzet(voor), omzet(achter) if achter else -1)
        _paren[sleutel] = curses.color_pair(nummer)
    except curses.error:
        _paren[sleutel] = 0
    return _paren[sleutel]
