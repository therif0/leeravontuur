"""Register van vakken, domeinen en vaardigheden: Vak → Domein → Vaardigheid."""

from dataclasses import dataclass

VAKKEN = {"wiskunde": "Wiskunde", "taal": "Taal", "frans": "Frans"}


@dataclass(frozen=True)
class Vaardigheid:
    id: str            # bv. "wiskunde.eenheden.omzetten"; ook de naam van de leerlijn
    naam: str
    omschrijving: str

    @property
    def vak(self):
        return self.id.split(".")[0]

    @property
    def domein(self):
        return self.id.split(".")[1]


REGISTER = {}
DENKFOUTEN = {}  # diagnosecode -> korte omschrijving (voor rapporten)


def registreer(v):
    if v.id in REGISTER:
        raise ValueError(f"vaardigheid '{v.id}' bestaat al")
    if v.vak not in VAKKEN:
        raise ValueError(f"onbekend vak in '{v.id}'")
    REGISTER[v.id] = v
    return v
