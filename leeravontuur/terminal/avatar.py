"""De avatar tekenen in de terminal: 2 pixels per teken met ▀ (16 breed, 8 hoog), of groot (32 x 16).

Zonder kleuren, in ASCII-modus of met hoog contrast wordt het een tekstgezichtje zoals [^_^].
"""

from ..kern import avatar as A
from . import thema

BREEDTE, HOOGTE = A.GROOTTE, A.GROOTTE // 2


def kan_pixels(scherm):
    return (scherm.kleuren and not scherm.ascii and scherm.inst.thema not in ("geen-kleur", "contrast")
            and thema.pixels_mogelijk())


def teken(scherm, y, x, config, uitdrukking="normaal"):
    """Tekent de avatar met de linkerbovenhoek op (y, x). Geeft de hoogte in regels terug."""
    if not kan_pixels(scherm):
        scherm.put(y, x, A.TEKSTGEZICHT.get(uitdrukking, A.TEKSTGEZICHT["normaal"]), "accent")
        return 1
    raster = A.teken(config, uitdrukking)
    for r in range(0, A.GROOTTE, 2):
        for c in range(A.GROOTTE):
            boven, onder = raster[r][c], raster[r + 1][c]
            if boven and onder:
                scherm.put(y + r // 2, x + c, "▀", thema.pixel(boven, onder))
            elif boven:
                scherm.put(y + r // 2, x + c, "▀", thema.pixel(boven))
            elif onder:
                scherm.put(y + r // 2, x + c, "▄", thema.pixel(onder))
    return HOOGTE


def teken_groot(scherm, y, x, config, uitdrukking="normaal"):
    """Dubbel zo groot (32 breed, 16 hoog): elke pixel = 2 tekens █."""
    if not kan_pixels(scherm):
        scherm.put(y, x, A.TEKSTGEZICHT.get(uitdrukking, A.TEKSTGEZICHT["normaal"]), "accent")
        return 1
    raster = A.teken(config, uitdrukking)
    for r, rij in enumerate(raster):
        for c, kleur in enumerate(rij):
            if kleur:
                scherm.put(y + r, x + 2 * c, "██", thema.pixel(kleur))
    return A.GROOTTE


def breedte(scherm):
    return BREEDTE if kan_pixels(scherm) else len(A.TEKSTGEZICHT["normaal"])
