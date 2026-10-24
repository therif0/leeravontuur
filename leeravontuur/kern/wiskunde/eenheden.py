"""Eenheden omzetten: lengte (km … mm) en massa (t … mg) met de eenhedentabel.

Alles hier is zuivere logica: vragen maken, nakijken, uitleggen en denkfouten herkennen.
Teksten voor de spiekbrief krijgen een rol ("accent", "dim" …) in plaats van een kleur.
"""

import random
from dataclasses import dataclass
from decimal import Decimal

from .. import leerlijnen
from ..getal import decimalen, fmt
from ..vaardigheden import DENKFOUTEN as _ALLE_DENKFOUTEN, Vaardigheid, registreer

OMZETTEN = registreer(Vaardigheid(
    "wiskunde.eenheden.omzetten", "Eenheden omzetten",
    "lengte en massa herleiden met de eenhedentabel"))

MASSA, LENGTE = "massa", "lengte"
CW = 5  # breedte van een vakje in de tabel

# Kolommen van de tabel: (label, macht van 10 t.o.v. g of m, echte eenheid?)
TABELLEN = {
    MASSA: [("t", 6, True), ("100kg", 5, False), ("10kg", 4, False), ("kg", 3, True),
            ("hg", 2, True), ("dag", 1, True), ("g", 0, True), ("dg", -1, True),
            ("cg", -2, True), ("mg", -3, True)],
    LENGTE: [("km", 3, True), ("hm", 2, True), ("dam", 1, True), ("m", 0, True),
             ("dm", -1, True), ("cm", -2, True), ("mm", -3, True)],
}
EENHEDEN = {cat: [l for l, _, echt in cols if echt] for cat, cols in TABELLEN.items()}
MACHT = {l: k for cols in TABELLEN.values() for l, k, echt in cols if echt}
CATEGORIE = {u: cat for cat, us in EENHEDEN.items() for u in us}


@dataclass
class Omzetting:
    cat: str
    van: str
    naar: str
    getal: Decimal

    @property
    def stap(self):
        """Aantal kolommen naar rechts (> 0) of naar links (< 0) in de tabel."""
        return MACHT[self.van] - MACHT[self.naar]

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
    t = v.getal.scaleb(MACHT[v.van]).normalize().as_tuple()
    laag = min(t.exponent, MACHT[v.van], MACHT[v.naar])
    hoog = max(len(t.digits) + t.exponent - 1, MACHT[v.van], MACHT[v.naar])
    return laag, hoog


def past_in_tabel(v):
    laag, hoog = tabel_bereik(v)
    cols = TABELLEN[v.cat]
    return cols[-1][1] <= laag and hoog <= cols[0][1]


def verwachte_cijfers(v):
    """{macht: cijfer} voor elk vakje dat ingevuld moet worden (inclusief nullen)."""
    basis = v.getal.scaleb(MACHT[v.van])
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
    for k in range(1, 7):
        for teken in (1, -1):
            if gegeven == v.antwoord.scaleb(teken * k):
                te = "ver" if (teken > 0) == (v.stap > 0) else "weinig"
                return ("factor_10",
                        f"Je zit er {k} {_meervoud(k)} naast: de komma ging {k} {_meervoud(k)} te {te}. "
                        f"Tel de kolommen van {v.van} naar {v.naar} nog eens.")
    return None


def maak_vraag(eenheden, leerjaar, tabel=False, vorige=None):
    """Maakt een willekeurige omzetting tussen twee gekozen eenheden van dezelfde soort.

    De moeilijkheid komt uit de leerlijn van het gegeven leerjaar. Lukt het niet binnen die
    grenzen (bv. door een vreemde keuze van eenheden), dan worden de grenzen wat losser.
    """
    p = leerlijnen.parameters(OMZETTEN.id, leerjaar)
    los = leerlijnen.parameters(OMZETTEN.id, "m2")
    paren = [(a, b) for a in eenheden for b in eenheden
             if a != b and CATEGORIE[a] == CATEGORIE[b]]
    if not paren:
        raise ValueError("kies minstens 2 eenheden van dezelfde soort")
    kort = [q for q in paren if abs(MACHT[q[0]] - MACHT[q[1]]) <= p["max_stap"]]
    paren = kort or paren
    for poging in range(6000):
        nv = p if poging < 3000 else los
        van, naar = random.choice(paren)
        n = random.randint(*nv["cijfers"])
        m = random.randint(10 ** (n - 1), 10 ** n - 1)
        if n > 1 and m % 10 == 0:
            continue
        v = Omzetting(CATEGORIE[van], van, naar, Decimal(m).scaleb(random.randint(-3, 4)))
        if decimalen(v.getal) > nv["dec_getal"] or decimalen(v.antwoord) > nv["dec_antw"]:
            continue
        if v.getal >= nv["max_getal"] or v.antwoord >= nv["max_antw"]:
            continue
        if tabel and not past_in_tabel(v):
            continue
        if vorige and vorige.sleutel == v.sleutel:
            continue
        return v
    van, naar = random.choice(paren)
    return Omzetting(CATEGORIE[van], van, naar, Decimal(1))


# --- spiekbrief (tekst + rol; de weergave kiest de kleur) ---------------------

def cel_tekst(cijfer, komma, fout=False):
    s = [" "] * CW
    if fout:
        s[0] = "!"
    if cijfer is not None:
        s[2] = str(cijfer)
    if komma:
        s[4] = ","
    return "".join(s)


def tabel_tekst(cat, cijfers=None, komma=None):
    """De tabel als gewone tekstregels."""
    cols = TABELLEN[cat]
    n = len(cols)
    lijn = lambda l, m, r: l + m.join(["─" * CW] * n) + r
    regels = [lijn("┌", "┬", "┐"), "│" + "│".join(l.center(CW) for l, _, _ in cols) + "│"]
    if cijfers is not None:
        regels.append(lijn("├", "┼", "┤"))
        regels.append("│" + "│".join(cel_tekst(cijfers.get(k), k == komma) for _, k, _ in cols) + "│")
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
    ]
