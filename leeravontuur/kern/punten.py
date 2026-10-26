"""Punten verdienen (en later uitgeven in de winkel). Elke wijziging staat in het puntenlogboek.

Regels (eerlijk en moeilijk te 'farmen'):
- een juist antwoord: 10 punten op het eigen niveau, 5 op Makkelijk, 15 op Moeilijk, 20 op Heel moeilijk
- een vraag die het kind al eens juist had, levert niets meer op
- 'fouten opnieuw' (dezelfde vragen) levert de helft op
- een tabel helemaal juist (cijfers en komma): +5
- elke 5 juist op rij: +10; een reeks van 10 zonder fout: +20; een onderwerp beheerst in de herhaalbak: +15
- een vraagstuk: dubbel (het is meer werk), −3 per tip (minstens 5), +5 zonder tip, +5 als het klad helemaal juist is;
  pas juist na een fout eerste antwoord: de helft
- een gewone oefening (de vaste werkwijze): −2 per tip (minstens 2), +2 als het klad helemaal juist is, pas juist na
  een tweede kans: de helft
"""

from .leerjaren import LEERJAREN

PER_NIVEAU = {-1: 5, 0: 10, 1: 15, 2: 20}
OP_RIJ = 5
BONUS_OP_RIJ = 10
BONUS_PERFECT = 20
BONUS_BEHEERST = 15
BONUS_TABEL = 5
TIP_KOST = 3
BONUS_ZONDER_TIP = 5
BONUS_KLAD = 5
TIP_KOST_GEWOON = 2
BONUS_KLAD_GEWOON = 2


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
    if extra and extra.get("vraagstuk"):
        p *= 2
        if extra.get("eerste_fout") is not None:
            p //= 2
        p = max(5, p - TIP_KOST * extra.get("tips", 0))
        if not extra.get("tips"):
            p += BONUS_ZONDER_TIP
        if extra.get("klad_ok"):
            p += BONUS_KLAD
        return p, "vraagstuk juist"
    if extra and extra.get("eerste_fout") is not None:
        p //= 2
    if extra and extra.get("tips"):
        p = max(TIP_KOST_GEWOON, p - TIP_KOST_GEWOON * extra["tips"])
    if extra and extra.get("klad_ok"):
        p += BONUS_KLAD_GEWOON
    return p, "juist na een tweede kans" if extra and extra.get("eerste_fout") is not None else "juist antwoord"
