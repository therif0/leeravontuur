"""Taal: de domeinen en onderwerpen in de volgorde van het menu (het plan: docs/taal.md).

Wat nog niet gebouwd is, staat er al als een domein zonder onderwerpen: in het menu in het grijs ("komt binnenkort").
"""

from ...kern.taal import zinsontleding as ZO
from . import Domein, Onderwerp, Vak
from . import modi as M

ZINSONTLEDING = "Zinsontleding"


def oefenaar(id_, label, kern, domein):
    """Een onderwerp van de Oefenaar (reeks en vrij oefenen). De spiekbrief komt in T1.3."""
    modi = {"reeks": M.oefenaar(kern.id, "reeks", domein), "vrij": M.oefenaar(kern.id, "vrij", domein)}
    return Onderwerp(f"taal.{id_}", label, modi, None, (kern.id,), kern.omschrijving)


TAAL = Vak("taal", "Taal", (
    Domein("taal.zinsontleding", ZINSONTLEDING, (
        oefenaar("zinsontleding.zinsdelen", "Zinsdelen", ZO.ZINSONTLEDING, ZINSONTLEDING),
    ), "pv, onderwerp, lijdend en meewerkend voorwerp"),
    Domein("taal.woordsoorten", "Woordsoorten", (), "zn, lidw, bn, ww …"),
    Domein("taal.werkwoordspelling", "Werkwoordspelling", (), "d, t of dt, verleden tijd, voltooid deelwoord"),
    Domein("taal.spelling", "Spelling", (), "meervoud, verkleinwoord, ei/ij, au/ou …"),
    Domein("taal.woordenschat", "Woordenschat", (), "synoniemen, uitdrukkingen, spreekwoorden"),
    Domein("taal.lezen", "Begrijpend lezen", (), "een tekst lezen en vragen beantwoorden"),
), "zinsontleding, woordsoorten, spelling …")
