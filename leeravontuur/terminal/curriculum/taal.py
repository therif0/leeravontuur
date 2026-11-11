"""Taal: de domeinen en onderwerpen in de volgorde van het menu (het plan: docs/taal.md).

Wat nog niet gebouwd is, staat er al als een domein zonder onderwerpen: in het menu in het grijs ("komt binnenkort").
"""

from ...kern.taal import werkwoorden as WW
from ...kern.taal import zinsontleding as ZO
from . import Domein, Onderwerp, Spiekbrief, Vak
from . import modi as M

ZINSONTLEDING = "Zinsontleding"
WERKWOORDSPELLING = "Werkwoordspelling"


def oefenaar(id_, label, kern, domein, spiek):
    """Een onderwerp van de Oefenaar (reeks en vrij oefenen), met zijn spiekbrief (ook in Leerstof)."""
    modi = {"reeks": M.oefenaar(kern.id, "reeks", domein), "vrij": M.oefenaar(kern.id, "vrij", domein)}
    return Onderwerp(f"taal.{id_}", label, modi, Spiekbrief(spiek, M.spiek_oefenaar(kern.id)), (kern.id,),
                     kern.omschrijving)


TAAL = Vak("taal", "Taal", (
    Domein("taal.zinsontleding", ZINSONTLEDING, (
        oefenaar("zinsontleding.zinsdelen", "Zinsdelen", ZO.ZINSONTLEDING, ZINSONTLEDING, "Zinsontleding"),
    ), "pv, onderwerp, lijdend en meewerkend voorwerp"),
    Domein("taal.werkwoordspelling", WERKWOORDSPELLING, (
        oefenaar("werkwoordspelling.tt", "Tegenwoordige tijd", WW.TEGENWOORDIGE_TIJD, WERKWOORDSPELLING,
                 "Tegenwoordige tijd"),
        oefenaar("werkwoordspelling.vt_zwak", "Verleden tijd: zwakke werkwoorden", WW.VERLEDEN_TIJD_ZWAK,
                 WERKWOORDSPELLING, "Verleden tijd ('t kofschip)"),
        oefenaar("werkwoordspelling.vt_sterk", "Verleden tijd: sterke werkwoorden", WW.VERLEDEN_TIJD_STERK,
                 WERKWOORDSPELLING, "Sterke werkwoorden"),
        oefenaar("werkwoordspelling.vd", "Voltooid deelwoord", WW.VOLTOOID_DEELWOORD, WERKWOORDSPELLING,
                 "Voltooid deelwoord"),
        oefenaar("werkwoordspelling.naar_vt", "Zet in de verleden tijd", WW.ZET_IN_DE_VERLEDEN_TIJD,
                 WERKWOORDSPELLING, "Van tegenwoordige naar verleden tijd"),
    ), "d, t of dt, verleden tijd, voltooid deelwoord"),
    Domein("taal.woordsoorten", "Woordsoorten", (), "zn, lidw, bn, ww …"),
    Domein("taal.spelling", "Spelling", (), "meervoud, verkleinwoord, ei/ij, au/ou …"),
    Domein("taal.woordenschat", "Woordenschat", (), "synoniemen, uitdrukkingen, spreekwoorden"),
    Domein("taal.lezen", "Begrijpend lezen", (), "een tekst lezen en vragen beantwoorden"),
), "zinsontleding, woordsoorten, spelling …")
