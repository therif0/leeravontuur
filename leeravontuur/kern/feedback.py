"""Opmerkingen van het kind of de ouder ("Zeg het ons"), bewaard in `feedback.txt` in de datamap.

Er wordt niets verstuurd: de ouder kan het bestand zelf doorgeven. Schrijven mag nooit crashen.
"""

from .. import VERSIE
from . import klok, paden

BESTAND = "feedback.txt"


def pad():
    return paden.data_map() / BESTAND


def bewaar(naam, tekst, waar=""):
    """Bewaart één opmerking. Geeft True als het gelukt is."""
    tekst = " ".join((tekst or "").split())
    if not tekst:
        return False
    try:
        p = pad()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{klok.iso()}\t{naam or '?'}\t{waar}\t{VERSIE}\t{tekst}\n")
        return True
    except OSError:
        return False


def lees():
    """Alle opmerkingen, nieuwste eerst: [{tijdstip, naam, waar, versie, tekst}]."""
    try:
        regels = pad().read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    uit = []
    for regel in regels:
        delen = regel.split("\t")
        if len(delen) == 5:
            uit.append(dict(zip(("tijdstip", "naam", "waar", "versie", "tekst"), delen)))
    return uit[::-1]
