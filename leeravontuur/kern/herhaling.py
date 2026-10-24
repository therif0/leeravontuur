"""De herhaalbak (Leitner-systeem) en de beheersing per vaardigheid.

Een fout onderwerp (bv. "km naar m") komt in bak 1 en komt morgen terug. Elke keer juist schuift het een
bak op (na 3, dan 7 dagen). Na 3 keer juist na elkaar is het onderwerp beheerst en verdwijnt het.
Bij een fout begint het opnieuw in bak 1. Herhalen gebeurt met nieuwe getallen: zo leert het kind de
regel en niet het antwoord.
"""

from datetime import date, timedelta

from . import klok

WACHTDAGEN = {1: 1, 2: 3, 3: 7}  # bak -> dagen tot de volgende keer
LAATSTE_BAK = 3

# beheersing per vaardigheid
MIN_VRAGEN_BEHEERST = 10
DREMPEL_BEHEERST = 0.8


def vandaag():
    return klok.nu().date()


def fout(opslag, kind_id, vaardigheid, onderwerp, data):
    """Een fout: (terug) naar bak 1, morgen opnieuw."""
    opslag.herhaal_zet(kind_id, vaardigheid, onderwerp, data, 1, vandaag() + timedelta(days=WACHTDAGEN[1]))


def juist(opslag, item):
    """Juist bij het herhalen: een bak verder, of klaar na de laatste bak. Geeft True als het onderwerp klaar is."""
    if item["bak"] >= LAATSTE_BAK:
        opslag.herhaal_weg(item["kind_id"], item["vaardigheid"], item["onderwerp"])
        return True
    bak = item["bak"] + 1
    opslag.herhaal_zet(item["kind_id"], item["vaardigheid"], item["onderwerp"], item["data"], bak,
                       vandaag() + timedelta(days=WACHTDAGEN[bak]))
    return False


def aan_de_beurt(opslag, kind_id):
    return opslag.herhaalbak(kind_id, vandaag().isoformat())


# ---- beheersing -------------------------------------------------------------------

NIET_GEZIEN, BEZIG, BEHEERST = "nog niet gezien", "bezig", "beheerst"


def status(antwoorden):
    """Status van één vaardigheid op basis van de antwoorden (nieuwste eerst)."""
    if not antwoorden:
        return NIET_GEZIEN
    laatste = antwoorden[:20]
    if len(antwoorden) >= MIN_VRAGEN_BEHEERST and sum(a["juist"] for a in laatste) >= DREMPEL_BEHEERST * len(laatste):
        return BEHEERST
    return BEZIG


def overzicht(opslag, kind_id, vaardigheden):
    """[(vaardigheid, status, aantal, laatst geoefend (date of None), juist-% van de laatste 20)]."""
    uit = []
    for v in vaardigheden:
        rijen = opslag.recente_antwoorden(kind_id, v.id, 200)
        laatst = date.fromisoformat(rijen[0]["dag"]) if rijen else None
        laatste20 = rijen[:20]
        pct = round(100 * sum(a["juist"] for a in laatste20) / len(laatste20)) if laatste20 else 0
        uit.append((v, status(rijen), len(rijen), laatst, pct))
    return uit
