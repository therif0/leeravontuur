"""Een reeks vragen uit verschillende onderwerpen: Gemengd oefenen nu, de examens later (zonder curses).

Zo werkt het (de vader, 7/11: "zorg dat de examens later veel makkelijker gaan"):
- Een **thema** is een domein uit het leerplan (bv. "wiskunde.breuken"). De terminal geeft de thema's mee als data:
  {thema-id: (vaardigheid-id, ...)}. Zo kent de kern het leerplan niet, en komt Taal er later vanzelf bij.
- `kies_onderwerpen` kiest welke vaardigheden in de reeks komen (gewogen: wat wegzakt eerst).
- `maak_vragen` maakt er een `Reeksplan` van: de vragen, met een `Hulp` (welke hulp er is).
- De terminal speelt het plan; `Uitslag` vat de antwoorden samen (ook per thema).

Een examen wordt later: de ouder kiest de thema's (of de onderwerpen) en het aantal, `Hulp.EXAMEN`, en de `Uitslag`
wordt bewaard. Dezelfde keuze, hetzelfde plan, dezelfde speler.
"""

import random
from dataclasses import dataclass, field, replace

from . import catalogus, herhaling, klok, selectie  # noqa: F401 (catalogus: alle onderwerpen geladen)
from .onderwerp import ONDERWERPEN
from .wiskunde import eenheden as E

GEMENGD_AANTAL = 20  # de vader, 7/11
MAX_LANG = 3  # hoogstens zoveel lange vragen (vraagstuk, staartdeling) in een reeks
MAX_NA_ELKAAR = 2  # hoogstens zoveel vragen na elkaar uit hetzelfde thema
FRIS_DAGEN = 14  # beheerst, maar zo lang niet meer geoefend: "fris houden"
SNEL = ("snel60", "snel20")  # snelrekenen telt niet mee (dat staat apart)

# gewicht per stand: wat wegzakt komt het vaakst
GEWICHT_FRIS = 4.0
GEWICHT_BEZIG = 2.0
GEWICHT_BEHEERST = 1.0

FRIS = "fris houden"


@dataclass(frozen=True)
class Hulp:
    """Welke hulp er is tijdens de reeks. Het klad is er altijd (de vaste werkwijze)."""
    tips: bool = True          # F1: de getrapte tips
    tweede_kans: bool = True   # fout = nog één kans
    spiekbrief: bool = True    # de spiekbrief (S, of na de laatste tip)
    uitleg_na: bool = True     # na elke vraag: juist/fout met "Zo kan het:"
    herhaalbak: bool = True    # een fout gaat in de herhaalbak
    punten: bool = True


Hulp.ALLES = Hulp()
Hulp.EXAMEN = Hulp(tips=False, tweede_kans=False, spiekbrief=False, uitleg_na=False, herhaalbak=False, punten=False)


@dataclass
class Reeksvraag:
    thema: str
    vaardigheid: str
    vraag: object


@dataclass
class Reeksplan:
    soort: str  # "gemengd" (later "examen")
    titel: str  # bv. "Gemengd oefenen"
    leerjaar: str
    vragen: list = field(default_factory=list)  # [Reeksvraag]
    hulp: Hulp = Hulp.ALLES


# ---- de stand van een vaardigheid ---------------------------------------------------

def stand(opslag, kind_id, vaardigheid, vandaag=None):
    """(stand, dagen sinds het laatst geoefend) of None als het nog nooit geoefend werd.
    stand: "fris houden" (beheerst, maar lang niet geoefend), "bezig" of "beheerst"."""
    rijen = opslag.recente_antwoorden(kind_id, vaardigheid, 200, SNEL)
    if not rijen:
        return None
    st, _, laatst, _ = herhaling._beheersing(rijen)
    dagen = ((vandaag or klok.nu().date()) - laatst).days if laatst else 0
    if st == herhaling.BEHEERST and dagen >= FRIS_DAGEN:
        return FRIS, dagen
    return st, dagen


def gewicht(st):
    return {FRIS: GEWICHT_FRIS, herhaling.BEZIG: GEWICHT_BEZIG}.get(st, GEWICHT_BEHEERST)


class _Maten:
    """Maten (de eenheden omzetten) met dezelfde namen als een Onderwerp, zodat een gemengde reeks (herhaalbak,
    fouten opnieuw, gelijkaardige vragen, het resultaat) er niets apart voor hoeft te doen. Het scherm blijft dat
    van de eenheden (terminal/schermen/eenheden.py)."""
    id = E.OMZETTEN.id
    naam = "Maten"
    lang = False

    @staticmethod
    def diagnose(v, gegeven):
        return E.diagnose(v, gegeven) if gegeven is not None else None

    @staticmethod
    def uitleg(v):
        return E.regel_uitleg(v)

    @staticmethod
    def lees_vraag(v, tekst):
        from .getal import lees_getal
        return lees_getal(tekst)

    @staticmethod
    def onderwerp(v):
        return E.onderwerp(v)

    @staticmethod
    def herhaal_data(v):
        return E.herhaal_data(v)

    @staticmethod
    def maak_herhaling(data, leerjaar, vermijd=()):
        return E.maak_herhaling(data, leerjaar, vermijd)

    @staticmethod
    def verwacht_tekst(v):
        from .getal import fmt
        return f"{fmt(v.antwoord)} {v.naar}"


MATEN = _Maten()


def onderwerp_van(vaardigheid):
    """Het Onderwerp van een vaardigheid (Maten: het object hierboven), of None."""
    return MATEN if vaardigheid == E.OMZETTEN.id else ONDERWERPEN.get(vaardigheid)


def is_maten(o):
    return o is MATEN


def is_lang(vaardigheid):
    o = ONDERWERPEN.get(vaardigheid)
    return bool(o and o.lang)


def bestaat(vaardigheid):
    return vaardigheid in ONDERWERPEN or vaardigheid == E.OMZETTEN.id


# ---- welke vaardigheden in de reeks komen -------------------------------------------

def kies_onderwerpen(opslag, kind_id, themas, aantal=GEMENGD_AANTAL, rng=random, vandaag=None):
    """[(thema, vaardigheid)] voor een reeks van `aantal` vragen, uit de gegeven thema's
    ({thema-id: (vaardigheid-id, ...)}). Alleen wat al geoefend werd (wat nieuw is, leer je in het eigen menu).
    Leeg = in die thema's werd nog niets geoefend.

    Gewogen: fris houden > bezig > beheerst. Elke keer dat een vaardigheid gekozen is, telt ze daarna half zo zwaar
    (zo komen er meer verschillende). Hoogstens MAX_NA_ELKAAR na elkaar uit hetzelfde thema en MAX_LANG lange."""
    kandidaten = {}  # (thema, vaardigheid) -> gewicht
    for thema, ids in themas.items():
        for vid in ids:
            if not bestaat(vid) or any(vid == v for _, v in kandidaten):
                continue
            s = stand(opslag, kind_id, vid, vandaag)
            if s is not None:
                kandidaten[(thema, vid)] = gewicht(s[0])
    if not kandidaten:
        return []
    keuze, lang = [], 0
    for _ in range(aantal):
        mogelijk = dict(kandidaten)
        if lang >= MAX_LANG:
            mogelijk = {k: g for k, g in mogelijk.items() if not is_lang(k[1])} or mogelijk
        laatste = [t for t, _ in keuze[-MAX_NA_ELKAAR:]]
        if len(laatste) == MAX_NA_ELKAAR and len(set(laatste)) == 1:
            mogelijk = {k: g for k, g in mogelijk.items() if k[0] != laatste[0]} or mogelijk
        items = list(mogelijk)
        k = rng.choices(items, weights=[mogelijk[i] for i in items], k=1)[0]
        keuze.append(k)
        kandidaten[k] /= 2
        lang += is_lang(k[1])
    return keuze


# ---- de vragen maken ------------------------------------------------------------------

def _gewichten(opslag, kind_id, vaardigheid):
    """Zoals in een gewone reeks: wat vaak fout gaat, komt vaker."""
    recent = opslag.recente_antwoorden(kind_id, vaardigheid, 100)
    if vaardigheid == E.OMZETTEN.id:
        paren = {f"{a}>{b}" for c in E.SOORTEN for a in E.EENHEDEN[c] for b in E.EENHEDEN[c] if a != b}
        return selectie.gewichten(recent, E.onderwerp_van_sleutel, paren)
    o = ONDERWERPEN[vaardigheid]
    onderwerpen = {o.onderwerp_van_sleutel(a["sleutel"]) for a in recent} - {None}
    return selectie.gewichten(recent, o.onderwerp_van_sleutel, onderwerpen) if onderwerpen else None


def maak_vraag(opslag, kind_id, vaardigheid, leerjaar, vermijd):
    """Eén vraag van een vaardigheid (ook Maten), niet recent al gezien."""
    gew = _gewichten(opslag, kind_id, vaardigheid)
    if vaardigheid == E.OMZETTEN.id:
        return E.maak_vraag(E.eenheden_voor(leerjaar), leerjaar, vermijd=vermijd, gewichten=gew)
    return ONDERWERPEN[vaardigheid].maak(leerjaar, vermijd, gew)


def maak_vragen(opslag, kind_id, keuze, leerjaar):
    """[Reeksvraag] voor de gekozen [(thema, vaardigheid)]."""
    vermijd, uit = {}, []
    for thema, vid in keuze:
        if vid not in vermijd:
            vermijd[vid] = selectie.recent_gezien(opslag, kind_id, vid)
        v = maak_vraag(opslag, kind_id, vid, leerjaar, vermijd[vid])
        vermijd[vid].add(v.sleutel)
        uit.append(Reeksvraag(thema, vid, v))
    return uit


def gemengd_plan(opslag, kind_id, themas, leerjaar, titel="Gemengd oefenen", aantal=GEMENGD_AANTAL, rng=random):
    """Het plan voor Gemengd oefenen, of None als er in die thema's nog niets geoefend werd."""
    keuze = kies_onderwerpen(opslag, kind_id, themas, aantal, rng)
    if not keuze:
        return None
    return Reeksplan("gemengd", titel, leerjaar, maak_vragen(opslag, kind_id, keuze, leerjaar), Hulp.ALLES)


# ---- de uitslag ----------------------------------------------------------------------

@dataclass
class Uitslag:
    goed: int = 0
    totaal: int = 0
    tijd_ms: int = 0
    per_thema: dict = field(default_factory=dict)  # thema -> [goed, totaal] (volgorde = eerste keer in de reeks)
    fouten: list = field(default_factory=list)  # [Reeksvraag]

    @classmethod
    def van(cls, antwoorden):
        """antwoorden: [(Reeksvraag, goed, tijd_ms)]."""
        u = cls()
        for rv, goed, tijd in antwoorden:
            u.totaal += 1
            u.goed += bool(goed)
            u.tijd_ms += tijd or 0
            t = u.per_thema.setdefault(rv.thema, [0, 0])
            t[0] += bool(goed)
            t[1] += 1
            if not goed:
                u.fouten.append(rv)
        return u


# ---- wie kiest de thema's (de vader, 7/11) ---------------------------------------------

KIND, VAST, EEN_KEER = "kind", "vast", "een_keer"
STANDEN = {KIND: "het kind kiest", VAST: "vast", EEN_KEER: "één keer"}


def ouder_keuze(inst):
    """(stand, thema's) die de ouder koos; een ongeldige waarde = het kind kiest."""
    data = inst.gemengd_ouder if isinstance(inst.gemengd_ouder, dict) else {}
    st = data.get("stand", KIND)
    themas = [t for t in data.get("themas", []) if isinstance(t, str)] if isinstance(data.get("themas"), list) else []
    if st not in STANDEN or (st != KIND and not themas):
        return KIND, []
    return st, themas


def themas_voor_reeks(inst, alle):
    """(thema's voor de volgende reeks, mag het kind kiezen?). alle = de thema-ids van het leerplan (volgorde).
    Thema's die niet (meer) bestaan, vallen weg; blijft er niets over van de keuze van de ouder, dan kiest het kind."""
    st, themas = ouder_keuze(inst)
    if st != KIND:
        gekozen = [t for t in alle if t in themas]
        if gekozen:
            return gekozen, False
    eigen = inst.gemengd_themas
    if isinstance(eigen, list):
        gekozen = [t for t in alle if t in eigen]
        if gekozen:
            return gekozen, True
    return list(alle), True


def na_reeks(inst):
    """Een reeks is af: "één keer" van de ouder vervalt (daarna kiest het kind weer). Geeft de nieuwe instellingen."""
    if ouder_keuze(inst)[0] == EEN_KEER:
        return replace(inst, gemengd_ouder={"stand": KIND, "themas": []})
    return inst
