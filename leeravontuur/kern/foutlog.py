"""Het foutenlogboek: onverwachte fouten komen in `fouten.log` in de datamap, zodat een ouder ze kan doorgeven.

Schrijven naar het logboek mag zelf nooit een fout geven. Het bestand blijft klein (de oudste meldingen
verdwijnen eerst).
"""

import platform
import traceback

from .. import NAAM, VERSIE
from . import klok, paden

BESTAND = "fouten.log"
MAX = 200_000  # tekens
SCHEIDING = "=== "


def pad():
    return paden.data_map() / BESTAND


def schrijf(waar, fout=None, extra=""):
    """Bewaart een melding. waar = waar het gebeurde (bv. de broodkruimel), fout = de exception."""
    try:
        kop = (f"{SCHEIDING}{klok.iso()} · {NAAM} {VERSIE} · Python {platform.python_version()} · "
               f"{platform.system()} {platform.release()}\n")
        tekst = kop + f"waar: {waar}\n" + (f"{extra}\n" if extra else "")
        if fout is not None:
            tekst += "".join(traceback.format_exception(type(fout), fout, fout.__traceback__))
        p = pad()
        p.parent.mkdir(parents=True, exist_ok=True)
        oud = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        nieuw = oud + tekst + "\n"
        if len(nieuw) > MAX:
            nieuw = nieuw[-MAX:]
            begin = nieuw.find(SCHEIDING)
            nieuw = nieuw[begin:] if begin >= 0 else nieuw
        p.write_text(nieuw, encoding="utf-8")
        return True
    except Exception:  # het logboek mag nooit zelf het programma laten crashen
        return False


def meldingen():
    """Alle bewaarde meldingen (oudste eerst), elk als tekst."""
    try:
        tekst = pad().read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [SCHEIDING + stuk.strip() for stuk in tekst.split(SCHEIDING) if stuk.strip()]


def aantal():
    return len(meldingen())
