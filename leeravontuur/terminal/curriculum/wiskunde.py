"""Wiskunde: de domeinen en onderwerpen in de volgorde van het menu."""

from ...kern import snelrekenen as SR
from ...kern.wiskunde import breuken as BR
from ...kern.wiskunde import cijferen as C
from ...kern.wiskunde import eenheden as E
from ...kern.wiskunde import getallen as G
from ...kern.wiskunde import grootheden as TG
from ...kern.wiskunde import hoofdrekenen as H
from ...kern.wiskunde import klok as KL
from ...kern.wiskunde import meetkunde as MK
from ...kern.wiskunde import procenten as PR
from ...kern.wiskunde import vraagstukken as VS
from . import Domein, Onderwerp, Spiekbrief, Vak
from . import modi as M


def oefenaar(id_, label, kern, domein, spiek, snel=None):
    """Een onderwerp van de Oefenaar (reeks en vrij), met eventueel ook snelrekenen (60 s en 20 sommen)."""
    modi = {"reeks": M.oefenaar(kern.id, "reeks", domein), "vrij": M.oefenaar(kern.id, "vrij", domein)}
    opslag = (kern.id,)
    if snel:
        modi |= {"60s": M.snel(snel, "snel60"), "20sommen": M.snel(snel, "snel20")}
        opslag += (SR.vaardigheid(snel),)
    return Onderwerp(f"wiskunde.{id_}", label, modi, Spiekbrief(spiek, M.spiek_oefenaar(kern.id)), opslag,
                     kern.omschrijving)


EENHEDEN_SPIEK = Spiekbrief("Eenheden omzetten", M.spiek_eenheden)
GROEPEN = {E.OMZETTEN.id: "Maten"}  # de zeven maten zijn in de databank één vaardigheid
VANAF = {E.OPPERVLAKTE: "  (5de lj)", E.VOLUME: "  (6de lj)"}


def maat(id_, label, maat_, uitleg):
    modi = {vorm: M.eenheden(maat_, vorm) for vorm in ("reeks", "vrij", "tabel")}
    return Onderwerp(f"wiskunde.meten.{id_}", label, modi, EENHEDEN_SPIEK, (E.OMZETTEN.id,), uitleg)


def eenheid(soort, id_, label):
    return maat(id_, label, soort, "  ".join(E.EENHEDEN[soort]) + VANAF.get(soort, ""))


GETALLEN = "Getallen"
HOOFDREKENEN = "Hoofdrekenen"
CIJFEREN = "Cijferen"
BREUKEN_PROCENTEN = "Breuken en procenten"
METEN = "Meten"
TIJD_GELD_SNELHEID = "Tijd, geld en snelheid"
MEETKUNDE = "Meetkunde"
VRAAGSTUKKEN = "Vraagstukken"

WISKUNDE = Vak("wiskunde", "Wiskunde", (
    Domein("wiskunde.getallen", GETALLEN, (
        oefenaar("getallen.plaatswaarde", "Plaatswaarde", G.PLAATSWAARDE, GETALLEN, "Getallen"),
        oefenaar("getallen.getallenlijn", "Getallenlijn", G.GETALLENLIJN, GETALLEN, "Getallen"),
        oefenaar("getallen.afronden", "Afronden", G.AFRONDEN, GETALLEN, "Getallen"),
        oefenaar("getallen.deelbaarheid", "Deelbaarheid", G.DEELBAARHEID, GETALLEN, "Getallen"),
    ), "plaatswaarde, afronden, deelbaarheid"),
    Domein("wiskunde.hoofdrekenen", HOOFDREKENEN, (
        oefenaar("hoofdrekenen.optellen_aftrekken", "Optellen en aftrekken", H.PLUSMIN, HOOFDREKENEN, "Hoofdrekenen",
                 snel="plusmin"),
        oefenaar("hoofdrekenen.verdubbelen_halveren", "Verdubbelen en halveren", H.DUBBELHELFT, HOOFDREKENEN,
                 "Hoofdrekenen"),
        oefenaar("hoofdrekenen.tafels", "Tafels", H.TAFELS, HOOFDREKENEN, "Hoofdrekenen", snel="tafels"),
        oefenaar("hoofdrekenen.maal_deel_10_100_1000", "× en : met 10, 100, 1000", H.MAALDEEL10, HOOFDREKENEN,
                 "Hoofdrekenen"),
        oefenaar("hoofdrekenen.slim_splitsen", "Slim × en : (splitsen)", H.SPLITSEN, HOOFDREKENEN, "Hoofdrekenen"),
        Onderwerp("wiskunde.hoofdrekenen.gemengd", "Gemengd",
                  {"60s": M.snel("gemengd", "snel60"), "20sommen": M.snel("gemengd", "snel20")},
                  None, (SR.vaardigheid("gemengd"),),
                  "snel rekenen: tafels, plus en min, dubbel en helft"),
    ), "plus en min, tafels, × 10, splitsen, snel"),
    Domein("wiskunde.cijferen", CIJFEREN, (
        oefenaar("cijferen.optellen", "Optellen", C.OPTELLEN, CIJFEREN, "Cijferen"),
        oefenaar("cijferen.aftrekken", "Aftrekken", C.AFTREKKEN, CIJFEREN, "Cijferen"),
        oefenaar("cijferen.vermenigvuldigen", "Vermenigvuldigen", C.VERMENIGVULDIGEN, CIJFEREN, "Cijferen"),
        oefenaar("cijferen.staartdeling", "Staartdeling", C.DELEN, CIJFEREN, "Cijferen"),
    ), "onder elkaar: + − × en de staartdeling"),
    Domein("wiskunde.breuken_procenten", BREUKEN_PROCENTEN, (
        oefenaar("breuken_procenten.herkennen", "Herkennen", BR.HERKENNEN, BREUKEN_PROCENTEN, "Breuken"),
        oefenaar("breuken_procenten.vergelijken", "Vergelijken", BR.VERGELIJKEN, BREUKEN_PROCENTEN, "Breuken"),
        oefenaar("breuken_procenten.vereenvoudigen", "Vereenvoudigen", BR.GELIJKWAARDIG, BREUKEN_PROCENTEN,
                 "Breuken"),
        oefenaar("breuken_procenten.breuk_van_getal", "Breuk van een getal", BR.BREUK_VAN, BREUKEN_PROCENTEN,
                 "Breuken"),
        oefenaar("breuken_procenten.optellen_aftrekken", "Optellen en aftrekken", BR.OPTELLEN, BREUKEN_PROCENTEN,
                 "Breuken"),
        oefenaar("breuken_procenten.breuk_kommagetal", "Breuk en kommagetal", BR.KOMMAGETAL, BREUKEN_PROCENTEN,
                 "Breuken"),
        oefenaar("breuken_procenten.honderdveld", "Honderdveld", PR.VELD, BREUKEN_PROCENTEN, "Procenten"),
        oefenaar("breuken_procenten.procent_breuk_kommagetal", "Procent, breuk en kommagetal", PR.OMZETTEN,
                 BREUKEN_PROCENTEN, "Procenten"),
        oefenaar("breuken_procenten.procent_van_getal", "Procent van een getal", PR.PROCENT_VAN, BREUKEN_PROCENTEN,
                 "Procenten"),
        oefenaar("breuken_procenten.korting_btw", "Korting en btw", PR.KORTING, BREUKEN_PROCENTEN, "Procenten"),
    ), "breuken, procenten, korting en btw"),
    Domein("wiskunde.meten", METEN, (
        eenheid(E.LENGTE, "lengte", "Lengte (m)"),
        eenheid(E.MASSA, "massa", "Massa (g)"),
        eenheid(E.INHOUD, "inhoud", "Inhoud (l)"),
        eenheid(E.OPPERVLAKTE, "oppervlakte", "Oppervlakte (m²)"),
        eenheid(E.VOLUME, "volume", "Volume (m³)"),
        maat("maten_gemengd", "Maten gemengd", "alles", "alles wat bij je leerjaar hoort"),
        maat("maten_zelf_kiezen", "Maten zelf kiezen", "zelf", "duid zelf de eenheden aan"),
        oefenaar("meten.oppervlakte_omtrek", "Oppervlakte en omtrek", MK.ROOSTER, METEN, "Oppervlakte en formules"),
        oefenaar("meten.formules", "Formules", MK.FORMULES, METEN, "Oppervlakte en formules"),
    ), "lengte, massa, inhoud, oppervlakte, volume"),
    Domein("wiskunde.tijd_geld_snelheid", TIJD_GELD_SNELHEID, (
        oefenaar("tijd_geld_snelheid.klok", "De klok", KL.KLOK, TIJD_GELD_SNELHEID, "De klok"),
        oefenaar("tijd_geld_snelheid.tijd", "Tijd", TG.TIJD, TIJD_GELD_SNELHEID, "Tijd, geld en snelheid"),
        oefenaar("tijd_geld_snelheid.geld", "Geld", TG.GELD, TIJD_GELD_SNELHEID, "Tijd, geld en snelheid"),
        oefenaar("tijd_geld_snelheid.snelheid", "Snelheid", TG.SNELHEID, TIJD_GELD_SNELHEID,
                 "Tijd, geld en snelheid"),
    ), "de klok, uren en minuten, geld, km/u"),
    Domein("wiskunde.meetkunde", MEETKUNDE, (
        oefenaar("meetkunde.schatkaart", "Schatkaart", MK.COORDINATEN, MEETKUNDE, "Meetkunde"),
        oefenaar("meetkunde.hoeken", "Hoeken", MK.HOEKEN, MEETKUNDE, "Meetkunde"),
        oefenaar("meetkunde.schaal", "Schaal", MK.SCHAAL, MEETKUNDE, "Meetkunde"),
    ), "schatkaart, hoeken, schaal"),
    Domein("wiskunde.vraagstukken", VRAAGSTUKKEN, (
        oefenaar("vraagstukken.oplossen", "Oplossen", VS.VRAAGSTUKKEN, VRAAGSTUKKEN, "Vraagstukken"),
        oefenaar("vraagstukken.speurneus", "Speurneus", VS.SPEURNEUS, VRAAGSTUKKEN, "Vraagstukken"),
        oefenaar("vraagstukken.schatten_controleren", "Schatten en controleren", VS.SCHATTEN, VRAAGSTUKKEN,
                 "Vraagstukken"),
    ), "oplossen in 4 stappen, Speurneus, schatten"),
), "rekenen, meten, meetkunde, vraagstukken")
