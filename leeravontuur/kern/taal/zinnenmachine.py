"""De zinnenmachine: een zinsbouw × woorden uit de woordenlijst (inhoud/taal/woorden.json) = een volledig ontlede zin.

Zoals bij de vraagstukken: de zinsbouw zegt welke zinsdelen er zijn en in welke volgorde, de woordenlijst geeft de
woorden. Omdat de machine weet waar elk woord vandaan komt, kent ze de zinsdelen én de woordsoorten. De pv past bij het
onderwerp (enkelvoud of meervoud) en bij de tijd; het lijdend voorwerp past bij het werkwoord (*lezen* een boek,
*eten* een appel).

Een zinsbouw (de code in de leerlijn):
    o_pv              De hond slaapt.
    o_pv_lv           De juf leest een boek.
    o_pv_mv_lv        Oma geeft haar kleinzoon een fiets.
    bwb_pv_o_lv       Morgen koopt opa een nieuwe fiets.         (inversie)
    bwb_pv_o_mv_lv    Gisteren stuurde Noor de juf een kaartje.
    vraag_pv_o_lv     Leest de juf een boek?
    o_pv_lv_vd        Opa heeft een taart gebakken.              (de pv is het hulpwerkwoord)
    o_pv_mv_lv_vd     Mama heeft de kinderen een verhaal verteld.
    o_pv_nwg          De kat is heel moe.                        (naamwoordelijk gezegde)
    o_pv_lv_bwb       Tom zoekt een sleutel in de tuin.
    o_pv_lv_aan_mv    De juf geeft een boek aan de kinderen.     (meewerkend voorwerp met aan/voor)
"""

import json
import random
from functools import lru_cache
from pathlib import Path

from .zinnen import BREEDTE, Deel, LT, Woord, Zin, breedte, controleer

PAD = Path(__file__).resolve().parent.parent.parent / "inhoud" / "taal" / "woorden.json"

ZINSBOUW = ("o_pv", "o_pv_lv", "o_pv_mv_lv", "bwb_pv_o_lv", "bwb_pv_o_mv_lv", "vraag_pv_o_lv",
            "o_pv_lv_vd", "o_pv_mv_lv_vd", "o_pv_nwg", "o_pv_lv_bwb", "o_pv_lv_aan_mv")
# zinnen met twee persoonsvormen (0.25.1): alleen de pv's en hun onderwerp zijn aangeduid (zinnen.deelzinnen)
#    twee_en            De juf leest een boek en de kinderen spelen.
#    twee_samen         Tom zoekt een sleutel en vindt een bal.          (de twee pv's delen het onderwerp)
#    twee_dat           Oma ziet dat de hond een bal zoekt.              (in de bijzin staat de pv achteraan)
#    twee_terwijl       Papa bakt een taart terwijl de kinderen spelen.
#    twee_terwijl_voor  Terwijl de kinderen spelen, bakt papa een taart. (de bijzin vooraan: dan pv vóór o)
SAMENGESTELD = ("twee_en", "twee_samen", "twee_dat", "twee_terwijl", "twee_terwijl_voor")
KORT = ("vallen", "vertrekken", "vinden")  # duurt maar een ogenblik: niet in een bijzin met terwijl
TELWOORDEN = ("twee", "drie", "vier", "vijf")


class Opnieuw(Exception):
    """Deze keuze past niet (bv. een werkwoord zonder meewerkend voorwerp): opnieuw proberen."""


@lru_cache(maxsize=None)
def lijst():
    return json.loads(PAD.read_text(encoding="utf-8"))


def groep(tekst):
    """'de/lidw juf/zn' → [Woord('de', 'lidw'), Woord('juf', 'zn')]."""
    uit = []
    for stuk in tekst.split():
        woord, _, soort = stuk.partition("/")
        uit.append(Woord(woord, soort or None))
    return uit


def woordsoorten():
    """{woord (kleine letters): woordsoort} uit de woordenlijst (voor zinnen met haakjes zonder /soort)."""
    L = lijst()
    uit = {}

    def zet(woord, soort):
        uit.setdefault(woord.lower(), soort)
    for soort in ("onderwerpen",):
        for items in L[soort].values():
            for item in items:
                for w in groep(item["tekst"]):
                    zet(w.tekst, w.soort)
    for tekst in [*L["meewerkend"], *L["personen_lv"], *L["naamwoordelijk"], *(b["tekst"] for b in L["bepalingen"])]:
        for w in groep(tekst):
            zet(w.tekst, w.soort)
    for items in L["dingen"].values():
        for d in items:
            zet(d["zn"], "zn")
            if d["mv"]:
                zet(d["mv"], "zn")
    for basis, met_e in L["bn"].items():
        zet(basis, "bn")
        zet(met_e, "bn")
    for ww in [*L["werkwoorden"], *L["koppelwerkwoorden"], *L["zegwerkwoorden"]]:
        for vorm in [ww["inf"], *ww["tt"], *ww["vt"], ww.get("vd", ww["inf"])]:
            zet(vorm, "ww")
    for hulp in L["hulpwerkwoorden"].values():
        for vorm in [*hulp["tt"], *hulp["vt"]]:
            zet(vorm, "ww")
    for w in ("de", "het", "een"):
        zet(w, "lidw")
    for w in TELWOORDEN:
        zet(w, "telw")
    for w in ("aan", "voor", "in", "op", "na", "om", "onder", "naar", "met", "van", "door", "bij", "uit", "over",
              "tegen", "achter", "naast", "tussen", "boven"):
        zet(w, "vz")
    for w in ("en", "dat", "terwijl", "maar", "want", "omdat", "als", "wanneer", "toen", "of"):
        zet(w, "vw")
    return uit


def soort_van(woord):
    """De woordsoort van een woord volgens de woordenlijst (hoofdletters maken niet uit), of None."""
    return _soorten().get(woord.lower())


@lru_cache(maxsize=None)
def _soorten():
    return woordsoorten()


# ---- woordgroepen ---------------------------------------------------------------------

def ding_groep(d, rng, meervoud_mag=True):
    """Een lijdend voorwerp met een ding: een boek, het dikke boek, twee nieuwe fietsen …"""
    bn = lijst()["bn"]
    vorm = rng.choice(["een", "een", "bepaald", "bn", "meervoud"] if meervoud_mag and d["mv"] else
                      ["een", "een", "bepaald", "bn"])
    if vorm == "een":
        return [Woord("een", "lidw"), Woord(d["zn"], "zn")]
    if vorm == "bepaald":
        return [Woord(d["lidw"], "lidw"), Woord(d["zn"], "zn")]
    b = rng.choice(d["bn"])
    if vorm == "bn":
        if rng.random() < 0.5:  # het dikke boek
            return [Woord(d["lidw"], "lidw"), Woord(bn[b], "bn"), Woord(d["zn"], "zn")]
        # een dik boek (het-woord: zonder -e), een rode bal
        return [Woord("een", "lidw"), Woord(b if d["lidw"] == "het" else bn[b], "bn"), Woord(d["zn"], "zn")]
    if rng.random() < 0.5:
        return [Woord(rng.choice(TELWOORDEN), "telw"), Woord(d["mv"], "zn")]
    return [Woord(rng.choice(TELWOORDEN), "telw"), Woord(bn[b], "bn"), Woord(d["mv"], "zn")]


def lv_groep(ww, rng):
    """(woorden, wie?) voor het lijdend voorwerp van dit werkwoord."""
    L = lijst()
    cat = rng.choice(ww["lv"])
    if cat == "personen":
        return groep(rng.choice(L["personen_lv"])), True
    return ding_groep(rng.choice(L["dingen"][cat]), rng), False


# ---- de zin bouwen --------------------------------------------------------------------

class Bouwer:
    """Bouwt een zin stuk per stuk: elk stuk = woorden + de labels van het zinsdeel."""

    def __init__(self):
        self.woorden, self.delen, self.gezegde = [], [], []

    def voeg(self, woorden, *labels):
        posities = tuple(range(len(self.woorden), len(self.woorden) + len(woorden)))
        self.woorden += woorden
        for label in labels:
            if label == "wwg":
                self.gezegde += list(posities)
            elif label == "nwg":
                self.gezegde += list(posities)
                self.nwg = True
            else:
                self.delen.append(Deel(label, posities))
        return posities

    def los(self, woorden):
        """Woorden zonder zinsdeel (in een zin met twee pv's is alleen pv en o aangeduid)."""
        self.woorden += woorden

    def grens(self):
        """Hier begint een nieuwe deelzin."""
        self.grenzen = [*getattr(self, "grenzen", []), len(self.woorden)]

    def zin(self, leesteken, data):
        self.woorden.append(Woord(leesteken, LT))
        if getattr(self, "grenzen", None) or len([d for d in self.delen if d.label == "pv"]) > 1:
            data = {**data, "grenzen": list(getattr(self, "grenzen", [])), "eerste": self.woorden[0].tekst}
            return Zin(_hoofdletter(self.woorden), list(self.delen), data)
        label = "nwg" if getattr(self, "nwg", False) else "wwg"
        delen = self.delen + [Deel(label, tuple(sorted(self.gezegde)))]
        data = {**data, "eerste": self.woorden[0].tekst}  # zoals in de woordenlijst (papa, Lotte): voor de proefjes
        return Zin(_hoofdletter(self.woorden), delen, data)


def _hoofdletter(woorden):
    """Het eerste woord met een hoofdletter; namen houden hun hoofdletter."""
    w = woorden[0]
    return [Woord(w.tekst[0].upper() + w.tekst[1:], w.soort), *woorden[1:]]


def kies_ww(rng, nodig_lv=False, nodig_mv=False, zonder_lv=False, lv_weglaten=True):
    """Een werkwoord dat bij de zinsbouw past. zonder_lv = een zin zonder lijdend voorwerp; lv_weglaten = dan mag ook
    een werkwoord dat gewoonlijk een lv heeft ("Oma eet."): alleen op Moeilijk en hoger (de vader, 7/11)."""
    kandidaten = [w for w in lijst()["werkwoorden"]
                  if (not nodig_lv or w.get("lv")) and (nodig_mv if w.get("mv_nodig") else (not nodig_mv or w.get("mv")))
                  and (not zonder_lv or not w.get("lv") or (lv_weglaten and w.get("zonder_lv")))]
    return rng.choice(kandidaten)


def kies_o(ww, rng):
    """(woorden, getal) van een onderwerp dat bij het werkwoord past."""
    L = lijst()
    soort = rng.choice(ww["o"])
    item = rng.choice(L["onderwerpen"][soort])
    return groep(item["tekst"]), item["getal"]


def kies_bwb(rng, tijd, plek="voor"):
    """Een bijwoordelijke bepaling die bij de tijd past (gisteren + vt, morgen + tt …)."""
    opties = [b for b in lijst()["bepalingen"] if b["tijd"] in (None, tijd) and b["plek"] in (plek, "beide")]
    return groep(rng.choice(opties)["tekst"])


def mv_groep(rng):
    return groep(rng.choice(lijst()["meewerkend"]))


def maak(zinsbouw, rng=random, tijden=("tt", "vt"), max_woorden=None, lv_weglaten=True):
    """Een volledig ontlede Zin met deze zinsbouw. Probeert opnieuw als een keuze niet past, de zin te breed is voor het
    scherm of meer woorden heeft dan max_woorden (de leerlijn; zonder het leesteken)."""
    if zinsbouw not in ZINSBOUW:
        raise ValueError(f"onbekende zinsbouw '{zinsbouw}'")
    for _ in range(200):
        try:
            zin = _maak(zinsbouw, rng, rng.choice(list(tijden)), lv_weglaten)
        except Opnieuw:
            continue
        lang = max_woorden is not None and sum(not w.leesteken for w in zin.woorden) > max_woorden
        if not controleer(zin) and breedte(zin) <= BREEDTE and not lang:
            return zin
    raise RuntimeError(f"geen zin gevonden voor '{zinsbouw}'")


def _maak(zinsbouw, rng, tijd, lv_weglaten=True):
    delen = zinsbouw.split("_")
    met_lv = "lv" in delen
    met_mv = "mv" in delen
    vd = "vd" in delen
    if "nwg" in delen:
        return _maak_nwg(rng, tijd)
    ww = kies_ww(rng, nodig_lv=met_lv, nodig_mv=met_mv, zonder_lv=not met_lv, lv_weglaten=lv_weglaten)
    o, getal = kies_o(ww, rng)
    g = 0 if getal == "ev" else 1
    if vd:
        hulp = lijst()["hulpwerkwoorden"][ww["hulp"]]
        pv = Woord(hulp[tijd][g], "ww")
        anders = hulp["vt" if tijd == "tt" else "tt"][g]
    else:
        pv = Woord(ww[tijd][g], "ww")
        anders = ww["vt" if tijd == "tt" else "tt"][g]
    data = {"zinsbouw": zinsbouw, "ww": ww["inf"], "tijd": tijd, "getal": getal, "pv_andere_tijd": anders,
            "mv_vz": ww.get("mv")}
    lv, lv_wie = lv_groep(ww, rng) if met_lv else (None, False)
    data["lv_wie"] = lv_wie
    mv = mv_groep(rng) if met_mv else None
    if met_mv and lv and _zelfde(lv, mv):
        raise Opnieuw()
    if _zelfde(o, mv) or _zelfde(o, lv):
        raise Opnieuw()
    b = Bouwer()
    if delen[0] == "bwb":  # inversie: bwb pv o …
        b.voeg(kies_bwb(rng, tijd), "bwb")
        b.voeg([pv], "pv", "wwg")
        b.voeg(o, "o")
    elif delen[0] == "vraag":
        b.voeg([pv], "pv", "wwg")
        b.voeg(o, "o")
    else:
        b.voeg(o, "o")
        b.voeg([pv], "pv", "wwg")
    if "aan" in delen:
        b.voeg(lv, "lv")
        if not ww.get("mv"):
            raise Opnieuw()
        b.voeg([Woord(ww["mv"], "vz"), *mv], "mv")
    else:
        if met_mv:
            b.voeg(mv, "mv")
        if met_lv:
            b.voeg(lv, "lv")
    if delen[-1] == "bwb":
        b.voeg(kies_bwb(rng, tijd, plek="na"), "bwb")
    if vd:
        b.voeg([Woord(ww["vd"], "ww")], "wwg")
    return b.zin("?" if delen[0] == "vraag" else ".", data)


# ---- zinnen met twee persoonsvormen ----------------------------------------------------

def maak_samengesteld(zinsbouw, rng=random, tijden=("tt", "vt")):
    """Een zin met twee pv's (alleen pv en o aangeduid). Probeert opnieuw als de zin te breed is voor het scherm."""
    if zinsbouw not in SAMENGESTELD:
        raise ValueError(f"onbekende zinsbouw '{zinsbouw}'")
    for _ in range(400):
        try:
            zin = _maak_samengesteld(zinsbouw, rng, rng.choice(list(tijden)))
        except Opnieuw:
            continue
        if not controleer(zin) and breedte(zin) <= BREEDTE:
            return zin
    raise RuntimeError(f"geen zin gevonden voor '{zinsbouw}'")


def _deelzin(rng, tijd, soort=None, niet=()):
    """Eén deelzin: (onderwerp, pv, de rest (een lijdend voorwerp of niets), het werkwoord, de soort van het
    onderwerp). soort = het onderwerp moet van die soort zijn (een gedeeld onderwerp); niet = deze werkwoorden niet."""
    met_lv = rng.random() < 0.6
    ww = kies_ww(rng, nodig_lv=met_lv, zonder_lv=not met_lv, lv_weglaten=False)
    if ww["inf"] in niet or (soort and soort not in ww["o"]):
        raise Opnieuw()
    soort = soort or rng.choice(ww["o"])
    item = rng.choice(lijst()["onderwerpen"][soort])
    g = 0 if item["getal"] == "ev" else 1
    rest = lv_groep(ww, rng)[0] if met_lv else []
    o = groep(item["tekst"])
    if _zelfde(o, rest):
        raise Opnieuw()
    return {"o": o, "pv": Woord(ww[tijd][g], "ww"), "rest": rest, "ww": ww, "soort": soort, "g": g}


def _maak_samengesteld(zinsbouw, rng, tijd):
    b = Bouwer()
    data = {"zinsbouw": zinsbouw, "tijd": tijd}
    een = _deelzin(rng, tijd)
    if zinsbouw == "twee_samen":  # o pv … en pv …: één onderwerp voor twee pv's
        ww2 = kies_ww(rng, nodig_lv=True)
        if ww2["inf"] == een["ww"]["inf"] or een["soort"] not in ww2["o"] or not een["rest"]:
            raise Opnieuw()  # (zonder lijdend voorwerp klinkt het vreemd: "Opa slaapt en schrijft een brief.")
        b.voeg(een["o"], "o")
        b.voeg([een["pv"]], "pv")
        b.los(een["rest"])
        b.los([Woord("en", "vw")])
        b.voeg([Woord(ww2[tijd][een["g"]], "ww")], "pv")
        b.los(lv_groep(ww2, rng)[0])
        return b.zin(".", data)
    if zinsbouw == "twee_dat":  # een mens zegt/ziet/denkt dat + een deelzin met de pv achteraan
        zeg = rng.choice(lijst()["zegwerkwoorden"])
        item = rng.choice(lijst()["onderwerpen"]["mens"])
        wie = groep(item["tekst"])
        if _zelfde(wie, een["o"]) or _zelfde(wie, een["rest"]):
            raise Opnieuw()
        b.voeg(wie, "o")
        b.voeg([Woord(zeg[tijd][0 if item["getal"] == "ev" else 1], "ww")], "pv")
        b.grens()
        b.los([Woord("dat", "vw")])
        b.voeg(een["o"], "o")
        b.los(een["rest"])
        b.voeg([een["pv"]], "pv")
        return b.zin(".", data)
    # terwijl + iets dat maar een ogenblik duurt klinkt vreemd ("terwijl de buren vielen")
    kort = () if zinsbouw == "twee_en" else KORT
    twee = _deelzin(rng, tijd, niet=(een["ww"]["inf"], *kort))
    if _zelfde(een["o"], twee["o"]) or _zelfde(een["o"], twee["rest"]) or _zelfde(twee["o"], een["rest"]) or \
            (een["rest"] and _zelfde(een["rest"], twee["rest"])):
        raise Opnieuw()
    if zinsbouw == "twee_en":
        for deel, voor in ((een, None), (twee, "en")):
            if voor:
                b.grens()
                b.los([Woord(voor, "vw")])
            b.voeg(deel["o"], "o")
            b.voeg([deel["pv"]], "pv")
            b.los(deel["rest"])
    elif zinsbouw == "twee_terwijl":
        b.voeg(een["o"], "o")
        b.voeg([een["pv"]], "pv")
        b.los(een["rest"])
        b.grens()
        b.los([Woord("terwijl", "vw")])
        b.voeg(twee["o"], "o")
        b.los(twee["rest"])
        b.voeg([twee["pv"]], "pv")
    else:  # twee_terwijl_voor: de bijzin vooraan, daarna de pv vóór het onderwerp
        b.los([Woord("terwijl", "vw")])
        b.voeg(twee["o"], "o")
        b.los(twee["rest"])
        b.voeg([twee["pv"]], "pv")
        b.los([Woord(",", LT)])
        b.grens()
        b.voeg([een["pv"]], "pv")
        b.voeg(een["o"], "o")
        b.los(een["rest"])
    return b.zin(".", data)


def _maak_nwg(rng, tijd):
    """o pv nwg: De kat is heel moe. (koppelwerkwoord + bijvoeglijk naamwoord)"""
    L = lijst()
    kw = rng.choice(L["koppelwerkwoorden"])
    soort = rng.choice(["mens", "dier", "hond"])
    item = rng.choice(L["onderwerpen"][soort])
    g = 0 if item["getal"] == "ev" else 1
    data = {"zinsbouw": "o_pv_nwg", "ww": kw["inf"], "tijd": tijd, "getal": item["getal"],
            "pv_andere_tijd": kw["vt" if tijd == "tt" else "tt"][g], "mv_vz": None, "lv_wie": False}
    b = Bouwer()
    b.voeg(groep(item["tekst"]), "o")
    b.voeg([Woord(kw[tijd][g], "ww")], "pv", "nwg")
    b.voeg(groep(rng.choice(L["naamwoordelijk"])), "nwg")
    return b.zin(".", data)


def _zelfde(a, b):
    return a is not None and b is not None and [w.tekst.lower() for w in a] == [w.tekst.lower() for w in b]
