"""Starters voor de modi: elk een functie f(app, kruimel) die een bestaand oefenscherm opent.

Ze doen wat de oude menu's deden na de keuze van de vorm: het niveau vragen (waar dat nu gebeurt), de oefening
onthouden voor 'Verder' en ze starten. Met functools.partial vastgezet in de registry."""

from functools import partial

from ...kern import catalogus
from ...kern import snelrekenen as SR
from ..oefenaar import VORMEN, Oefenaar
from ..schermen.eenheden import Eenheden
from ..schermen.snelrekenen import Snelrekenen

_VORM_NAAM = {vorm: naam for naam, vorm, _ in VORMEN if vorm}
_EENHEDEN_VORM = {"vrij": "Vrij oefenen", "reeks": "Reeks van 10", "tabel": "Tabel-oefening"}


def _oefenaar(vid, vorm, domein, app, kr):
    o = catalogus.ONDERWERPEN[vid]
    scherm = Oefenaar(app, kr, [o], domein)
    niveau = scherm.kies_niveau(kr + [_VORM_NAAM[vorm]], o)
    if niveau is None:
        return
    app.onthoud_oefening({"onderwerp": "oefenaar", "vaardigheid": o.id, "vorm": vorm, "niveau": niveau,
                          "domein": domein})
    scherm.start(o, vorm, niveau)


def _eenheden(maat, vorm, app, kr):
    Eenheden(app, kr).oefen(vorm, maat, kr + [_EENHEDEN_VORM[vorm]])


def _snel(soort, modus, app, kr):
    Snelrekenen(app).ronde(kr + [SR.MODI[modus]], soort, modus)


def _spiek_oefenaar(vid, app, kr):
    o = catalogus.ONDERWERPEN[vid]
    Oefenaar(app, kr, [o], "").spiekbrief(kr, o)


def _spiek_eenheden(app, kr):
    Eenheden(app, kr).spiekbrief(kr)


def oefenaar(vid, vorm, domein):
    return partial(_oefenaar, vid, vorm, domein)


def eenheden(maat, vorm):
    return partial(_eenheden, maat, vorm)


def snel(soort, modus):
    return partial(_snel, soort, modus)


def spiek_oefenaar(vid):
    return partial(_spiek_oefenaar, vid)


spiek_eenheden = _spiek_eenheden
