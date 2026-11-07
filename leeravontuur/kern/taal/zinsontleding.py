"""Zinsontleding: de stappen, het nakijken, de denkfouten, de tips (de proefjes) en de uitleg. Zonder curses.

De vader (7/11, docs/taal.md): stap voor stap zoals op school (pv → ow → lv → mv; op Moeilijk ook het gezegde en de
bwb), een tip met het proefje en een tweede kans, en de vraag zoals op school: "wie/wat + pv + ow?".
In elke stap kiest het kind woorden (een tuple met posities) of zegt het dat het zinsdeel er niet is (None).
"""

from .zinnen import GEZEGDE, ZINSDELEN

VOLGORDE = ("pv", "ow", "wwg", "nwg", "lv", "mv", "bwb")  # de volgorde van de stappen
NAMEN = ZINSDELEN
LIDWOORD = {"pv": "de", "ow": "het", "wwg": "het", "nwg": "het", "lv": "het", "mv": "het", "bwb": "de"}

DENKFOUTEN = {
    "zo_pv_geen_ww": "als persoonsvorm een woord gekozen dat geen werkwoord is",
    "zo_pv_eerste": "het eerste woord van de zin als persoonsvorm gekozen",
    "zo_pv_ander_ww": "het andere werkwoord als persoonsvorm gekozen (niet het werkwoord dat verandert)",
    "zo_groep_te_klein": "een zinsdeel te klein gekozen (een deel van de woordgroep)",
    "zo_groep_te_groot": "een zinsdeel te groot gekozen (woorden van een ander zinsdeel erbij)",
    "zo_ow_lv": "onderwerp en lijdend voorwerp verwisseld",
    "zo_lv_mv": "lijdend en meewerkend voorwerp verwisseld",
    "zo_vergeten": "gezegd dat een zinsdeel er niet is terwijl het er wel is (of omgekeerd)",
}


def stappen(zin, gevraagd):
    """De labels die in deze oefening gevraagd worden, in de volgorde van de stappen. gevraagd = de zinsdelen van het
    leerjaar (leerlijn). Het gezegde is één stap: wwg of nwg, wat de zin heeft."""
    uit = []
    for label in VOLGORDE:
        if label not in gevraagd:
            continue
        if label in GEZEGDE:
            echt = next((g for g in GEZEGDE if zin.deel(g)), None)
            if echt and echt not in uit:
                uit.append(echt)
            continue
        uit.append(label)
    return uit


def verwacht(zin, label):
    """De posities van het zinsdeel (alle bwb's samen), of None als de zin het niet heeft."""
    delen = zin.alle(label)
    if not delen:
        return None
    return tuple(sorted({p for d in delen for p in d.posities}))


def nakijken(zin, label, gekozen):
    """Is de keuze voor deze stap juist? gekozen = tuple van posities, of None ("er is er geen")."""
    juist = verwacht(zin, label)
    if gekozen is None or juist is None:
        return gekozen is None and juist is None
    return tuple(sorted(gekozen)) == juist


def diagnose(zin, label, gekozen):
    """(code, uitleg voor het kind) bij een foute keuze, of None als er geen bekende denkfout is."""
    juist = verwacht(zin, label)
    if nakijken(zin, label, gekozen):
        return None
    if gekozen is None or juist is None:
        vraag = vraag_naar(zin, label)
        if gekozen is None:
            return "zo_vergeten", f"Kijk nog eens: er is wel een {NAMEN[label]}. {vraag}"
        return "zo_vergeten", f"Stel de vraag nog eens: {vraag} Komt er geen antwoord, druk dan N."
    keuze = set(gekozen)
    if label == "pv":
        w = zin.woorden[min(keuze)]
        if len(keuze) > 1:
            return "zo_groep_te_groot", "De persoonsvorm is maar één woord."
        if w.soort != "ww" and min(keuze) == 0:
            return "zo_pv_eerste", (f"De pv staat niet altijd vooraan, en *{w.tekst}* is geen werkwoord. "
                                    "Maak er een vraag van: welk werkwoord komt vooraan?")
        if w.soort != "ww":
            return "zo_pv_geen_ww", f"*{w.tekst}* is geen werkwoord. De pv is altijd een werkwoord."
        return "zo_pv_ander_ww", ("Er zijn twee werkwoorden. De pv is het werkwoord dat verandert als je de zin in een "
                                  "andere tijd zet.")
    for ander in ("ow", "lv", "mv"):  # twee zinsdelen verwisseld
        elders = verwacht(zin, ander)
        if ander != label and elders and keuze == set(elders) and (label, ander) in VERWISSELD:
            code, tekst = VERWISSELD[(label, ander)]
            return code, tekst + " " + vraag_naar(zin, label)
    if keuze < set(juist):
        return "zo_groep_te_klein", "Een zinsdeel kan meer woorden zijn: wat hoort er nog bij?"
    if keuze > set(juist):
        return "zo_groep_te_groot", "Er zitten woorden bij die niet bij dit zinsdeel horen."
    return None


# (gevraagd, gekozen) -> (denkfout, wat het programma zegt; daarna komt de vraag van school)
VERWISSELD = {
    ("ow", "lv"): ("zo_ow_lv", "Dat is het lijdend voorwerp. Het onderwerp past bij de pv: maak het meervoud en kijk "
                               "of de pv mee verandert."),
    ("lv", "ow"): ("zo_ow_lv", "Dat is het onderwerp."),
    ("lv", "mv"): ("zo_lv_mv", "Dat is het meewerkend voorwerp: dat krijgt iets."),
    ("mv", "lv"): ("zo_lv_mv", "Dat is het lijdend voorwerp. Het meewerkend voorwerp krijgt iets."),
}


# ---- de proefjes: de vraag (tip 1), het proefje op deze zin (tip 2) en de uitleg achteraf -------------------------

def _tekst(zin, label):
    posities = verwacht(zin, label)
    return " ".join(zin.woorden[p].tekst for p in posities) if posities else ""


def _naam(zin, p):
    """Houdt woord p zijn hoofdletter midden in een vraag? Ja voor een naam: een zelfstandig naamwoord met een
    hoofdletter (een gewoon zn begint de zin niet zonder lidwoord of voornaamwoord: *de juf*, *mijn broer*)."""
    w = zin.woorden[p]
    if p == 0 and "eerste" in zin.data:  # een zin van de machine: die weet hoe het woord in de lijst staat
        return zin.data["eerste"][:1].isupper()
    return w.tekst[:1].isupper() and (p > 0 or w.soort == "zn")


def _woorden(zin, posities):
    """De woorden op die posities, met een kleine letter als het eerste woord van de zin midden in een vraag komt."""
    uit = []
    for p in posities:
        w = zin.woorden[p].tekst
        if p == 0 and not _naam(zin, p):
            w = w[0].lower() + w[1:]
        uit.append(w)
    return " ".join(uit)


def vraag_naar(zin, label):
    """De vraag zoals op school, ingevuld met deze zin (zonder het antwoord)."""
    pv = _woorden(zin, verwacht(zin, "pv"))
    ow = _woorden(zin, verwacht(zin, "ow") or ())
    rest_ww = _woorden(zin, [p for p in (verwacht(zin, "wwg") or verwacht(zin, "nwg") or ())
                             if p not in verwacht(zin, "pv") and zin.woorden[p].soort == "ww"])
    lv = _woorden(zin, verwacht(zin, "lv") or ())
    if label == "pv":
        return "Maak er een vraag van: welk werkwoord komt vooraan?"
    if label == "ow":
        return f"Wie of wat {pv}{' ' + rest_ww if rest_ww else ''}?"
    if label == "lv":
        wie = "Wie" if zin.data.get("lv_wie") else "Wat"
        return f"{wie} {pv} {ow}{' ' + rest_ww if rest_ww else ''}?"
    if label == "mv":
        vz = (zin.data.get("mv_vz") or "aan").capitalize()
        return f"{vz} wie {pv} {ow}{' ' + lv if lv else ''}{' ' + rest_ww if rest_ww else ''}?"
    if label in GEZEGDE:
        return "Welke werkwoorden horen samen (de pv en de andere werkwoorden), en zegt het gezegde wat het ow doet " \
               "of hoe het is?"
    if label == "bwb":
        return "Waar, wanneer of hoe gebeurt het?"
    return ""


TIP1 = {
    "pv": "Maak er een vraag van: het werkwoord dat vooraan komt, is de pv.",
    "ow": "Wie of wat + pv?",
    "lv": "Wie of wat + pv + ow?",
    "mv": "Aan of voor wie + pv + ow + lv?",
    "wwg": "Het werkwoordelijk gezegde: de pv en de andere werkwoorden samen.",
    "nwg": "Het naamwoordelijk gezegde: een koppelwerkwoord (zijn, worden, blijven) + wat het ow is of wordt.",
    "bwb": "Waar, wanneer of hoe? Dat is een bijwoordelijke bepaling.",
}


def tips(zin, label):
    """[tip 1 (de vraag), tip 2 (het proefje op deze zin, zonder het antwoord te zeggen)]."""
    tweede = vraag_naar(zin, label)
    if label == "pv":
        anders = zin.data.get("pv_andere_tijd")
        if zin.woorden[-1].tekst == "?":
            tweede = "Het is al een vraag: welk werkwoord staat vooraan?"
        elif anders:
            tijd = "verleden tijd" if zin.data.get("tijd") == "tt" else "tegenwoordige tijd"
            tweede = f"De tijdproef: zet de zin in de {tijd}. Welk woord verandert? Dat is de pv."
        else:
            tweede = "De tijdproef: zet de zin in een andere tijd (gisteren …, vandaag …). Welk woord verandert?"
    elif label == "ow":
        tweede = f"Vraag het met de pv: {tweede}"
    elif label in ("lv", "mv"):
        tweede = f"Vraag het zoals op school: {tweede}"
    return [TIP1[label], tweede]


def uitleg(zin, label):
    """Na het nakijken (of na de tweede kans): het juiste antwoord, met de vraag of het proefje."""
    antwoord = _tekst(zin, label)
    if not antwoord:
        return f"Deze zin heeft geen {NAMEN[label]}."
    if label == "pv":
        anders = zin.data.get("pv_andere_tijd")
        proef = f" In een andere tijd wordt het *{anders}*: dat woord verandert." if anders else ""
        if zin.woorden[-1].tekst == "?":
            return f"De pv is *{antwoord}*: in een vraag staat de pv vooraan."
        return f"De pv is *{antwoord}*.{proef}"
    if label in ("ow", "lv", "mv"):
        return f"{vraag_naar(zin, label)} → *{_woorden(zin, verwacht(zin, label))}*. Dat is het {NAMEN[label]}."
    return f"{LIDWOORD[label].capitalize()} {NAMEN[label]} is *{_woorden(zin, verwacht(zin, label))}*."


# ---- vrij kleuren (Tab; op Moeilijk altijd) ---------------------------------------------------------------------

def nakijken_vrij(zin, gevraagd, markering):
    """markering = {positie: label} (wat het kind kleurde). Geeft {label: (juist?, diagnose of None)} per gevraagd
    label. De pv hoort ook bij het gezegde: wie de pv kleurt, kleurt dat woord ook als stuk van het gezegde."""
    uit = {}
    for label in stappen(zin, gevraagd):
        gekozen = tuple(sorted(p for p, l in markering.items() if l == label))
        if label in GEZEGDE and gekozen:
            gekozen = tuple(sorted(set(gekozen) | {p for p, l in markering.items() if l == "pv"}))
        keuze = gekozen or None
        uit[label] = (nakijken(zin, label, keuze), diagnose(zin, label, keuze))
    return uit


# ---- in zinsdelen verdelen (Makkelijk: L4 1.4.10, "zinsdeel") ---------------------------------------------------

TIP_VERDELEN = ["Woorden die samen één zinsdeel zijn, kan je samen verplaatsen.",
                "De verplaatsproef: zet een groep woorden vooraan. Klopt de zin nog? Dan is het één zinsdeel."]


def verdeling(zin):
    """De zinsdelen als aaneengesloten stukken: [(posities), …] in de volgorde van de zin. De pv is een eigen stuk;
    de rest van het gezegde (bv. *gekocht*) ook."""
    def wie(i):
        delen = [d for d in zin.delen if i in d.posities]
        pv = [d for d in delen if d.label == "pv"]
        return id((pv or delen or [None])[0])
    stukken, vorige = [], None
    for i, w in enumerate(zin.woorden):
        if w.leesteken:
            vorige = None
            continue
        if stukken and wie(i) == vorige and stukken[-1][-1] == i - 1:
            stukken[-1].append(i)
        else:
            stukken.append([i])
        vorige = wie(i)
    return [tuple(s) for s in stukken]


def nakijken_verdeling(zin, stukken):
    """Zijn de stukken van het kind dezelfde als de zinsdelen? Geeft (juist?, de stukken die niet kloppen)."""
    juist = set(verdeling(zin))
    fout = [s for s in map(tuple, stukken) if s not in juist]
    return not fout and len(juist) == len(stukken), fout
