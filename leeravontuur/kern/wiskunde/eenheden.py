"""Eenheden omzetten met de eenhedentabel: lengte, massa, inhoud, oppervlakte en volume.

De tabel bestaat uit vakjes (elk één cijfer, met een macht van 10). Bij lengte, massa en inhoud hoort bij elke
eenheid één vakje; bij oppervlakte twee (× 100 per eenheid) en bij volume drie (× 1000 per eenheid).
Sommige eenheden zijn een andere naam voor hetzelfde vakje: 1 ha = 1 hm², 1 l = 1 dm³, 1 ml = 1 cm³.

Alles hier is zuivere logica: vragen maken, nakijken, uitleggen en denkfouten herkennen.
Teksten voor de spiekbrief krijgen een rol ("accent", "dim" …) in plaats van een kleur.
"""

import random
from dataclasses import dataclass, field
from decimal import Decimal

from .. import leerlijnen
from ..getal import decimalen, fmt
from ..vaardigheden import DENKFOUTEN as _ALLE_DENKFOUTEN, Vaardigheid, registreer

OMZETTEN = registreer(Vaardigheid(
    "wiskunde.eenheden.omzetten", "Eenheden omzetten",
    "lengte, massa, inhoud, oppervlakte en volume herleiden met de eenhedentabel"))

MASSA, LENGTE, INHOUD, OPPERVLAKTE, VOLUME = "massa", "lengte", "inhoud", "oppervlakte", "volume"
SOORTEN = [MASSA, LENGTE, INHOUD, OPPERVLAKTE, VOLUME]
NAMEN = {LENGTE: "Lengte", MASSA: "Massa", INHOUD: "Inhoud", OPPERVLAKTE: "Oppervlakte", VOLUME: "Volume"}
CW = 5  # breedte van een vakje in een tabel met één vakje per eenheid


def _per_eenheid(eenheden, n):
    """Vakjes voor eenheden met n vakjes elk: [("", hoog, False) …, (eenheid, macht, True)]."""
    uit = []
    for label, macht in eenheden:
        uit += [("", macht + i, False) for i in range(n - 1, 0, -1)] + [(label, macht, True)]
    return uit


# Vakjes van de tabel, van links naar rechts: (label, macht van 10, staat er een eenheid?)
TABELLEN = {
    MASSA: [("t", 6, True), ("100kg", 5, False), ("10kg", 4, False), ("kg", 3, True),
            ("hg", 2, True), ("dag", 1, True), ("g", 0, True), ("dg", -1, True),
            ("cg", -2, True), ("mg", -3, True)],
    LENGTE: [("km", 3, True), ("hm", 2, True), ("dam", 1, True), ("m", 0, True),
             ("dm", -1, True), ("cm", -2, True), ("mm", -3, True)],
    INHOUD: [("hl", 2, True), ("dal", 1, True), ("l", 0, True), ("dl", -1, True), ("cl", -2, True),
             ("ml", -3, True)],
    OPPERVLAKTE: _per_eenheid([("km²", 6), ("hm²", 4), ("dam²", 2), ("m²", 0), ("dm²", -2), ("cm²", -4),
                               ("mm²", -6)], 2),
    VOLUME: _per_eenheid([("m³", 6), ("dm³", 3), ("cm³", 0)], 3),
}
VAKJES = {OPPERVLAKTE: 2, VOLUME: 3}  # vakjes per eenheid (anders 1)
# andere namen voor een vakje: getoond in een tweede kopregel
ALIASSEN = {
    OPPERVLAKTE: [("ha", 4), ("a", 2), ("ca", 0)],
    VOLUME: [("hl", 5), ("dal", 4), ("l", 3), ("dl", 2), ("cl", 1), ("ml", 0)],
}
# deze andere namen staan precies op het vakje van een echte eenheid (de rest, zoals dl, zit ertussen)
ZELFDE_ALS = {"ha": "hm²", "a": "dam²", "ca": "m²", "l": "dm³", "ml": "cm³"}
MACHT_IN = {cat: {**{l: k for l, k, echt in cols if echt}, **dict(ALIASSEN.get(cat, []))}
            for cat, cols in TABELLEN.items()}
EENHEDEN = {cat: list(m) for cat, m in MACHT_IN.items()}
# een eenheid → de eerste soort waarin ze voorkomt (l, dl … staan ook bij volume: zie soorten_van)
CATEGORIE = {}
for _cat in SOORTEN:
    for _u in EENHEDEN[_cat]:
        CATEGORIE.setdefault(_u, _cat)
MACHT = {u: MACHT_IN[c][u] for u, c in CATEGORIE.items()}


def meer_vakjes(v):
    """Geldt hier 'elke eenheid heeft 2 (of 3) vakjes'? Alleen tussen echte eenheden (en ha, l …)."""
    hoofd = {l for l, _, echt in TABELLEN[v.cat] if echt} | set(ZELFDE_ALS)
    return VAKJES.get(v.cat, 1) > 1 and v.van in hoofd and v.naar in hoofd


def soorten_van(eenheid):
    return [cat for cat in SOORTEN if eenheid in MACHT_IN[cat]]


def cw(cat):
    """Breedte van een vakje: smaller als er veel vakjes zijn, zodat de tabel in 80 kolommen past."""
    return CW if len(TABELLEN[cat]) <= 10 else 3


def kolom(cat, eenheid):
    """Index van het vakje van een eenheid in de tabel."""
    m = MACHT_IN[cat][eenheid]
    return next(i for i, (_, k, _) in enumerate(TABELLEN[cat]) if k == m)


def eenheid_bij(cat, i):
    """De naam (of namen) van de eenheid bij vakje i, bv. 'hm² = ha', of None als daar geen eenheid hoort."""
    k = TABELLEN[cat][i][1]
    namen = [u for u, m in MACHT_IN[cat].items() if m == k]
    return " = ".join(namen) if namen else None


def koppen(cat):
    """De kop van de tabel: [(label, eerste vakje, aantal vakjes)]. Lege vakjes horen bij de eenheid rechts."""
    uit, begin = [], 0
    for i, (label, _, echt) in enumerate(TABELLEN[cat]):
        if label == "" and not echt:
            continue
        uit.append((label, begin, i - begin + 1))
        begin = i + 1
    return uit


def alias_kop(cat):
    """Tweede kopregel (bv. ha a ca): [(label, vakje)] of []."""
    return [(label, kolom(cat, label)) for label, _ in ALIASSEN.get(cat, [])]


@dataclass
class Omzetting:
    cat: str
    van: str
    naar: str
    getal: Decimal

    @property
    def stap(self):
        """Aantal vakjes naar rechts (> 0) of naar links (< 0) in de tabel."""
        return MACHT_IN[self.cat][self.van] - MACHT_IN[self.cat][self.naar]

    @property
    def antwoord(self):
        return self.getal.scaleb(self.stap)

    @property
    def sleutel(self):
        """Uniek per vraag; later gebruikt om herhaling binnen 30 dagen te vermijden."""
        return f"{OMZETTEN.id}:{self.van}>{self.naar}:{fmt(self.getal)}"

    @property
    def tekst(self):
        return f"{fmt(self.getal)} {self.van} = ? {self.naar}"


def tabel_bereik(v):
    """Laagste en hoogste kolom (macht van 10) die ingevuld moeten worden."""
    mv, mn = MACHT_IN[v.cat][v.van], MACHT_IN[v.cat][v.naar]
    t = v.getal.scaleb(mv).normalize().as_tuple()
    laag = min(t.exponent, mv, mn)
    hoog = max(len(t.digits) + t.exponent - 1, mv, mn)
    return laag, hoog


def past_in_tabel(v):
    laag, hoog = tabel_bereik(v)
    cols = TABELLEN[v.cat]
    return cols[-1][1] <= laag and hoog <= cols[0][1]


def verwachte_cijfers(v):
    """{macht: cijfer} voor elk vakje dat ingevuld moet worden (inclusief nullen)."""
    basis = v.getal.scaleb(MACHT_IN[v.cat][v.van])
    laag, hoog = tabel_bereik(v)
    return {k: int(basis.scaleb(-k) // 1 % 10) for k in range(laag, hoog + 1)}


def controleer_tabel(v, cellen):
    """Per vakje: True (juist), False (fout) of None (leeg en hoeft niet)."""
    verw = verwachte_cijfers(v)
    res = []
    for (_, k, _), c in zip(TABELLEN[v.cat], cellen):
        if k in verw:
            res.append(c == verw[k])
        elif c is None:
            res.append(None)
        else:
            res.append(c == 0)  # een extra nul vooraan of achteraan mag
    return res


def aflezen(cellen, komma):
    """Leest het getal in de tabel af met de komma achter vakje `komma`. None zonder cijfers."""
    gevuld = [i for i, c in enumerate(cellen) if c is not None]
    if not gevuld:
        return None
    eerste, laatste = min(gevuld[0], komma), max(gevuld[-1], komma)
    cijfers = [str(cellen[i] or 0) for i in range(eerste, laatste + 1)]
    deel = komma - eerste + 1
    voor = "".join(cijfers[:deel]).lstrip("0") or "0"
    na = "".join(cijfers[deel:])
    return voor + ("," + na if na else "")


def _meervoud(n):
    return "plaats" if n == 1 else "plaatsen"


def regel_uitleg(v):
    n = abs(v.stap)
    f = 10 ** n
    pl = _meervoud(n)
    per = VAKJES.get(v.cat, 1)
    if meer_vakjes(v):
        x = "100" if per == 2 else "1000"
        regels = regel_uitleg_gewoon(v, n, f, pl)
        regels.insert(1, f"Bij {NAMEN[v.cat].lower()} heeft elke eenheid {per} vakjes: per eenheid × of : {x}.")
        return regels
    return regel_uitleg_gewoon(v, n, f, pl)


def regel_uitleg_gewoon(v, n, f, pl):
    if v.stap > 0:
        return [f"1 {v.van} = {f} {v.naar}, dus doe je maal {f}.",
                f"Van {v.van} naar {v.naar} ga je {n} {pl} naar rechts in de tabel: "
                f"de komma schuift {n} {pl} naar rechts.",
                f"{fmt(v.getal)} × {f} = {fmt(v.antwoord)}"]
    return [f"1 {v.naar} = {f} {v.van}, dus doe je gedeeld door {f}.",
            f"Van {v.van} naar {v.naar} ga je {n} {pl} naar links in de tabel: "
            f"de komma schuift {n} {pl} naar links.",
            f"{fmt(v.getal)} : {f} = {fmt(v.antwoord)}"]


def tabel_uitleg(v):
    if not past_in_tabel(v):
        return []
    if VAKJES.get(v.cat, 1) > 1:
        uitleg = f" (elke eenheid heeft {VAKJES[v.cat]} vakjes)" if meer_vakjes(v) else ""
        return [f"In de tabel: komma achter {v.van}{uitleg}.",
                f"Vul aan met nullen en lees af met de komma achter {v.naar}: {fmt(v.antwoord)} {v.naar}."]
    verw = verwachte_cijfers(v)
    namen = {k: lab for lab, k, _ in TABELLEN[v.cat]}
    delen = ", ".join(f"{verw[k]} bij {namen[k]}" for k in sorted(verw, reverse=True))
    return [f"In de tabel: komma achter {v.van}, dus {delen}.",
            f"Lees af met de komma achter {v.naar}: {fmt(v.antwoord)} {v.naar}."]


# korte omschrijving per diagnosecode (voor rapporten)
DENKFOUTEN = {
    "niet_omgezet": "het getal overgeschreven zonder om te zetten",
    "verkeerde_richting": "de komma de verkeerde kant op geschoven",
    "factor_10": "een of meer kolommen te ver of te weinig geteld",
    "een_vakje_per_eenheid": "bij oppervlakte of volume maar 1 vakje per eenheid geteld",
}
_ALLE_DENKFOUTEN.update(DENKFOUTEN)


def diagnose(v, gegeven):
    """Herkent typische denkfouten. Geeft (code, uitleg) of None als we het niet weten."""
    if gegeven is None or gegeven == v.antwoord:
        return None
    richting = "rechts" if v.stap > 0 else "links"
    if gegeven == v.getal:
        return ("niet_omgezet",
                f"Je schreef het getal over zonder om te zetten. Van {v.van} naar {v.naar} "
                f"schuift de komma {abs(v.stap)} {_meervoud(abs(v.stap))} naar {richting}.")
    if gegeven == v.getal.scaleb(-v.stap):
        return ("verkeerde_richting",
                f"Je schoof de komma de verkeerde kant op. Van {v.van} naar {v.naar} "
                f"gaat het naar {richting} in de tabel.")
    per = VAKJES.get(v.cat, 1)
    if meer_vakjes(v) and v.stap % per == 0 and gegeven == v.getal.scaleb(v.stap // per):
        x = "100" if per == 2 else "1000"
        return ("een_vakje_per_eenheid",
                f"Je schoof de komma maar 1 plaats per eenheid. Bij {NAMEN[v.cat].lower()} heeft elke eenheid "
                f"{per} vakjes: per eenheid is het × of : {x}.")
    for k in range(1, 7):
        for teken in (1, -1):
            if gegeven == v.antwoord.scaleb(teken * k):
                te = "ver" if (teken > 0) == (v.stap > 0) else "weinig"
                return ("factor_10",
                        f"Je zit er {k} {_meervoud(k)} naast: de komma ging {k} {_meervoud(k)} te {te}. "
                        f"Tel de kolommen van {v.van} naar {v.naar} nog eens.")
    return None


def onderwerp(v, tabel=False):
    """Het onderwerp van een vraag (voor herhaling en gewichten): bv. 'km>m' of 'km>m|tabel'."""
    return f"{v.van}>{v.naar}" + ("|tabel" if tabel else "")


def onderwerp_van_sleutel(sleutel):
    """'wiskunde.eenheden.omzetten:km>m:3,5' -> 'km>m' (of None als het geen omzetting is)."""
    delen = sleutel.split(":")
    if len(delen) != 3 or delen[0] != OMZETTEN.id:
        return None
    return delen[1]


def herhaal_data(v, tabel=False):
    """Wat de herhaalbak moet onthouden om later een gelijkaardige vraag (met een nieuw getal) te maken."""
    return {"van": v.van, "naar": v.naar, "tabel": tabel, "cat": v.cat}


def maak_herhaling(data, leerjaar, vermijd=()):
    return maak_vraag([data["van"], data["naar"]], leerjaar, data.get("tabel", False),
                      paar=(data["van"], data["naar"]), vermijd=vermijd, cat=data.get("cat"))


def eenheden_voor(leerjaar):
    """Alle eenheden van de soorten die in dit leerjaar aan bod komen."""
    p = leerlijnen.parameters(OMZETTEN.id, leerjaar)
    return [u for cat in p["soorten"] for u in EENHEDEN[cat]]


def _paren(eenheden, cat=None):
    """Mogelijke (van, naar, soort): beide eenheden in dezelfde soort. Een eenheid die in twee soorten staat
    (l, dl …), komt in de soort waar de meeste gekozen eenheden in zitten."""
    gekozen = set(eenheden)
    soorten = [cat] if cat else sorted(SOORTEN, key=lambda c: -len(gekozen & set(EENHEDEN[c])))
    paren, gezien = [], set()
    for c in soorten:
        for a in EENHEDEN[c]:
            for b in EENHEDEN[c]:
                if a != b and a in gekozen and b in gekozen and (a, b) not in gezien:
                    gezien.add((a, b))
                    paren.append((a, b, c))
    return paren


def maak_vraag(eenheden, leerjaar, tabel=False, vorige=None, paar=None, vermijd=(), gewichten=None, cat=None):
    """Maakt een willekeurige omzetting tussen twee gekozen eenheden van dezelfde soort.

    De moeilijkheid komt uit de leerlijn van het gegeven leerjaar. Lukt het niet binnen die
    grenzen (bv. door een vreemde keuze van eenheden), dan worden de grenzen wat losser.
    paar = vaste (van, naar); vermijd = vraagsleutels die recent al kwamen;
    gewichten = {"km>m": 2.5, …} om moeilijke omzettingen vaker te kiezen.
    """
    p = leerlijnen.parameters(OMZETTEN.id, leerjaar)
    los = leerlijnen.parameters(OMZETTEN.id, "m2")
    paren = _paren(paar or eenheden, cat if cat in TABELLEN else None)
    if paar:
        paren = [q for q in paren if q[:2] == tuple(paar)][:1]
    if not paren:
        raise ValueError("kies minstens 2 eenheden van dezelfde soort")

    def eenheidstappen(q):
        a, b, c = q
        return abs(MACHT_IN[c][a] - MACHT_IN[c][b]) // VAKJES.get(c, 1)

    kort = [q for q in paren if eenheidstappen(q) <= p["max_stap"]]
    paren = kort or paren
    w = None
    if gewichten:
        w = [gewichten.get(f"{a}>{b}", 1.0) for a, b, _ in paren]
    for poging in range(6000):
        nv = p if poging < 3000 else los
        van, naar, c = random.choices(paren, weights=w, k=1)[0] if w else random.choice(paren)
        n = random.randint(*nv["cijfers"])
        m = random.randint(10 ** (n - 1), 10 ** n - 1)
        if n > 1 and m % 10 == 0:
            continue
        v = Omzetting(c, van, naar, Decimal(m).scaleb(random.randint(-3, 4)))
        if decimalen(v.getal) > nv["dec_getal"] or decimalen(v.antwoord) > nv["dec_antw"]:
            continue
        if v.getal >= nv["max_getal"] or v.antwoord >= nv["max_antw"]:
            continue
        if tabel and not past_in_tabel(v):
            continue
        if vorige and vorige.sleutel == v.sleutel:
            continue
        if v.sleutel in vermijd and poging < 2000:  # lukt het niet, dan toch maar een eerder gezien getal
            continue
        return v
    van, naar, c = random.choice(paren)
    return Omzetting(c, van, naar, Decimal(1))


# --- spiekbrief (tekst + rol; de weergave kiest de kleur) ---------------------

def cel_tekst(cijfer, komma, fout=False, breedte=CW):
    s = [" "] * breedte
    if fout:
        s[0] = "!"
    if cijfer is not None:
        s[breedte // 2] = str(cijfer)
    if komma:
        s[breedte - 1] = ","
    return "".join(s)


def kop_tekst(cat):
    """De kopregel(s) van de tabel als tekst (de koppen lopen over al hun vakjes)."""
    b = cw(cat)
    delen = [label.center(n * (b + 1) - 1) for label, _, n in koppen(cat)]
    regels = ["│" + "│".join(delen) + "│"]
    if ALIASSEN.get(cat):
        rij = [" " * b for _ in TABELLEN[cat]]
        for label, i in alias_kop(cat):
            rij[i] = label.center(b)[:max(b, len(label))]
        regels.append("│" + "│".join(rij) + "│")
    return regels


def tabel_tekst(cat, cijfers=None, komma=None):
    """De tabel als gewone tekstregels."""
    cols = TABELLEN[cat]
    b = cw(cat)
    n = len(cols)
    lijn = lambda l, m, r: l + m.join(["─" * b] * n) + r
    regels = [lijn("┌", "┬", "┐"), *kop_tekst(cat)]
    if cijfers is not None:
        regels.append(lijn("├", "┼", "┤"))
        regels.append("│" + "│".join(cel_tekst(cijfers.get(k), k == komma, breedte=b) for _, k, _ in cols) + "│")
    regels.append(lijn("└", "┴", "┘"))
    return regels


def spiekbrief():
    """Regels (tekst, rol) met de uitleg over de eenhedentabel."""
    vb = Omzetting(LENGTE, "m", "cm", Decimal("4.25"))
    return [
        ("Hoe werkt omzetten?", "accent"),
        ("  • Elke kolom naar rechts is 10 keer kleiner: je doet maal 10.", ""),
        ("  • Elke kolom naar links is 10 keer groter: je doet gedeeld door 10.", ""),
        ("  • Zet het getal in de tabel met de komma achter de eenheid die je krijgt.", ""),
        ("  • Vul aan met nullen tot de eenheid die gevraagd wordt en lees af.", ""),
        ("", ""),
        ("LENGTE", "accent"),
        *[("  " + r, "") for r in tabel_tekst(LENGTE)],
        ("  1 km = 1000 m      1 m = 10 dm = 100 cm = 1000 mm      1 cm = 10 mm", "accent2"),
        ("  km = kilometer, hm = hectometer, dam = decameter, m = meter,", "dim"),
        ("  dm = decimeter, cm = centimeter, mm = millimeter", "dim"),
        ("  Ezelsbruggetje: Koning Hendrik Dronk Elke Dag Chocolade Melk", "dim"),
        ("", ""),
        ("MASSA", "accent"),
        *[("  " + r, "") for r in tabel_tekst(MASSA)],
        ("  1 t = 1000 kg      1 kg = 1000 g      1 g = 1000 mg      1 kg = 10 hg", "accent2"),
        ("  t = ton, kg = kilogram, hg = hectogram, dag = decagram, g = gram,", "dim"),
        ("  dg = decigram, cg = centigram, mg = milligram", "dim"),
        ("  Tussen t en kg zitten twee lege kolommen (100 kg en 10 kg).", "dim"),
        ("", ""),
        ("VOORBEELD:  4,25 m = ? cm", "accent"),
        ("  1. Zet 4,25 in de tabel met de komma achter m:", ""),
        *[("     " + r, "") for r in tabel_tekst(LENGTE, verwachte_cijfers(vb), 0)],
        ("  2. De komma springt naar cm. Lees af:", ""),
        *[("     " + r, "") for r in tabel_tekst(LENGTE, verwachte_cijfers(vb), -2)],
        ("  3. 4,25 m = 425 cm", "bold"),
        ("", ""),
        ("  Nog een: 5 mm = ? m → 0 bij m, 0 bij dm, 0 bij cm, 5 bij mm → 0,005 m", ""),
        ("", ""),
        ("INHOUD", "accent"),
        *[("  " + r, "") for r in tabel_tekst(INHOUD)],
        ("  1 l = 10 dl = 100 cl = 1000 ml      1 hl = 100 l", "accent2"),
        ("  hl = hectoliter, dal = decaliter, l = liter,", "dim"),
        ("  dl = deciliter, cl = centiliter, ml = milliliter", "dim"),
        ("", ""),
        ("OPPERVLAKTE  (5de leerjaar)", "accent"),
        *[("  " + r, "") for r in tabel_tekst(OPPERVLAKTE)],
        ("  Elke eenheid heeft 2 vakjes: per eenheid × of : 100.", ""),
        ("  1 m² = 100 dm² = 10 000 cm²    1 ha = 1 hm² = 10 000 m²    1 a = 100 m²", "accent2"),
        ("  ha = hectare, a = are, ca = centiare (= 1 m²)", "dim"),
        ("", ""),
        ("VOLUME  (6de leerjaar)", "accent"),
        *[("  " + r, "") for r in tabel_tekst(VOLUME)],
        ("  Elke eenheid heeft 3 vakjes: per eenheid × of : 1000.", ""),
        ("  1 m³ = 1000 dm³      1 dm³ = 1 l      1 cm³ = 1 ml", "accent2"),
        ("  De literkolommen staan onder dm³ en cm³: zo zie je meteen dat 1 l = 1 dm³.", "dim"),
    ]
