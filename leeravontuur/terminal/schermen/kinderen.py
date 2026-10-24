"""Schermen om een kind te kiezen of een nieuw kind aan te maken."""

from ...kern import leerjaren

KRUIMEL = ["Leeravontuur", "Wie ben jij?"]


def kies_kind(app):
    """Geeft het gekozen Kind, of None als er niets gekozen werd (Esc)."""
    s, opslag = app.s, app.opslag
    while True:
        kinderen = opslag.kinderen()
        if not kinderen:
            return nieuw_kind(app)
        laatste = opslag.algemeen("laatste_kind")
        start = next((i for i, k in enumerate(kinderen) if k.id == laatste), 0)
        opties = [(k.naam, leerjaren.NAMEN[k.leerjaar]) for k in kinderen]
        opties.append(("+ Nieuw kind", "een eigen account maken"))
        info = [opslag.probleem] if opslag.probleem else []
        k = s.menu(KRUIMEL, "Wie ben jij?", opties, start=start, info=info)
        if k is None:
            return None
        if k < len(kinderen):
            return kinderen[k]
        kind = nieuw_kind(app)
        if kind:
            return kind


def nieuw_kind(app):
    """Naam en leerjaar vragen en het kind aanmaken. None bij Esc."""
    s, opslag = app.s, app.opslag
    kr = KRUIMEL + ["Nieuw kind"]
    vraag = "Hallo! Hoe heet je?"
    bestaand = {k.naam.lower() for k in opslag.kinderen()}
    while True:
        naam = s.invoer(kr, vraag)
        if naam is None:
            return None
        if not naam:
            vraag = "Typ eerst je naam:"
            continue
        if naam.lower() in bestaand:
            vraag = f"Er is al iemand die {naam} heet. Kies een andere naam (bv. met een initiaal):"
            continue
        break
    opties = [(leerjaren.NAMEN[j], "") for j in leerjaren.LEERJAREN]
    k = s.menu(kr, f"In welk leerjaar zit je, {naam}?", opties, start=leerjaren.LEERJAREN.index("5"))
    if k is None:
        return None
    return opslag.nieuw_kind(naam, leerjaren.LEERJAREN[k])
