"""Het oefenmaatje: de avatar van het kind naast de oefening, met een gezicht en een kort tekstje."""

from ..kern import avatar as A
from . import avatar as AV


def teken(app, gezicht="normaal", ballon="", ruim=False, hoog=False):
    """Rechtsboven op het scherm.

    ruim = er is rechts plaats voor de pixel-avatar (16 x 8); anders een tekstgezichtje + tekstje.
    hoog = één regel hoger (een sprongetje bij een juist antwoord).
    """
    s = app.s
    if not app.inst.avatar:
        return
    h, w = s.maat()
    config = app.avatar_config()
    if w >= 100 and AV.kan_pixels(s):
        x = w - AV.BREEDTE - 3
        AV.teken(s, 3 - hoog, x, config, gezicht)
        if ballon:
            s.put(4 + AV.HOOGTE, max(0, x + AV.BREEDTE // 2 - len(ballon) // 2), ballon, "accent")
    elif ruim and AV.kan_pixels(s):
        x = w - AV.BREEDTE - 1
        AV.teken(s, 1 - hoog, x, config, gezicht)
        if ballon:
            s.put(1, max(0, x - len(ballon) - 2), ballon, "accent")
    else:
        tekst = A.TEKSTGEZICHT.get(gezicht, A.TEKSTGEZICHT["normaal"]) + (" " + ballon if ballon else "")
        s.put(1, max(0, w - len(tekst) - 2), tekst, "accent")
