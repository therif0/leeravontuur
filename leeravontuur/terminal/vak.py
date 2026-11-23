"""Een vak met een rand en een titel in de rand, zoals btop: de bouwsteen van de schermen 1.0 (werk/schermen.md).

Alleen weergave: wat er in het vak staat, tekent het scherm zelf binnen (y + 1, x + 2) tot (y + h - 2, x + w - 3).
"""


def label(s, y, x, tekst, rol="bold", rand="dim"):
    """┤ tekst ├ in een rand; geeft de breedte."""
    s.put(y, x, "┤ ", rand)
    s.put(y, x + 2, tekst, rol)
    s.put(y, x + 2 + len(tekst), " ├", rand)
    return len(tekst) + 4


def teken(s, y, x, h, w, titel="", rechts="", onder="", actie=None, rand="dim"):
    """De rand van (y, x) tot (y + h - 1, x + w - 1). titel = links in de bovenrand, rechts = rechts in de bovenrand
    (valt weg als het niet past), onder = een toets rechts in de onderrand, klikbaar met actie (dezelfde als de toets)."""
    if h < 2 or w < 4:
        return
    s.put(y, x, "╭" + "─" * (w - 2) + "╮", rand)
    for r in range(y + 1, y + h - 1):
        s.put(r, x, "│", rand)
        s.put(r, x + w - 1, "│", rand)
    s.put(y + h - 1, x, "╰" + "─" * (w - 2) + "╯", rand)
    bezet = x + 2 + (label(s, y, x + 2, titel[:w - 8]) if titel else 0)
    if rechts and bezet + len(rechts) + 6 <= x + w - 2:
        label(s, y, x + w - 6 - len(rechts), rechts, "dim", rand)
    if onder:
        ox = x + w - 6 - len(onder)
        label(s, y + h - 1, ox, onder, "knop", rand)
        if actie is not None:
            s.zones.voeg(y + h - 1, ox, 1, len(onder) + 4, actie)
