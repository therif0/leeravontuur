"""Visuele modellen tekenen (de data komt uit kern/modellen.py).

De getallenlijn neemt 4 rijen in:  y   tekstjes bij markeringen ("start", "nu")
                                   y+1 pijlen ▼ (aflezen, markeringen, de pijl van het kind)
                                   y+2 de lijn met streepjes (en de vulling van een thermometer)
                                   y+3 de getallen onder de streepjes
"""

from ..kern.getal import fmt

HOOGTE = 4


def posities(lijn, x0=4, breedte=72):
    """x-positie van elk streepje."""
    n = max(1, len(lijn.streepjes()) - 1)
    sp = max(1, breedte // n)
    return [x0 + i * sp for i in range(n + 1)], sp


def teken_getallenlijn(s, y, lijn, cursor=None, cursor_rol="cursor", goed_bij=None, actie=None, x0=4,
                       breedte=72):
    """Tekent de lijn. cursor = index van het streepje met de pijl van het kind.
    goed_bij = waarde die als juist getoond wordt (na het nakijken).
    actie(i) = klikactie voor streepje i (dan wordt elk streepje klikbaar)."""
    streepjes = lijn.streepjes()
    xs, sp = posities(lijn, x0, breedte)
    links, rechts = xs[0] - 2, xs[-1] + 2
    # de lijn
    vul_tot = None
    if lijn.vulling is not None:
        vul_tot = xs[streepjes.index(lijn.dichtst(lijn.vulling))]
    for x in range(links, rechts + 1):
        if vul_tot is not None and xs[0] <= x <= vul_tot:
            s.put(y + 2, x, "━", "fout")
        else:
            s.put(y + 2, x, "─", "dim")
    s.put(y + 2, rechts + 1, "▶", "dim")
    for i, (x, w) in enumerate(zip(xs, streepjes)):
        gelabeld = i % max(1, lijn.label_elke) == 0 or i == len(xs) - 1
        if vul_tot is not None and x <= vul_tot:
            s.put(y + 2, x, "╋", "fout")
        else:
            s.put(y + 2, x, "┼", "bold" if gelabeld else "")
        if gelabeld:
            tekst = fmt(w)
            s.put(y + 3, max(0, x - len(tekst) // 2), tekst, "bold")
    if lijn.eenheid:
        s.put(y + 3, rechts + 2, lijn.eenheid, "bold")
    # markeringen en pijlen
    for waarde, tekst in lijn.markeringen.items():
        if lijn.van <= waarde <= lijn.tot:
            x = xs[streepjes.index(lijn.dichtst(waarde))]
            s.put(y, max(0, x - len(tekst) // 2), tekst, "accent2")
            s.put(y + 1, x, "▼", "accent2")
    if lijn.pijl is not None:
        s.put(y + 1, xs[streepjes.index(lijn.dichtst(lijn.pijl))], "▼", "accent")
    if goed_bij is not None and lijn.van <= goed_bij <= lijn.tot and goed_bij in streepjes:
        x = xs[streepjes.index(goed_bij)]
        s.put(y, max(0, x - 3), "juist", "goed")
        s.put(y + 1, x, "▼", "goed")
    if cursor is not None:
        s.put(y + 1, xs[cursor], "▼", cursor_rol)
    if actie is not None:
        for i, x in enumerate(xs):
            s.zones.voeg(y + 1, x - sp // 2, 3, max(1, sp), actie(i))
    return xs
