"""Leerjaren en niveaus.

De niveaus zijn relatief tegenover het leerjaar van het kind: Makkelijk is een jaar lager,
Heel moeilijk twee jaar hoger. Gaat het kind een jaar verder, dan schuift alles mee.
"""

LEERJAREN = ["3", "4", "5", "6", "m1", "m2"]

NAMEN = {
    "3": "3de leerjaar",
    "4": "4de leerjaar",
    "5": "5de leerjaar",
    "6": "6de leerjaar",
    "m1": "1ste middelbaar",
    "m2": "2de middelbaar",
}

# (naam, verschuiving tegenover het leerjaar van het kind)
NIVEAUS = [("Makkelijk", -1), ("Normaal", 0), ("Moeilijk", 1), ("Heel moeilijk", 2)]


def leerjaar_voor_niveau(leerjaar, niveau):
    """Welk leerjaar hoort bij dit niveau? Blijft binnen de leerjaren die bestaan."""
    i = LEERJAREN.index(leerjaar) + NIVEAUS[niveau][1]
    return LEERJAREN[max(0, min(i, len(LEERJAREN) - 1))]


def volgend(leerjaar):
    """Het leerjaar na dit leerjaar (blijft op het laatste staan)."""
    i = LEERJAREN.index(leerjaar)
    return LEERJAREN[min(i + 1, len(LEERJAREN) - 1)]
