"""Visuele modellen tekenen (de data komt uit kern/modellen.py).

De getallenlijn neemt 4 rijen in:  y   tekstjes bij markeringen ("start", "nu")
                                   y+1 pijlen ▼ (aflezen, markeringen, de pijl van het kind)
                                   y+2 de lijn met streepjes (en de vulling van een thermometer)
                                   y+3 de getallen onder de streepjes
"""

from ..kern.getal import fmt
from ..kern.modellen import Breukbalk, Breukbalken, Getallenlijn, Groepjes

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


# ---- breuken ---------------------------------------------------------------------------------------------

BALK_B = 52  # breedte van een breukbalk (rechts blijft plaats voor het label en het maatje)


def stuk_grenzen(noemer, x0, breedte=BALK_B):
    """[(x_begin, x_eind)] per stuk; x_begin is de scheidingslijn links van het stuk."""
    return [(x0 + i * breedte // noemer, x0 + (i + 1) * breedte // noemer) for i in range(noemer)]


def teken_balk(s, y, noemer, gearceerd, x0=8, label="", actie=None, hoogte=2):
    """Een breukbalk van `hoogte` rijen. Gearceerd = █, wit = ░, │ tussen de stukken. Geeft de rechterrand."""
    grenzen = stuk_grenzen(noemer, x0)
    for rij in range(hoogte):
        for i, (a, b) in enumerate(grenzen):
            s.put(y + rij, a, "│", "dim")
            vol = i in gearceerd
            s.put(y + rij, a + 1, ("█" if vol else "░") * max(0, b - a - 1), "accent2" if vol else "dim")
        s.put(y + rij, grenzen[-1][1], "│", "dim")
    if actie is not None:
        for i, (a, b) in enumerate(grenzen):
            s.zones.voeg(y, a + 1, hoogte, max(1, b - a - 1), actie(i))
    rechts = grenzen[-1][1]
    if label:
        s.put(y, rechts + 2, label, "bold")
    return rechts


def teken_groepjes(s, y, g, x0=8, breedte=68):
    """Bolletjes in groepjes: (●●●●) (●●●●) (○○○○). Geeft (hoogte, breedte)."""
    per = g.totaal // g.groepen
    # tot 12 per groepje: bolletjes; meer: een getal per groepje (of ? zolang de vraag loopt)
    inhoud = "●" * per if per <= 12 else (f" {per} " if g.gekleurd else " ? ")
    x, yy, rechts = x0, y, x0
    for i in range(g.groepen):
        stuk = len(inhoud) + 3
        if x + stuk > x0 + breedte:
            x, yy = x0, yy + 1
        gekleurd = i < g.gekleurd
        s.put(yy, x, "(", "dim")
        s.put(yy, x + 1, inhoud, "goed" if gekleurd else ("bold" if not g.gekleurd else "dim"))
        s.put(yy, x + 1 + len(inhoud), ")", "dim")
        x += stuk
        rechts = max(rechts, x)
    return yy - y + 1, rechts - x0


def teken_model(s, y, model, x0=8):
    """Tekent een model uit kern/modellen.py. Geeft (hoogte, breedte)."""
    if isinstance(model, Breukbalk):
        rechts = teken_balk(s, y, model.noemer, model.gearceerd, x0, model.label)
        return 2, rechts - x0 + 2 + len(model.label)
    if isinstance(model, Breukbalken):
        rechts = x0
        for i, balk in enumerate(model.balken):
            rechts = max(rechts, teken_balk(s, y + 2 * i, balk.noemer, balk.gearceerd, x0, balk.label, hoogte=1)
                         + 2 + len(balk.label))
        return 2 * len(model.balken) - 1, rechts - x0
    if isinstance(model, Groepjes):
        return teken_groepjes(s, y, model, x0)
    if isinstance(model, Getallenlijn):
        teken_getallenlijn(s, y + 1, model)
        return 5, 76
    return 0, 0
