"""Een digitaal klokje met grote cijfers (7 segmenten) om een tijdstip op te typen (#21).

Wat er staat komt uit kern/wiskunde/grootheden.klok_cijfers (4 tekens: '_' = nog leeg, ' ' = geen cijfer).
In ASCII-modus worden █ ░ ▪ vervangen via terminal/tekens.py.
"""

# welke segmenten oplichten: a boven, b rechtsboven, c rechtsonder, d onder, e linksonder, f linksboven, g midden
SEGMENTEN = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
             "7": "abc", "8": "abcdefg", "9": "abcdfg", " ": "", "_": "abcdefg"}
CIJFER_H, CIJFER_B = 5, 4
HOOGTE = CIJFER_H + 2          # met het kader
BREEDTE = 4 * CIJFER_B + 1 + 4 * 2 + 4 + 4  # 4 cijfers, de dubbele punt, tussenruimtes, marge en kader = 33


def cijfer_beeld(c):
    """Een cijfer als 5 regels van 4 tekens ('_' = alle segmenten, maar leeg/grijs)."""
    seg = SEGMENTEN.get(c, "")
    vol = "░" if c == "_" else "█"
    g = [[" "] * CIJFER_B for _ in range(CIJFER_H)]
    stukken = {"a": [(0, k) for k in range(CIJFER_B)], "d": [(4, k) for k in range(CIJFER_B)],
               "g": [(2, k) for k in range(CIJFER_B)], "f": [(r, 0) for r in range(3)],
               "b": [(r, 3) for r in range(3)], "e": [(r, 0) for r in range(2, 5)], "c": [(r, 3) for r in range(2, 5)]}
    for s in seg:
        for r, k in stukken[s]:
            g[r][k] = vol
    return ["".join(r) for r in g]


def compact_beeld(c):
    """Hetzelfde cijfer in 3 regels: telkens twee regels samen met halve blokjes (▀ ▄ █)."""
    groot = cijfer_beeld(c) + [" " * CIJFER_B]
    uit = []
    for boven, onder in zip(groot[0::2], groot[1::2]):
        uit.append("".join(("░" if "░" in (a, b) else "█" if a != " " and b != " " else "▀" if a != " " else
                            "▄" if b != " " else " ") for a, b in zip(boven, onder)))
    return uit


COMPACT_H = 3  # zonder kader: als er weinig plaats is (de klok in de terminal staat ernaast)


def teken(s, y, x, cijfers, rol="bold", kader="dim", actie=None, compact=False):
    """Tekent het klokje met linksboven (y, x). cijfers = 4 tekens of None (onleesbaar: leeg klokje).
    rol = de kleur van de cijfers (bold tijdens het typen, goed/fout na het nakijken).
    compact = 3 regels hoog zonder kader (COMPACT_H), anders HOOGTE."""
    cijfers = cijfers or "____"
    if compact:
        beelden = [compact_beeld(c) for c in cijfers]
        for r in range(COMPACT_H):
            xx = x
            for i, (c, beeld) in enumerate(zip(cijfers, beelden)):
                s.put(y + r, xx, beeld[r], "dim" if c == "_" else rol)
                xx += CIJFER_B + 1
                if i == 1:
                    s.put(y + r, xx, "▪" if r == 1 else " ", kader)
                    xx += 2
        if actie is not None:
            s.zones.voeg(y, x, COMPACT_H, xx - x, actie)
        return
    s.put(y, x, "┌" + "─" * (BREEDTE - 2) + "┐", kader)
    s.put(y + HOOGTE - 1, x, "└" + "─" * (BREEDTE - 2) + "┘", kader)
    beelden = [cijfer_beeld(c) for c in cijfers]
    for r in range(CIJFER_H):
        yy = y + 1 + r
        s.put(yy, x, "│", kader)
        s.put(yy, x + BREEDTE - 1, "│", kader)
        xx = x + 4
        for i, (c, beeld) in enumerate(zip(cijfers, beelden)):
            s.put(yy, xx, beeld[r], "dim" if c == "_" else rol)
            xx += CIJFER_B + 2
            if i == 1:  # de dubbele punt tussen uur en minuten
                s.put(yy, xx, "▪" if r in (1, 3) else " ", kader)
                xx += 3
    if actie is not None:
        s.zones.voeg(y, x, HOOGTE, BREEDTE, actie)
