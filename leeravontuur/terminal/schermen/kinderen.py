"""Schermen om een kind te kiezen of een nieuw kind aan te maken."""

from ...kern import leerjaren, wachtwoord
from ..scherm import TerugNaar

KRUIMEL = ["Leeravontuur", "Wie ben jij?"]


def kies_kind(app):
    """Geeft het gekozen Kind, of None als er niets gekozen werd (Esc). Een klik op de broodkruimel ("Wie ben
    jij?") brengt terug naar de keuze; op "Leeravontuur" terug naar het hoofdmenu (of, bij het starten, hier)."""
    while True:
        try:
            return _kies_kind(app)
        except TerugNaar as t:
            if t.niveau == 0 and app.kind is not None:
                return None  # terug naar het hoofdmenu


def _kies_kind(app):
    s, opslag = app.s, app.opslag
    while True:
        kinderen = opslag.kinderen()
        if not kinderen:
            return nieuw_kind(app)
        laatste = opslag.algemeen("laatste_kind")
        start = next((i for i, k in enumerate(kinderen) if k.id == laatste), 0)
        opties = [(k.naam, leerjaren.NAMEN[k.leerjaar]) for k in kinderen]
        opties.append(("+ Nieuw kind", "een eigen account maken"))
        opties.append(("Ouders", "rapporten en instellingen (met wachtwoord)"))
        info = [opslag.probleem] if opslag.probleem else []
        k = s.menu(KRUIMEL, "Wie ben jij?", opties, start=start, info=info)
        if k is None:
            return None
        if k < len(kinderen):
            if pincode_ok(app, kinderen[k]):
                return kinderen[k]
        elif k == len(kinderen):
            kind = nieuw_kind(app)
            if kind:
                return kind
        else:
            from .ouder import Ouderdeel
            Ouderdeel(app).open()
            app.herlaad_kind()


def pincode_ok(app, kind):
    opgeslagen = app.opslag.pincode(kind.id)
    if not opgeslagen:
        return True
    for poging in range(3):
        vraag = f"Hallo {kind.naam}! Typ je pincode:" if poging == 0 else "Niet juist. Probeer nog eens:"
        pin = app.s.invoer(KRUIMEL + [kind.naam], vraag, verborgen=True, max_lengte=4, cijfers=True,
                           uitleg=["Pincode vergeten? Vraag het aan je ouders."])
        if pin is None:
            return False
        if wachtwoord.controleer(pin, opgeslagen):
            return True
    return False


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
