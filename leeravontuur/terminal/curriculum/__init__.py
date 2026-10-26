"""Het leerplan als menu: Vak → Domein → Onderwerp, met per onderwerp de oefenvormen (modi).

De menu's, de Spiekbrieven en de groepering in de rapporten komen hieruit; geen ander menubestand bevat de namen
van vakken, domeinen of onderwerpen. De ids hier zijn menu-ids (vast). `opslag` wijst naar de ids die al in de
databank staan (de vaardigheden uit kern/vaardigheden.py en snelrekenen.<soort>); die veranderen nooit.
Een modus en een spiekbrief zijn functies f(app, kruimel) die een bestaand scherm starten."""

from dataclasses import dataclass, field
from typing import Callable

# modus -> wat er op de knop in de voetregel staat
MODI = {"reeks": "reeks", "vrij": "vrij", "60s": "60 s", "20sommen": "20 sommen", "tabel": "tabel-oefening"}
# de toets van elke modus op het gemarkeerde onderwerp; Enter start de eerste van ENTER die het onderwerp heeft
TOETS = {"vrij": "v", "60s": "t", "20sommen": "z", "tabel": "h"}
SPIEK_TOETS = "s"
ENTER = ("reeks", "60s", "20sommen")
MAX_PER_MENU = 10  # de cijfertoetsen 1–9 en 0 kiezen hoogstens 10 keuzes


@dataclass(frozen=True)
class Spiekbrief:
    titel: str
    toon: Callable


@dataclass(frozen=True)
class Onderwerp:
    id: str                       # "wiskunde.meten.lengte"; vast
    label: str                    # "Lengte (m)"
    modi: dict                    # modus -> f(app, kruimel)
    spiek: Spiekbrief | None
    opslag: tuple                 # ids in de databank
    uitleg: str = ""              # grijze tekst achter het label


@dataclass(frozen=True)
class Domein:
    id: str
    label: str
    onderwerpen: tuple
    uitleg: str = ""


@dataclass(frozen=True)
class Vak:
    id: str
    label: str
    domeinen: tuple = field(default_factory=tuple)
    uitleg: str = ""


def _vakken():
    from .wiskunde import WISKUNDE
    return (WISKUNDE,)


VAKKEN = _vakken()  # volgorde = volgorde in het hoofdmenu


def domeinen():
    return [d for v in VAKKEN for d in v.domeinen]


def onderwerpen():
    return [o for d in domeinen() for o in d.onderwerpen]


def zoek(id_):
    """Het onderwerp met dit menu-id, of None."""
    return next((o for o in onderwerpen() if o.id == id_), None)


def domein_van(onderwerp):
    return next(d for d in domeinen() if onderwerp in d.onderwerpen)


def vak_van(domein):
    return next(v for v in VAKKEN if domein in v.domeinen)


def van_opslag(opslag_id):
    """De onderwerpen die bij een bewaarde id horen (de zeven maten delen er één)."""
    return [o for o in onderwerpen() if opslag_id in o.opslag]
