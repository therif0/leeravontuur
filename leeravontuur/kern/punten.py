"""Punten verdienen (en later uitgeven in de winkel). Elke wijziging staat in het puntenlogboek.

Regels (eerlijk en moeilijk te 'farmen'):
- een juist antwoord: 10 punten op het eigen niveau, 5 op Makkelijk, 15 op Moeilijk, 20 op Heel moeilijk
- een vraag die het kind al eens juist had, levert niets meer op
- 'fouten opnieuw' (dezelfde vragen) levert de helft op
- een tabel helemaal juist (cijfers en komma): +5
- elke 5 juist op rij: +10; een reeks van 10 zonder fout: +20; een onderwerp beheerst in de herhaalbak: +15
"""

from .leerjaren import LEERJAREN

PER_NIVEAU = {-1: 5, 0: 10, 1: 15, 2: 20}
OP_RIJ = 5
BONUS_OP_RIJ = 10
BONUS_PERFECT = 20
BONUS_BEHEERST = 15
BONUS_TABEL = 5


def niveau_verschil(eigen_leerjaar, leerjaar):
    try:
        return max(-1, min(2, LEERJAREN.index(leerjaar) - LEERJAREN.index(eigen_leerjaar)))
    except ValueError:
        return 0


def voor_antwoord(juist, eigen_leerjaar, leerjaar, modus, al_juist, extra=None):
    """Punten voor één antwoord, met de reden. (0, None) als er niets te verdienen valt."""
    if not juist or al_juist:
        return 0, None
    p = PER_NIVEAU[niveau_verschil(eigen_leerjaar, leerjaar)]
    if modus == "fouten_opnieuw":
        p //= 2
    if extra and extra.get("cijfers_ok") and extra.get("komma_ok"):
        p += BONUS_TABEL
    return p, "juist antwoord"
