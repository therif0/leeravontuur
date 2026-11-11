"""Werkwoordspelling (T3, 0.26): de werkwoordenlijst, de zin met een gat, het denkschema in stappen, het nakijken, de
denkfouten, de tips, de uitleg en de spiekbrieven. Zonder curses.

De vader (10/11, docs/taal.md): stap voor stap zoals bij Zinsdelen (Tab = meteen typen; Moeilijk typt meteen), het
ezelsbruggetje is 't kofschip. Elke vorm staat uitgeschreven in inhoud/taal/werkwoorden.json; de regels hieronder
rekenen de zwakke vormen na (tests) en leggen ze uit, maar het antwoord komt altijd uit de lijst.

Een vraag is een `WwZin`: een zin met een gat en het werkwoord tussen haakjes ("Gisteren ___ Noor in het park.
(fietsen)"). De stappen (`stappen`) zijn data: een keuze of een woord typen; de laatste stap is altijd de vorm.
"""

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PAD = Path(__file__).resolve().parent.parent.parent / "inhoud" / "taal" / "werkwoorden.json"
KOFSCHIP = "'t kofschip"
KOF_LETTERS = "tkfschpx"   # de medeklinkers van 't kofschip (en de x van faxen)
BREED = 66                 # zo lang mag de zin met het gat zijn (naast het maatje is er minder plaats: zie het scherm)
GAT = "___"

DENKFOUTEN = {
    "ws_onderwerp": "het onderwerp niet juist gezien (wie doet het, één of meer)",
    "ws_stam_vz": "een v of z in de stam geschreven (leev, reiz) in plaats van f of s",
    "ws_stam_klinker": "de lange klank van de stam met één klinker geschreven (lop in plaats van loop)",
    "ws_stam_dubbel": "de stam met twee dezelfde medeklinkers aan het einde geschreven (pakk)",
    "ws_stam": "de stam (de ik-vorm) niet juist",
    "ws_t_vergeten": "de t na de stam vergeten (hij word, jij loop)",
    "ws_t_te_veel": "een t geschreven waar alleen de stam hoort (ik wordt)",
    "ws_inversie": "een t geschreven terwijl jij achter het werkwoord staat (wordt jij)",
    "ws_dubbele_t": "een woord op tt laten eindigen (hij praatt)",
    "ws_getal": "enkelvoud en meervoud verwisseld",
    "ws_tijd": "de verkeerde tijd geschreven",
    "ws_kofschip": "-te en -de verwisseld ('t kofschip)",
    "ws_kofschip_vz": "naar de stam gekeken in plaats van naar de letter vóór -en (leefte, reiste)",
    "ws_dubbel": "de dubbele t of d van de verleden tijd vergeten (praate, antwoorde)",
    "ws_regel": "de regel voor de uitgang niet juist gekozen",
}


@lru_cache(maxsize=None)
def lijst():
    return json.loads(PAD.read_text(encoding="utf-8"))["werkwoorden"]


@lru_cache(maxsize=None)
def _op_inf():
    return {w["inf"]: w for w in lijst()}


def ww(inf):
    """Het werkwoord uit de lijst (een dict), of None."""
    return _op_inf().get(inf)


# ---- de regels (voor de uitleg en om de lijst na te rekenen) ----------------------------------------------------

def ruw(inf):
    """Het werkwoord zonder -en (of -n): werk, lev, reiz, prat. Naar de laatste letter hiervan kijkt 't kofschip."""
    return inf[:-2] if inf.endswith("en") else inf[:-1]


def letter(inf):
    """De letter(s) waar 't kofschip naar kijkt: de laatste letter vóór -en (ch telt als één klank)."""
    r = ruw(inf)
    return "ch" if r.endswith("ch") else r[-1]


def in_kofschip(inf):
    return ruw(inf)[-1] in KOF_LETTERS


def regel_tt(w):
    """[ik, jij, hij, meervoud] volgens de regel stam + t (geen tweede t na een stam op t)."""
    stam = w["stam"]
    t = stam if stam.endswith("t") else stam + "t"
    return [stam, t, t, w["inf"]]


def regel_vt(w):
    """[enkelvoud, meervoud] van een zwak werkwoord: stam + te(n) of de(n)."""
    uitgang = "te" if in_kofschip(w["inf"]) else "de"
    return [w["stam"] + uitgang, w["stam"] + uitgang + "n"]


def regel_vd(w):
    """Het voltooid deelwoord van een zwak werkwoord: (ge) + stam + t of d (geen tweede t of d)."""
    eind = "t" if in_kofschip(w["inf"]) else "d"
    return ("ge" if w["ge"] else "") + w["stam"] + ("" if w["stam"].endswith(eind) else eind)


def stamsoort(w):
    """Wat de stam lastig maakt: "t" of "d" (de stam eindigt erop), "vz" (v of z vóór -en), anders "gewoon"."""
    if ruw(w["inf"])[-1] in "vz":
        return "vz"
    return w["stam"][-1] if w["stam"][-1] in "td" else "gewoon"


def _klinker(w):
    """Krijgt de stam een dubbele klinker die het werkwoord niet heeft (lopen → loop)?"""
    return any(d in w["stam"] and d not in w["inf"] for d in ("aa", "ee", "oo", "uu"))


def _dubbel(w):
    """Verliest de stam een dubbele medeklinker (pakken → pak)?"""
    r = ruw(w["inf"])
    return len(r) > 1 and r[-1] == r[-2] and w["stam"] == r[:-1]


# ---- de zin met het gat ------------------------------------------------------------------------------------------

# (tekst, persoon): ik, jij, hij (= hij, zij, het of één naam), mv. Geen zij of ze: dat kan één of meer zijn, en dan
# zou het gat twee juiste antwoorden hebben.
MENSEN = (("ik", "ik"), ("jij", "jij"), ("hij", "hij"), ("de juf", "hij"), ("mijn broer", "hij"), ("Noor", "hij"),
          ("opa", "hij"), ("onze buurman", "hij"), ("Sami", "hij"), ("mijn zus", "hij"), ("we", "mv"),
          ("jullie", "mv"), ("de kinderen", "mv"), ("mijn ouders", "mv"), ("de buren", "mv"),
          ("Lotte en Noor", "mv"))
PERSONEN = ("ik", "jij", "jij_inv", "hij", "mv")  # jij_inv = jij achter het werkwoord (dan valt de t weg)
PATRONEN = ("gewoon", "inversie", "vraag")
TT_WOORDEN = ("vandaag", "nu", "elke dag")
VT_WOORDEN = ("gisteren", "vorige week", "toen")
VROEGER = ("vroeger", "toen", "vorig jaar")
WIE = {"ik": "ik", "jij": "jij", "jij_inv": "jij", "hij": "hij, zij, het of één naam", "mv": "meer dan één"}


@dataclass(frozen=True)
class WwZin:
    voor: str      # wat vóór het gat staat ("Gisteren"; leeg bij een vraag)
    na: str        # wat na het gat staat ("Noor in het park.")
    inf: str       # het werkwoord tussen haakjes
    vorm: str      # "tt" of "vt" (later ook "vd")
    persoon: str   # zie PERSONEN
    o: str         # het onderwerp zoals het in de zin staat
    antwoord: str
    patroon: str = "gewoon"

    @property
    def zin(self):
        """De zin met het gat: "Gisteren ___ Noor in het park." """
        return _plak(self.voor, GAT, self.na)

    @property
    def tekst(self):
        return f"{self.zin} ({self.inf})"

    def vol(self, vorm=None):
        """De zin met de vorm ingevuld (met een hoofdletter als de zin ermee begint)."""
        vorm = self.antwoord if vorm is None else vorm
        return _plak(self.voor, vorm if self.voor else vorm[:1].upper() + vorm[1:], self.na)

    @property
    def ww(self):
        return ww(self.inf)

    @property
    def meervoud(self):
        return self.persoon == "mv"


def _plak(voor, midden, na):
    uit = f"{voor} {midden}".strip()
    return uit + na if na[:1] in ".?!," else f"{uit} {na}"


def _hoofd(tekst):
    return tekst[:1].upper() + tekst[1:]


def vorm_van(w, vorm, persoon):
    """De juiste vorm uit de lijst."""
    if vorm == "tt":
        return w["tt"][{"ik": 0, "jij": 1, "jij_inv": 0, "hij": 2, "mv": 3}[persoon]]
    if vorm == "vt":
        return w["vt"][1 if persoon == "mv" else 0]
    return w["vd"]


def maak_zin(w, vorm, rng=random, personen=PERSONEN, patronen=PATRONEN):
    """Een zin met een gat voor dit werkwoord. personen en patronen: wat het leerjaar toelaat. Geeft None als er met
    deze keuzes geen zin kan (bv. een werkwoord met eigen onderwerpen en alleen "ik" gevraagd)."""
    onderwerpen = [tuple(o) for o in w["o"]] if w.get("o") else MENSEN
    kandidaten = []
    for o, persoon in onderwerpen:
        for patroon in patronen:
            p = "jij_inv" if persoon == "jij" and patroon != "gewoon" else persoon
            if p in personen and not (patroon == "vraag" and persoon == "ik"):
                kandidaten.append((o, p, patroon))
    if not kandidaten:
        return None
    # elke persoon even vaak (er zijn meer namen dan "ik" en "jij")
    persoon = rng.choice(sorted({k[1] for k in kandidaten}))
    o, persoon, patroon = rng.choice([k for k in kandidaten if k[1] == persoon])
    rest = rng.choice(w["rest"])
    if vorm == "vt":
        tijd = rng.choice(VROEGER if w.get("vroeger") else VT_WOORDEN)
    else:
        tijd = rng.choice(TT_WOORDEN) if patroon == "inversie" or rng.random() < 0.3 else ""
    if patroon == "inversie":
        voor, na = _hoofd(tijd), f"{o} {rest}."
    elif patroon == "vraag":
        voor, na = "", f"{o} {tijd + ' ' if tijd else ''}{rest}?"
    else:
        voor, na = _hoofd(o), f"{tijd + ' ' if tijd else ''}{rest}."
    return WwZin(voor, na, w["inf"], vorm, persoon, o, vorm_van(w, vorm, persoon), patroon)


def nakijken(zin, getypt):
    """Is de getypte vorm juist? Hoofdletters tellen niet; "rij" naast "rijd" mag (de lijst: ook)."""
    getypt = (getypt or "").strip().lower()
    if getypt == zin.antwoord.lower():
        return True
    return zin.vorm == "tt" and zin.persoon in ("ik", "jij_inv") and getypt in zin.ww.get("ook", ())


# ---- het denkschema in stappen -----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Stap:
    naam: str             # "wie", "getal", "stam", "regel", "kofschip", "vorm"
    soort: str            # "keuze" (kies een van de opties) of "typ" (typ een woord)
    vraag: str
    opties: tuple = ()    # keuze: de teksten, in de volgorde van de cijfertoetsen
    juist: object = None  # keuze: het nummer van de juiste optie (vanaf 0); typ: de goede antwoorden (kleine letters)
    uitleg: str = ""      # het juiste antwoord met de reden (na de tweede kans en in de uitleg achteraf)
    tips: tuple = ()
    voor: str = ""        # typ: wat vóór het vakje staat ("ik")
    kofschip: str = ""    # deze letter licht op in 't kofschip zodra de stap klaar is
    kop: str = ""         # het kopje op de spiekbrief bij deze stap


TT_REGEL = ("de stam", "de stam + t", "het hele werkwoord")
TT_KEUZE = {"ik": 0, "jij": 1, "jij_inv": 0, "hij": 1, "mv": 2}
TT_WAAROM = {
    "ik": "Bij ik schrijf je alleen de stam.",
    "jij": "Jij staat vóór het werkwoord: de stam + t.",
    "jij_inv": "Jij staat achter het werkwoord: alleen de stam, zonder t.",
    "hij": "Bij hij, zij, het of één naam: de stam + t.",
    "mv": "Het onderwerp is meer dan één: het hele werkwoord.",
}


def _stam_stap(zin):
    w = zin.ww
    if _klinker(w):
        waarom = " (een lange klank: twee klinkers)"
        tip = "Zeg het hardop: ik … Hoor je een lange klank? Dan schrijf je twee klinkers."
    elif _dubbel(w):
        waarom = " (nooit twee dezelfde medeklinkers aan het einde)"
        tip = "Een stam eindigt nooit op twee dezelfde medeklinkers."
    else:
        waarom, tip = "", f"Haal -en van ‘{zin.inf}’ af en zeg: ik …"
    if stamsoort(w) == "vz":
        waarom = " (een stam eindigt nooit op v of z)"
        tip = "Een stam eindigt nooit op v of z: je schrijft f of s."
    return Stap("stam", "typ", f"Typ de stam (de ik-vorm) van ‘{zin.inf}’.", juist=(w["stam"], *w.get("ook", ())),
                uitleg=f"De stam van ‘{zin.inf}’ is ‘{w['stam']}’{waarom}.", voor="ik",
                tips=("De stam is de ik-vorm: ik …", tip), kop=KOP["stam"])


def _vorm_stap(zin, direct):
    if zin.vorm == "tt":
        tips = ("Wie doet het? Zoek het onderwerp en de stam (de ik-vorm).",
                "Ik: de stam. Jij, hij, zij, het of één naam: de stam + t. Meer dan één: het hele werkwoord. "
                "Staat jij achter het werkwoord? Dan valt de t weg.")
        kop = KOP["wie"]
    else:
        tips = ("Zoek de stam. Kijk dan naar de letter vóór -en: zit die in 't kofschip?",
                "'t Kofschip (t, k, f, s, ch, p): -te of -ten. Anders: -de of -den. Is het onderwerp één of meer?")
        kop = KOP["kofschip"]
    vraag = f"Typ de juiste vorm van ‘{zin.inf}’." if direct else "Typ nu de vorm in de zin."
    return Stap("vorm", "typ", vraag, juist=(zin.antwoord.lower(),), uitleg=f"In de zin komt ‘{zin.antwoord}’.",
                tips=tips, kop=kop)


def stappen(zin, stap_voor_stap=True):
    """De stappen van het denkschema voor deze zin; de laatste is altijd het typen van de vorm. Zonder stap_voor_stap
    (Tab, of Moeilijk) is er alleen die laatste stap. Een onregelmatig werkwoord (zijn, hebben) heeft geen regel:
    dan ook alleen de vorm."""
    w = zin.ww
    if not stap_voor_stap or (zin.vorm == "tt" and w.get("onregelmatig")):
        return [_vorm_stap(zin, True)]
    zoek = ("Zoek het onderwerp: wie of wat doet het?", "Het onderwerp staat vlak voor of vlak na het gat.")
    if zin.vorm == "tt":
        wie = ("ik", "jij", "hij, zij, het of één naam", "meer dan één")
        nr = {"ik": 0, "jij": 1, "jij_inv": 1, "hij": 2, "mv": 3}[zin.persoon]
        regel_tip = ("Kijk waar ‘jij’ staat: voor of achter het werkwoord?" if zin.persoon == "jij_inv" else
                     "Kijk nog eens wie het doet.")
        return [
            Stap("wie", "keuze", "Wie doet het?", wie, nr, f"Het onderwerp is ‘{zin.o}’: {wie[nr]}.", zoek,
                 kop=KOP["wie"]),
            _stam_stap(zin),
            Stap("regel", "keuze", "Wat schrijf je?", TT_REGEL, TT_KEUZE[zin.persoon], TT_WAAROM[zin.persoon],
                 ("Ik: de stam. Jij, hij, zij, het: de stam + t. Meer dan één: het hele werkwoord.", regel_tip),
                 kop=KOP["wie"]),
            _vorm_stap(zin, False),
        ]
    kof, lt = in_kofschip(zin.inf), letter(zin.inf)
    n = "n" if zin.meervoud else ""
    return [
        Stap("getal", "keuze", "Is het onderwerp één, of meer dan één?", ("één", "meer dan één"),
             1 if zin.meervoud else 0, f"Het onderwerp is ‘{zin.o}’: {'meer dan één' if zin.meervoud else 'één'}.",
             zoek, kop=KOP["getal"]),
        _stam_stap(zin),
        Stap("kofschip", "keuze", f"Zonder -en: ‘{ruw(zin.inf)}’. Zit de {lt} in {KOFSCHIP}?",
             ("ja: -te of -ten", "nee: -de of -den"), 0 if kof else 1,
             f"‘{ruw(zin.inf)}’ eindigt op {lt}: die zit {'wel' if kof else 'niet'} in {KOFSCHIP}, dus "
             f"-{'te' if kof else 'de'}{n}.",
             ("Neem het werkwoord zonder -en en kijk naar de laatste letter.",
              "De letters van 't kofschip: t, k, f, s, ch, p. Staat de letter erbij: -te. Anders: -de."),
             kofschip=lt, kop=KOP["kofschip"]),
        _vorm_stap(zin, False),
    ]


def nakijken_stap(stap, antwoord):
    """Is het antwoord op deze stap juist? keuze: het nummer van de optie; typ: het getypte woord."""
    if stap.soort == "keuze":
        return antwoord == stap.juist
    return (antwoord or "").strip().lower() in stap.juist


def diagnose_stap(zin, stap, antwoord):
    """(code, wat het programma zegt) bij een fout antwoord op een stap, of None. Zegt het antwoord niet."""
    if nakijken_stap(stap, antwoord):
        return None
    if stap.naam == "vorm":
        return diagnose_vorm(zin, antwoord)
    w = zin.ww
    if stap.naam in ("wie", "getal"):
        return "ws_onderwerp", "Zoek het onderwerp: wie of wat doet het? Kijk vlak voor en vlak na het gat."
    if stap.naam == "stam":
        getypt = (antwoord or "").strip().lower()
        if getypt == w["inf"]:
            return "ws_stam", "Dat is het hele werkwoord. De stam is de ik-vorm: ik …"
        if getypt == w["stam"] + "t" and not w["stam"].endswith("t"):
            return "ws_stam", "Dat is de vorm bij hij. De stam is de ik-vorm, zonder t."
        if stamsoort(w) == "vz" and getypt[-1:] in ("v", "z"):
            return "ws_stam_vz", "Een stam eindigt nooit op v of z: schrijf f of s."
        if _klinker(w) and getypt == ruw(w["inf"]):
            return "ws_stam_klinker", "Zeg het hardop: ik … Je hoort een lange klank: schrijf twee klinkers."
        if _dubbel(w) and getypt == ruw(w["inf"]):
            return "ws_stam_dubbel", "Een stam eindigt nooit op twee dezelfde medeklinkers."
        return "ws_stam", "De stam is de ik-vorm. Zeg het hardop: ik …"
    if stap.naam == "regel":
        if zin.persoon == "jij_inv" and antwoord == 1:
            return "ws_inversie", "Kijk waar ‘jij’ staat: voor of achter het werkwoord?"
        return "ws_regel", "Ik: de stam. Jij, hij, zij, het: de stam + t. Meer dan één: het hele werkwoord."
    if stap.naam == "kofschip":
        if stamsoort(w) == "vz":
            return "ws_kofschip_vz", (f"Kijk naar het werkwoord zonder -en (‘{ruw(zin.inf)}’), niet naar de stam: "
                                      f"zit de {letter(zin.inf)} in {KOFSCHIP}?")
        return "ws_kofschip", f"De letters van {KOFSCHIP} zijn t, k, f, s, ch en p. Staat de {letter(zin.inf)} erbij?"
    return None


def diagnose_vorm(zin, getypt):
    """(code, wat het programma zegt) bij een fout getypte vorm, of None als de fout niet herkend is."""
    getypt = (getypt or "").strip().lower()
    if not getypt or nakijken(zin, getypt):
        return None
    w, juist = zin.ww, zin.antwoord.lower()
    stam, soort = w["stam"], stamsoort(w)
    andere_tijd = {v.lower() for v in (w["vt"] if zin.vorm == "tt" else w["tt"])}
    if getypt in andere_tijd and getypt not in (w["tt"] if zin.vorm == "tt" else w["vt"]):
        if zin.vorm == "tt":
            return "ws_tijd", "Dat is de verleden tijd. De zin staat in de tegenwoordige tijd."
        return "ws_tijd", "Dat is de tegenwoordige tijd. De zin speelt in het verleden."
    if zin.vorm == "tt":
        if getypt.endswith("tt"):
            return "ws_dubbele_t", "Een woord eindigt nooit op tt: de stam eindigt al op t."
        if getypt == w["inf"] or (zin.meervoud and getypt in w["tt"][:3]):
            return "ws_getal", "Kijk naar het onderwerp: is het één, of meer dan één?"
        if juist == stam and getypt == stam + "t":
            if zin.persoon == "jij_inv":
                return "ws_inversie", "Jij staat achter het werkwoord: dan valt de t weg."
            return "ws_t_te_veel", "Bij ik schrijf je alleen de stam, zonder t."
        if juist != stam and getypt == stam:
            if stam.endswith("d"):
                return "ws_t_vergeten", "De stam eindigt op d, en bij dit onderwerp komt er nog een t bij."
            return "ws_t_vergeten", "Bij dit onderwerp komt er een t achter de stam."
        if stam.endswith("d") and getypt == stam[:-1] + "t":
            return "ws_t_vergeten", "De d van de stam blijft staan. Zeg het hele werkwoord: je hoort de d."
        if soort == "vz" and ruw(w["inf"]) in getypt:
            return "ws_stam_vz", "Schrijf eerst de stam: die eindigt nooit op v of z."
        if _klinker(w) and getypt.startswith(ruw(w["inf"])):
            return "ws_stam_klinker", "Zeg de stam hardop: je hoort een lange klank. Schrijf twee klinkers."
        return None
    # de verleden tijd van een zwak werkwoord
    te, de = stam + "te", stam + "de"
    if getypt in (te, te + "n", de, de + "n"):
        if getypt.endswith("n") != juist.endswith("n"):
            return "ws_getal", "Kijk naar het onderwerp: is het één, of meer dan één?"
        if soort == "vz":
            return "ws_kofschip_vz", (f"Kijk naar het werkwoord zonder -en (‘{ruw(zin.inf)}’), niet naar de stam: "
                                      f"de {letter(zin.inf)} zit niet in {KOFSCHIP}.")
        return "ws_kofschip", f"Kijk naar de letter vóór -en: zit de {letter(zin.inf)} in {KOFSCHIP}?"
    if soort in ("t", "d") and getypt in (stam + "e", stam + "en"):
        return "ws_dubbel", (f"De stam eindigt al op {soort}, en dan komt er nog -{soort}e bij: twee keer dezelfde "
                             "letter.")
    if soort == "vz" and getypt.startswith(ruw(w["inf"])):
        return "ws_stam_vz", "Schrijf eerst de stam: die eindigt op f of s. Daarna komt de uitgang."
    if _klinker(w) and getypt.startswith(ruw(w["inf"])) and not getypt.startswith(stam):
        return "ws_stam_klinker", "Schrijf eerst de stam: je hoort een lange klank, dus twee klinkers."
    if _dubbel(w) and getypt.startswith(ruw(w["inf"])):
        return "ws_stam_dubbel", "Schrijf eerst de stam: die eindigt nooit op twee dezelfde medeklinkers."
    return None


def uitleg(zin):
    """Na het nakijken: het denkschema voor deze zin, regel per regel, met de vorm op het einde."""
    w = zin.ww
    if zin.vorm == "tt" and w.get("onregelmatig"):
        tt = w["tt"]
        return [f"‘{zin.inf}’ is onregelmatig: ik {tt[0]}, jij {tt[1]}, hij {tt[2]}, wij {tt[3]}.",
                f"Het onderwerp is ‘{zin.o}’, dus: {zin.antwoord}."]
    regels = [s.uitleg for s in stappen(zin)[:-1]]
    if zin.vorm == "tt" and w["stam"].endswith("t") and TT_KEUZE[zin.persoon] == 1:
        regels.append("De stam eindigt al op t: er komt geen tweede t bij.")
    if zin.vorm == "vt" and stamsoort(w) in ("t", "d"):
        s = stamsoort(w)
        regels.append(f"De stam eindigt op {s} en de uitgang begint met {s}: je schrijft ze allebei.")
    return regels + [f"Dus: {zin.antwoord}.  →  {zin.vol()}"]


# ---- de spiekbrieven ---------------------------------------------------------------------------------------------

KOP = {
    "stam": "DE STAM",
    "wie": "WIE DOET HET?",
    "getal": "EEN OF MEER",
    "kofschip": "'T KOFSCHIP",
}

_STAM = [
    (KOP["stam"], "accent"),
    ("  De stam is de ik-vorm: ik werk, ik loop, ik pak.", ""),
    ("    lopen → ik loop     een lange klank: twee klinkers", "dim"),
    ("    pakken → ik pak     nooit twee dezelfde medeklinkers aan het einde", "dim"),
    ("    leven → ik leef     nooit een v of z aan het einde (reizen → ik reis)", "dim"),
    ("", ""),
]

SPIEKBRIEF_TT = [
    ("Tegenwoordige tijd: zo schrijf je het werkwoord", "accent"),
    ("Zoek eerst wie het doet (het onderwerp), dan de stam.", "dim"),
    ("", ""),
    *_STAM,
    (KOP["wie"], "accent"),
    ("  ik                      de stam              ik werk      ik word", ""),
    ("  jij vóór het werkwoord  de stam + t          jij werkt    jij wordt", ""),
    ("  jij erachter            de stam              werk jij?    word jij?", ""),
    ("  hij, zij, het, 1 naam   de stam + t          hij werkt    Noor wordt", ""),
    ("  meer dan één            het hele werkwoord   we werken    ze worden", ""),
    ("", ""),
    ("DE STAM EINDIGT OP D OF T", "accent"),
    ("  Op d: de t komt er gewoon bij.        hij wordt, zij vindt", ""),
    ("  Op t: er komt geen tweede t bij.      hij wacht, zij praat", ""),
    ("  Twijfel je? Zeg het met ‘lopen’: hij loopt, dus hij wordt.", "dim"),
    ("", ""),
    ("ZIJN EN HEBBEN", "accent"),
    ("  ik ben, jij bent, hij is, wij zijn", ""),
    ("  ik heb, jij hebt, hij heeft, wij hebben", ""),
]

SPIEKBRIEF_VT = [
    ("Verleden tijd van zwakke werkwoorden: 't kofschip", "accent"),
    ("Een zwak werkwoord houdt zijn klank: werken, werkte, gewerkt.", "dim"),
    ("", ""),
    *_STAM,
    (KOP["kofschip"], "accent"),
    ("  Neem het werkwoord zonder -en: werk(en), spel(en), lev(en).", ""),
    ("  Staat de laatste letter in 't kofschip (t, k, f, s, ch, p)?", ""),
    ("    ja   →  de stam + te     werken: werk + te = werkte", ""),
    ("    nee  →  de stam + de     spelen: speel + de = speelde", ""),
    ("", ""),
    (KOP["getal"], "accent"),
    ("  Eén:   -te of -de        hij werkte, zij speelde", ""),
    ("  Meer:  -ten of -den      we werkten, ze speelden", ""),
    ("", ""),
    ("LET OP", "accent"),
    ("  leven: de v zit niet in 't kofschip → leefde (de stam is leef).", ""),
    ("  reizen: de z zit er ook niet in → reisde.", ""),
    ("  praten: praat + te = praatte (twee t's).", ""),
    ("  antwoorden: antwoord + de = antwoordde (twee d's).", ""),
]


# ---- de onderwerpen (voor de Oefenaar: reeks, vrij oefenen, herhaalbak, punten, rapport) ------------------------

from ..onderwerp import Onderwerp, Vraag  # noqa: E402 (onderaan: de functies hierboven hebben dit niet nodig)


class Werkwoordspelling(Onderwerp):
    """Een onderwerp van Werkwoordspelling: een zin met een gat (het invoer-object terminal/werkwoord.py speelt de
    stappen en geeft de getypte vorm terug). De leerlijn kiest de werkwoorden (niveaus, stammen), de personen en de
    zinnen (patronen). Het groepje voor herhaling is "persoon/stamsoort" (bv. "jij_inv/d")."""
    vorm = "tt"
    denkfouten = DENKFOUTEN
    brief = ()

    def kandidaten(self, p):
        """De werkwoorden van dit leerjaar."""
        return [w for w in lijst() if w["niveau"] in p["niveaus"] and stamsoort(w) in p["stammen"] and self.past(w, p)]

    def past(self, w, p):
        return True

    def groepje(self, zin):
        return f"{zin.persoon}/{stamsoort(zin.ww)}"

    def maak_met(self, p, rng, data=None):
        ww_lijst = self.kandidaten(p)
        personen, stam = list(p["personen"]), None
        groep = (data or {}).get("onderwerp") or ""
        if "/" in groep:  # een herhaling: dezelfde persoon en dezelfde soort stam, als dat leerjaar ze heeft
            persoon, stam = groep.split("/", 1)
            if persoon in personen:
                personen = [persoon]
        soorten = sorted({stamsoort(w) for w in ww_lijst})
        for _ in range(200):
            # wat lastig is (een stam op d of t, een v of z) komt even vaak als elk ander soort, niet naar het aantal
            # werkwoorden in de lijst; de gewone stam telt dubbel
            soort = stam if stam in soorten else rng.choices(soorten, [2 if s == "gewoon" else 1 for s in soorten])[0]
            w = rng.choice([w for w in ww_lijst if stamsoort(w) == soort])
            zin = maak_zin(w, self.vorm, rng, personen, p["patronen"]) or \
                maak_zin(w, self.vorm, rng, p["personen"], p["patronen"])
            if zin is not None and len(zin.tekst) <= BREED:
                break
        else:
            raise RuntimeError(f"geen zin gevonden voor {self.id}")
        groep = self.groepje(zin)
        data = {"onderwerp": groep, "inf": zin.inf, "stap_voor_stap": p["stap_voor_stap"]}
        return Vraag(self.id, f"{self.id}:{groep}:{zin.tekst}", zin.tekst, zin.antwoord, "", data, invoer="werkwoord",
                     model=zin)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":", 2)
        return delen[1] if len(delen) == 3 and delen[0] == self.id and "/" in delen[1] else None

    def lees_vraag(self, v, tekst):
        tekst = (tekst or "").strip().lower()
        return tekst or None

    def nakijken(self, v, getal):
        return nakijken(v.model, getal)

    def diagnose(self, v, getal):
        return diagnose_vorm(v.model, getal)

    def uitleg(self, v):
        return uitleg(v.model)

    def tip(self, v):
        return stappen(v.model, False)[0].tips[0]

    def tips(self, v):
        return list(stappen(v.model, False)[0].tips)

    def spiekbrief(self):
        return list(self.brief)

    def kop_op_spiekbrief(self, v):
        """Het kopje van de stap waar het kind is (het invoer-object zet v.data["spiek_kop"])."""
        return v.data.get("spiek_kop") or stappen(v.model, False)[0].kop


class TegenwoordigeTijd(Werkwoordspelling):
    id = "taal.werkwoordspelling.tt"
    naam = "Tegenwoordige tijd"
    omschrijving = "de stam, de stam + t of het hele werkwoord (hij wordt, word jij?)"
    vorm = "tt"
    brief = SPIEKBRIEF_TT

    def past(self, w, p):
        if w.get("onregelmatig"):
            return bool(p.get("onregelmatig"))
        return w["tt"] == regel_tt(w)  # (gaan, staan en slaan hebben een eigen vorm: niet in deze oefening)


class VerledenTijdZwak(Werkwoordspelling):
    id = "taal.werkwoordspelling.vt_zwak"
    naam = "Verleden tijd: zwakke werkwoorden"
    omschrijving = "'t kofschip: werkte of speelde, praatte, leefde"
    vorm = "vt"
    brief = SPIEKBRIEF_VT

    def past(self, w, p):
        return w["vt_soort"] == "zwak"

    def groepje(self, zin):
        return f"{'mv' if zin.meervoud else 'ev'}/{stamsoort(zin.ww)}"


TEGENWOORDIGE_TIJD = TegenwoordigeTijd()
VERLEDEN_TIJD_ZWAK = VerledenTijdZwak()
