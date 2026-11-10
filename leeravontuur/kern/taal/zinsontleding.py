"""Zinsontleding: de stappen, het nakijken, de denkfouten, de tips (de proefjes) en de uitleg. Zonder curses.

De vader (7/11, docs/taal.md): stap voor stap zoals op school (pv → o → lv → mv; op Moeilijk ook het gezegde en de
bwb), een tip met het proefje en een tweede kans, en de vraag zoals op school: "wie/wat + pv + o?".
In elke stap kiest het kind woorden (een tuple met posities) of zegt het dat het zinsdeel er niet is (None).

Een zin met meer dan één pv (0.25.1, `Zin.samengesteld`): eerst **alle** persoonsvormen (stap "pv"), dan het onderwerp
bij elke pv (de stappen "o1", "o2" …, in de volgorde van de pv's). `soort("o2")` is "o": de naam en de kleur.
"""

from .zinnen import GEZEGDE, ZINSDELEN, deelzinnen

VOLGORDE = ("pv", "o", "wwg", "nwg", "lv", "mv", "bwb")  # de volgorde van de stappen
NAMEN = ZINSDELEN
LIDWOORD = {"pv": "de", "o": "het", "wwg": "het", "nwg": "het", "lv": "het", "mv": "het", "bwb": "de"}

DENKFOUTEN = {
    "zo_pv_geen_ww": "als persoonsvorm een woord gekozen dat geen werkwoord is",
    "zo_pv_eerste": "het eerste woord van de zin als persoonsvorm gekozen",
    "zo_pv_ander_ww": "het andere werkwoord als persoonsvorm gekozen (niet het werkwoord dat verandert)",
    "zo_groep_te_klein": "een zinsdeel te klein gekozen (een deel van de woordgroep)",
    "zo_groep_te_groot": "een zinsdeel te groot gekozen (woorden van een ander zinsdeel erbij)",
    "zo_o_lv": "onderwerp en lijdend voorwerp verwisseld",
    "zo_lv_mv": "lijdend en meewerkend voorwerp verwisseld",
    "zo_vergeten": "gezegd dat een zinsdeel er niet is terwijl het er wel is (of omgekeerd)",
    "zo_pv_een_vergeten": "in een zin met meer dan één persoonsvorm niet alle persoonsvormen gevonden",
    "zo_pv_te_veel": "in een zin met meer dan één persoonsvorm een woord te veel als persoonsvorm aangeduid",
    "zo_o_andere_pv": "in een zin met meer dan één persoonsvorm het onderwerp van de andere persoonsvorm gekozen",
}


def soort(label):
    """Het zinsdeel van een stap: "o2" (het onderwerp bij de tweede pv) is een "o"."""
    return "o" if len(label) == 2 and label[0] == "o" and label[1].isdigit() else label


def _nr(label):
    """Het nummer van de deelzin bij een stap "o1", "o2" … (vanaf 0), of None."""
    return int(label[1]) - 1 if soort(label) != label else None


def stappen(zin, gevraagd):
    """De labels die in deze oefening gevraagd worden, in de volgorde van de stappen. gevraagd = de zinsdelen van het
    leerjaar (leerlijn). Het gezegde is één stap: wwg of nwg, wat de zin heeft."""
    if zin.samengesteld:
        return ["pv", *(f"o{k + 1}" for k in range(len(deelzinnen(zin))))]
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
    """De posities van het zinsdeel (alle bwb's samen, alle pv's van een samengestelde zin), of None als de zin het
    niet heeft."""
    if _nr(label) is not None:
        paren = deelzinnen(zin)
        return paren[_nr(label)][1] if _nr(label) < len(paren) else None
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
            return "zo_vergeten", f"Kijk nog eens: er is wel een {NAMEN[soort(label)]}. {vraag}"
        return "zo_vergeten", f"Stel de vraag nog eens: {vraag} Komt er geen antwoord, druk dan N."
    keuze = set(gekozen)
    if zin.samengesteld:
        return _diagnose_samengesteld(zin, label, keuze, set(juist))
    if label == "pv":
        w = zin.woorden[min(keuze)]
        if len(keuze) > 1:
            return "zo_groep_te_groot", "De persoonsvorm is maar één woord."
        if w.soort != "ww" and min(keuze) == 0:
            return "zo_pv_eerste", (f"De pv staat niet altijd vooraan, en ‘{w.tekst}’ is geen werkwoord. "
                                    "Maak er een vraag van: welk werkwoord komt vooraan?")
        if w.soort != "ww":
            return "zo_pv_geen_ww", f"‘{w.tekst}’ is geen werkwoord. De pv is altijd een werkwoord."
        return "zo_pv_ander_ww", ("Er zijn twee werkwoorden. De pv is het werkwoord dat verandert als je de zin in een "
                                  "andere tijd zet.")
    for ander in ("o", "lv", "mv"):  # twee zinsdelen verwisseld
        elders = verwacht(zin, ander)
        if ander != label and elders and keuze == set(elders) and (label, ander) in VERWISSELD:
            code, tekst = VERWISSELD[(label, ander)]
            return code, tekst + " " + vraag_naar(zin, label)
    if keuze < set(juist):
        return "zo_groep_te_klein", "Een zinsdeel kan meer woorden zijn: wat hoort er nog bij?"
    if keuze > set(juist):
        return "zo_groep_te_groot", "Er zitten woorden bij die niet bij dit zinsdeel horen."
    return None


def _diagnose_samengesteld(zin, label, keuze, juist):
    """De denkfouten in een zin met meer dan één pv (alleen pv en o zijn aangeduid)."""
    n = len(deelzinnen(zin))
    aantal = {2: "twee", 3: "drie"}.get(n, str(n))
    if label == "pv":
        fout = sorted(keuze - juist)
        if fout:
            w = zin.woorden[fout[0]]
            if w.soort == "ww":
                return "zo_pv_ander_ww", (f"‘{w.tekst}’ is een werkwoord, maar geen pv: het verandert niet als je de "
                                          "zin in een andere tijd zet.")
            if w.soort is None:  # een woord dat niet in de woordenlijst staat
                return "zo_pv_te_veel", (f"Deze zin heeft {aantal} persoonsvormen. ‘{w.tekst}’ verandert niet als je "
                                         "de zin in een andere tijd zet.")
            return "zo_pv_geen_ww", f"‘{w.tekst}’ is geen werkwoord. Een pv is altijd een werkwoord."
        return "zo_pv_een_vergeten", (f"Deze zin heeft {aantal} persoonsvormen. Zet de zin in een andere tijd: welke "
                                      "werkwoorden veranderen?")
    pv = _pv_van(zin, label)
    for k, (_, o) in enumerate(deelzinnen(zin)):
        if k != _nr(label) and o and keuze == set(o) and set(o) != juist:
            ander = zin.woorden[deelzinnen(zin)[k][0]].tekst
            return "zo_o_andere_pv", f"Dat is het onderwerp bij ‘{ander}’. Vraag het met deze pv: wie of wat {pv}?"
    if keuze < juist:
        return "zo_groep_te_klein", "Een zinsdeel kan meer woorden zijn: wat hoort er nog bij?"
    if keuze > juist:
        return "zo_groep_te_groot", "Er zitten woorden bij die niet bij dit onderwerp horen."
    return None


def _pv_van(zin, label):
    """De pv (het woord) bij de stap "o1", "o2" …"""
    return _woorden(zin, [deelzinnen(zin)[_nr(label)][0]])


# (gevraagd, gekozen) -> (denkfout, wat het programma zegt; daarna komt de vraag van school)
VERWISSELD = {
    ("o", "lv"): ("zo_o_lv", "Dat is het lijdend voorwerp. Het onderwerp past bij de pv: maak het meervoud en kijk "
                               "of de pv mee verandert."),
    ("lv", "o"): ("zo_o_lv", "Dat is het onderwerp."),
    ("lv", "mv"): ("zo_lv_mv", "Dat is het meewerkend voorwerp: dat krijgt iets."),
    ("mv", "lv"): ("zo_lv_mv", "Dat is het lijdend voorwerp. Het meewerkend voorwerp krijgt iets."),
}


# ---- de proefjes: de vraag (tip 1), het proefje op deze zin (tip 2) en de uitleg achteraf -------------------------

def _tekst(zin, label):
    posities = verwacht(zin, label)
    return " ".join(zin.woorden[p].tekst for p in posities) if posities else ""


def _naam(zin, p):
    """Houdt woord p zijn hoofdletter midden in een vraag? Ja voor een naam: een zelfstandig naamwoord met een
    hoofdletter (een gewoon zn begint de zin niet zonder lidwoord of voornaamwoord: ‘de juf’, ‘mijn broer’)."""
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
    if zin.samengesteld:
        if label == "pv":
            return "Zet de zin in een andere tijd: welke werkwoorden veranderen?"
        return f"Wie of wat {_pv_van(zin, label)}?"
    pv = _woorden(zin, verwacht(zin, "pv"))
    o = _woorden(zin, verwacht(zin, "o") or ())
    rest_ww = _woorden(zin, [p for p in (verwacht(zin, "wwg") or verwacht(zin, "nwg") or ())
                             if p not in verwacht(zin, "pv") and zin.woorden[p].soort == "ww"])
    lv = _woorden(zin, verwacht(zin, "lv") or ())
    if label == "pv":
        return "Maak er een vraag van: welk werkwoord komt vooraan?"
    if label == "o":
        return f"Wie of wat {pv}{' ' + rest_ww if rest_ww else ''}?"
    if label == "lv":
        wie = "Wie" if zin.data.get("lv_wie") else "Wat"
        return f"{wie} {pv} {o}{' ' + rest_ww if rest_ww else ''}?"
    if label == "mv":
        vz = (zin.data.get("mv_vz") or "aan").capitalize()
        return f"{vz} wie {pv} {o}{' ' + lv if lv else ''}{' ' + rest_ww if rest_ww else ''}?"
    if label in GEZEGDE:
        return "Welke werkwoorden horen samen (de pv en de andere werkwoorden), en zegt het gezegde wat het onderwerp doet " \
               "of hoe het is?"
    if label == "bwb":
        return "Waar, wanneer of hoe gebeurt het?"
    return ""


TIP1 = {
    "pv": "Maak er een vraag van: het werkwoord dat vooraan komt, is de pv.",
    "o": "Wie of wat + pv?",
    "lv": "Wie of wat + pv + o?",
    "mv": "Aan of voor wie + pv + o + lv?",
    "wwg": "Het werkwoordelijk gezegde: de pv en de andere werkwoorden samen.",
    "nwg": "Het naamwoordelijk gezegde: een koppelwerkwoord (zijn, worden, blijven) + wat het onderwerp is of wordt.",
    "bwb": "Waar, wanneer of hoe? Dat is een bijwoordelijke bepaling.",
}


def tips(zin, label):
    """[tip 1 (de vraag), tip 2 (het proefje op deze zin, zonder het antwoord te zeggen)]."""
    if zin.samengesteld:
        if label == "pv":
            return ["Een lange zin kan meer dan één pv hebben: elk stuk van de zin heeft er één.",
                    "De tijdproef: zet de zin in een andere tijd. Elk werkwoord dat verandert, is een pv."]
        return ["Elke pv heeft een onderwerp. Soms delen twee pv's hetzelfde onderwerp.",
                f"Vraag het met de pv: {vraag_naar(zin, label)}"]
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
    elif label == "o":
        tweede = f"Vraag het met de pv: {tweede}"
    elif label in ("lv", "mv"):
        tweede = f"Vraag het zoals op school: {tweede}"
    return [TIP1[label], tweede]


def uitleg(zin, label):
    """Na het nakijken (of na de tweede kans): het juiste antwoord, met de vraag of het proefje."""
    if zin.samengesteld:
        if label == "pv":
            return f"De persoonsvormen zijn {opsomming(zin, verwacht(zin, 'pv'))}: elk stuk van de zin heeft er één."
        o = _woorden(zin, verwacht(zin, label))
        return f"{vraag_naar(zin, label)} → ‘{o}’. Dat is het onderwerp bij ‘{_pv_van(zin, label)}’."
    antwoord = _tekst(zin, label)
    if not antwoord:
        return f"Deze zin heeft geen {NAMEN[label]}."
    if label == "pv":
        anders = zin.data.get("pv_andere_tijd")
        proef = f" In een andere tijd wordt het ‘{anders}’: dat woord verandert." if anders else ""
        if zin.woorden[-1].tekst == "?":
            return f"De pv is ‘{antwoord}’: in een vraag staat de pv vooraan."
        return f"De pv is ‘{antwoord}’.{proef}"
    if label in ("o", "lv", "mv"):
        return f"{vraag_naar(zin, label)} → ‘{_woorden(zin, verwacht(zin, label))}’. Dat is het {NAMEN[label]}."
    return f"{LIDWOORD[label].capitalize()} {NAMEN[label]} is ‘{_woorden(zin, verwacht(zin, label))}’."


def opsomming(zin, posities):
    """‘vertelt’ en ‘ligt’ (losse woorden, zoals de pv's van een samengestelde zin)."""
    woorden = [f"‘{_woorden(zin, [p])}’" for p in posities]
    return " en ".join([", ".join(woorden[:-1]), woorden[-1]] if len(woorden) > 1 else woorden)


def kort(zin, label, posities):
    """De woorden van een nagekeken stap, kort: "mijn ouders", of "vertelt, ligt" (de pv's van een samengestelde zin)."""
    if zin.samengesteld and label == "pv":
        return ", ".join(_woorden(zin, [p]) for p in posities)
    return _woorden(zin, posities)


def naam_van_stap(zin, label):
    """Hoe de stap heet in een melding: "pv", "lv", of "o bij ‘ligt’" (samengestelde zin)."""
    return f"o bij ‘{_pv_van(zin, label)}’" if _nr(label) is not None else label


# ---- vrij kleuren (Tab; op Moeilijk altijd) ---------------------------------------------------------------------

def nakijken_vrij(zin, gevraagd, markering):
    """markering = {positie: label} (wat het kind kleurde). Geeft {label: (juist?, diagnose of None)} per gevraagd
    label. De pv hoort ook bij het gezegde: wie de pv kleurt, kleurt dat woord ook als stuk van het gezegde.
    In een zin met meer dan één pv: alle pv's en alle onderwerpen gekleurd (welk onderwerp bij welke pv hoort, vraagt
    alleen stap voor stap)."""
    if zin.samengesteld:
        pv = tuple(sorted(p for p, l in markering.items() if l == "pv"))
        o = {p for p, l in markering.items() if l == "o"}
        uit = {"pv": (nakijken(zin, "pv", pv or None), diagnose(zin, "pv", pv) if pv else None)}
        alle_o = {p for _, posities in deelzinnen(zin) for p in posities}
        for label in stappen(zin, gevraagd)[1:]:
            eigen = set(verwacht(zin, label))
            juist = eigen <= o and o <= alle_o
            d = None if juist else ("zo_groep_te_groot", "") if eigen <= o else ("zo_groep_te_klein", "") \
                if eigen & o else None
            uit[label] = (juist, d)
        return uit
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
    de rest van het gezegde (bv. ‘gekocht’) ook."""
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


# ---- het onderwerp (voor de Oefenaar: reeks, vrij oefenen, herhaalbak, punten, rapport) ------------------------

from ..onderwerp import Onderwerp, Vraag  # noqa: E402 (onderaan: de functies hierboven hebben dit niet nodig)
from . import nagekeken as N  # noqa: E402
from . import zinnenmachine as M  # noqa: E402

NAGEKEKEN, TWEE_LIJST = "nagekeken", "twee_lijst"  # zinsbouw van een zin uit de nagekeken lijst (inhoud/taal/zinnen.json)
ZINSBOUW = (*M.ZINSBOUW, *M.SAMENGESTELD, NAGEKEKEN, TWEE_LIJST)


def samenvatting(zin, gevraagd):
    """De juiste ontleding kort, voor het rapport: "pv geeft · o oma · lv een fiets · mv (geen)". Een zin met meer dan
    één pv: "pv vertelt · o grootvader | pv ligt · o de kist"."""
    if zin.samengesteld:
        return " | ".join(f"pv {_woorden(zin, [pv])} · o {_woorden(zin, o)}" for pv, o in deelzinnen(zin))
    stukken = []
    for label in stappen(zin, gevraagd):
        posities = verwacht(zin, label)
        stukken.append(f"{label} {_woorden(zin, posities) if posities else '(geen)'}")
    return " · ".join(stukken)


# ---- de spiekbrief (Leerstof › Taal › Zinsontleding, en na de laatste tip) ------------------------------------

SPIEK_KOP = {
    "verdelen": "IN ZINSDELEN VERDELEN",
    "pv": "DE PERSOONSVORM (pv)",
    "o": "HET ONDERWERP (o)",
    "lv": "HET LIJDEND VOORWERP (lv)",
    "mv": "HET MEEWERKEND VOORWERP (mv)",
    "wwg": "HET GEZEGDE (wwg, nwg)",
    "nwg": "HET GEZEGDE (wwg, nwg)",
    "bwb": "DE BIJWOORDELIJKE BEPALING (bwb)",
    "twee": "ZINNEN MET TWEE PERSOONSVORMEN",
}

SPIEKBRIEF = [
    ("Zinsontleding: zo vind je de zinsdelen", "accent"),
    ("Altijd in deze volgorde: eerst de pv, dan het onderwerp, dan de rest.", "dim"),
    ("", ""),
    (SPIEK_KOP["verdelen"], "accent"),
    ("  Woorden van één zinsdeel kan je samen verplaatsen (de verplaatsproef):", ""),
    ("  De juf | leest | een boek.  →  Een boek leest de juf.", ""),
    ("", ""),
    (SPIEK_KOP["pv"], "accent"),
    ("  De pv is altijd een werkwoord, en altijd maar één woord.", ""),
    ("  Vraagproef: maak er een vraag van. Het werkwoord vooraan is de pv.", ""),
    ("    Oma geeft haar kleinzoon een fiets.  →  Geeft oma … ?", "dim"),
    ("  Tijdproef: zet de zin in een andere tijd. Wat verandert, is de pv.", ""),
    ("    Oma geeft …  →  Oma gaf …", "dim"),
    ("  Getalproef: maak het onderwerp meervoud. Wat mee verandert, is de pv.", ""),
    ("    Oma geeft …  →  De oma's geven …", "dim"),
    ("", ""),
    (SPIEK_KOP["o"], "accent"),
    ("  Vraag: wie of wat + pv?    Wie geeft?  →  oma", ""),
    ("  Het onderwerp en de pv horen samen: o meervoud, dan ook pv meervoud.", ""),
    ("", ""),
    (SPIEK_KOP["lv"], "accent"),
    ("  Vraag: wie of wat + pv + o?    Wat geeft oma?  →  een fiets", ""),
    ("  Niet elke zin heeft een lijdend voorwerp: De hond slaapt.", ""),
    ("", ""),
    (SPIEK_KOP["mv"], "accent"),
    ("  Vraag: aan of voor wie + pv + o + lv?", ""),
    ("    Aan wie geeft oma een fiets?  →  haar kleinzoon", "dim"),
    ("  Het mv krijgt iets. Soms staat er aan of voor bij: aan de kinderen.", ""),
    ("  De meeste zinnen hebben geen meewerkend voorwerp.", ""),
    ("", ""),
    (SPIEK_KOP["wwg"], "accent"),
    ("  6de leerjaar. Werkwoordelijk gezegde (wwg) = de pv + de andere ww:", ""),
    ("    Oma heeft een fiets gekocht.  →  wwg: heeft gekocht", "dim"),
    ("  Naamwoordelijk gezegde (nwg) = een koppelwerkwoord (zijn, worden,", ""),
    ("  blijven) + wat het onderwerp is of wordt.", ""),
    ("    De kat is heel moe.  →  nwg: is heel moe", "dim"),
    ("", ""),
    (SPIEK_KOP["bwb"], "accent"),
    ("  6de leerjaar (extra). Waar, wanneer of hoe gebeurt het?", ""),
    ("    Morgen koopt opa een fiets.  →  bwb: morgen", "dim"),
    ("", ""),
    (SPIEK_KOP["twee"], "accent"),
    ("  6de leerjaar. Een lange zin kan twee pv's hebben. Zoek ze allebei:", ""),
    ("  zet de zin in een andere tijd, elk werkwoord dat verandert is een pv.", ""),
    ("    Opa vertelt dat de kist onder de grond ligt.", "dim"),
    ("    →  Opa vertelde dat de kist onder de grond lag.", "dim"),
    ("  Elke pv heeft een onderwerp: wie of wat vertelt? opa. Wie of wat", ""),
    ("  ligt? de kist. Soms delen twee pv's één onderwerp:", ""),
    ("    Emma leest de brief en krijgt een idee.  →  Emma leest, Emma krijgt", "dim"),
    ("", ""),
    ("DE KLEUREN (zoals je markeerstiften)", "accent"),
    (" pv  persoonsvorm             geel ", "z_pv"),
    (" o   onderwerp                blauw ", "z_o"),
    (" lv  lijdend voorwerp         groen ", "z_lv"),
    (" mv  meewerkend voorwerp      roze ", "z_mv"),
    (" wwg werkwoordelijk gezegde   oranje ", "z_wwg"),
    (" nwg naamwoordelijk gezegde   oranje ", "z_nwg"),
    (" bwb bijwoordelijke bepaling  paars ", "z_bwb"),
]


class Zinsontleding(Onderwerp):
    """Taal › Zinsontleding › Zinsdelen: een zin van de zinnenmachine ontleden (het invoer-object terminal/zinsdelen.py
    doet de stappen en geeft "juist" of "fout" terug)."""
    id = "taal.zinsontleding"
    naam = "Zinsdelen"
    omschrijving = "de pv, het onderwerp, het lijdend en meewerkend voorwerp aanduiden"
    denkfouten = DENKFOUTEN
    vast = ("zinsbouw",)

    def kies_onderwerp(self, gewichten, p, rng):
        return {"zinsbouw": self.kies_zinsbouw(p, rng, gewichten or {})}

    def kies_zinsbouw(self, p, rng, gewichten=None):
        """Welke soort zin: een zin met twee pv's (`twee_op_tien` van de 10, alleen waar de leerlijn ze geeft), een
        nagekeken zin (`nagekeken_op_tien`), anders een zin van de machine (met gewichten: wat moeilijk was, vaker)."""
        twee = [z for z in p.get("twee_pv", ()) if z in ZINSBOUW]
        lijst = [j for j in p.get("nagekeken", ()) if N.zinnen(str(j))]
        r = rng.random() * 10
        if twee and r < p.get("twee_op_tien", 0):
            return rng.choice(twee)
        if lijst and r < p.get("twee_op_tien", 0) * bool(twee) + p.get("nagekeken_op_tien", 0):
            return NAGEKEKEN
        zb = list(p["zinsbouw"])
        if gewichten:
            return rng.choices(zb, weights=[gewichten.get(z, 1.0) for z in zb], k=1)[0]
        return rng.choice(zb)

    def past(self, zb, p):
        """Mag deze zinsbouw in dit leerjaar (bv. een herhaling uit een ander leerjaar)?"""
        if zb == NAGEKEKEN:
            return any(N.zinnen(str(j)) for j in p.get("nagekeken", ()))
        if zb in M.SAMENGESTELD or zb == TWEE_LIJST:
            return zb in p.get("twee_pv", ())
        return zb in p["zinsbouw"] and zb in M.ZINSBOUW

    def maak_zin(self, zb, p, rng):
        if zb == NAGEKEKEN:
            return N.kies(rng, p["nagekeken"])
        if zb == TWEE_LIJST:
            return rng.choice(N.twee())
        if zb in M.SAMENGESTELD:
            return M.maak_samengesteld(zb, rng, p["tijden"])
        return M.maak(zb, rng, p["tijden"], p["max_woorden"], p["zonder_lv"])

    def maak_met(self, p, rng, data=None):
        zb = (data or {}).get("zinsbouw")
        if not self.past(zb, p):  # bv. een herhaling uit een ander leerjaar
            zb = self.kies_zinsbouw(p, rng)
        zin = self.maak_zin(zb, p, rng)
        delen = ["pv", "o"] if zin.samengesteld else list(p["delen"])
        data = {"zinsbouw": zb, "onderwerp": zb, "delen": delen, "verdelen": p["verdelen"] and not zin.samengesteld,
                "stap_voor_stap": p["stap_voor_stap"] or zin.samengesteld}
        return Vraag(self.id, f"{self.id}:{zb}:{zin.tekst}", zin.tekst, "juist", "", data, invoer="zinsdelen",
                     model=zin, verwacht_tekst=samenvatting(zin, delen))

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":", 2)
        return delen[1] if len(delen) == 3 and delen[0] == self.id and delen[1] in ZINSBOUW else None

    def lees_vraag(self, v, tekst):
        """Het object geeft "juist" of "fout"; de juiste ontleding getypt (zoals in het rapport) telt ook als juist."""
        if tekst in ("juist", "fout"):
            return tekst
        return "juist" if tekst == v.verwacht else None

    def uitleg(self, v):
        zin = v.model
        return [uitleg(zin, label) for label in stappen(zin, v.data.get("delen", ("pv", "o")))]

    def tip(self, v):
        return TIP1["pv"]

    def spiekbrief(self):
        return SPIEKBRIEF

    def kop_op_spiekbrief(self, v):
        """Het kopje van de stap waar het kind is (het invoer-object zet v.data["spiek_kop"])."""
        return v.data.get("spiek_kop", SPIEK_KOP["pv"])


ZINSONTLEDING = Zinsontleding()
