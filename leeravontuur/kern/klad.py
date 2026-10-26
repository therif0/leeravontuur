"""Het kladblad: rekenregels lezen en nakijken zoals het kind ze typt.

Een regel is bv. `0,75 x 3,20 = 2,40`, `750 g = 0,75 kg`, `25 % van 80 = 20`, `25 : 4 = 6 rest 1`,
`2 u 15 min = 135 min` of met een label ervoor: `kersen: 0,75 x 3,20 = 2,40`.
Maal mag als x, X of *, delen als : of /, min als -. Het kind hoeft dus nooit een speciaal teken te typen;
`netjes` toont de regel daarna met × : −.

Elke `=` wordt nagekeken (exact, met Fraction). Wat het kind schreef blijft bewaard, zodat een vraagstuk het
klad kan vergelijken met de juiste stappen en de bekende foute paden.
"""

import re
from dataclasses import dataclass, field
from fractions import Fraction

from .getal import lees_getal
from .wiskunde import eenheden as E

PLUS, MIN, MAAL, DEEL, VAN = "+", "−", "×", ":", "van"
OPS = {"+": PLUS, "-": MIN, "−": MIN, "–": MIN, "x": MAAL, "X": MAAL, "×": MAAL, "*": MAAL, "·": MAAL,
       ":": DEEL, "/": DEEL, "÷": DEEL}
OP_NAAM = {PLUS: "optellen", MIN: "aftrekken", MAAL: "vermenigvuldigen", DEEL: "delen", VAN: "vermenigvuldigen"}

# eenheden buiten de eenhedentabel: (soort, factor tegenover de kleinste)
TIJD = {"s": 1, "sec": 1, "seconden": 1, "min": 60, "minuten": 60, "minuut": 60, "u": 3600, "uur": 3600,
        "uren": 3600, "dag": 86400, "dagen": 86400, "week": 604800, "weken": 604800}
GELD = {"€": 100, "euro": 100, "eur": 100, "cent": 1, "c": 1}
SNELHEID = {"km/u": 1, "km/h": 1, "m/s": Fraction(18, 5)}
KLEINER = {"u": "min", "uur": "min", "min": "s", "€": "cent", "euro": "cent", "m": "cm", "kg": "g"}


def soort_van(eenheid):
    """(soort, factor) voor een eenheid, of (None, None) als het programma ze niet kan omzetten."""
    e = (eenheid or "").lower()
    if e in TIJD:
        return "tijd", Fraction(TIJD[e])
    if e in GELD:
        return "geld", Fraction(GELD[e])
    if e in SNELHEID:
        return "snelheid", Fraction(SNELHEID[e])
    e = e.replace("2", "²").replace("3", "³")
    if e in E.CATEGORIE:
        return E.CATEGORIE[e], Fraction(10) ** E.MACHT[e]
    return None, None


@dataclass
class Grootheid:
    """Een getal met (misschien) een eenheid. `basis` = de waarde in de kleinste eenheid (om om te zetten)."""
    getal: Fraction
    eenheid: str = ""
    soort: str | None = None
    basis: Fraction | None = None
    rest: Fraction | None = None   # bij `6 rest 1`


@dataclass
class Schakel:
    """Eén `=` in een regel: links = rechts."""
    ops: list                 # de bewerkingen links (leeg = omzetten of gewoon een getal)
    operanden: list           # de getallen links (Fraction), in volgorde
    gegeven: Grootheid        # wat het kind rechts schreef
    echt: Fraction | None     # wat links uitkomt (None als het niet te rekenen is, bv. delen door 0)
    juist: bool
    soort: str = "reken"      # "reken" of "omzet"
    afgerond: bool = False
    ketting: bool = False     # `3 x 4 = 12 + 3 = 15`: rechts rekende het kind verder
    links_tekst: str = ""
    links: Grootheid | None = None


@dataclass
class KladRegel:
    tekst: str
    netjes: str = ""
    label: str = ""
    schakels: list = field(default_factory=list)
    melding: str = ""          # wat er mis is (zonder het antwoord te verklappen)
    leesbaar: bool = True

    @property
    def juist(self):
        """True/False, of None als er niets na te kijken is (geen =)."""
        if not self.leesbaar or not self.schakels:
            return None
        return all(s.juist for s in self.schakels)

    @property
    def uitkomst(self):
        """Het laatste getal dat het kind schreef (de uitkomst van de regel)."""
        return self.schakels[-1].gegeven.getal if self.schakels else None


# ---- lezen ---------------------------------------------------------------------------------------------

def _tokens(tekst):
    """Lijst van (soort, waarde, tekst): getal, op, (, ), =, ≈, %, eenheid, woord, rest."""
    uit, i, t = [], 0, tekst
    while i < len(t):
        c = t[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit():
            m = re.match(r"\d{1,3}(?: \d{3})+(?![\d.,])|\d+(?:[.,]\d+)*", t[i:])  # ook 300 000
            uit.append(("getal", m.group(0).replace(" ", ""), m.group(0)))
            i += len(m.group(0))
            continue
        if c in "()":
            uit.append((c, c, c))
        elif c in "=≈":
            uit.append(("=", c, c))
        elif c == "%":
            uit.append(("%", c, c))
        elif c in OPS and c not in "xX":
            uit.append(("op", OPS[c], c))
        elif c == "€":
            uit.append(("eenheid", "€", "€"))
        elif c.isalpha():
            m = re.match(r"[A-Za-zÀ-ÿ]+[²³23]?(?:/[a-z]+)?", t[i:])
            w = m.group(0)
            if w[-1] in "23" and soort_van(w)[0] is None:  # 2u30: de 3 hoort bij het getal
                w = w[:-1]
            lw = w.lower()
            vorige = uit[-1][0] if uit else None
            if lw == "x" and vorige in ("getal", ")", "eenheid", "%", "woord"):
                uit.append(("op", MAAL, w))
            elif lw == "van":
                uit.append(("op", VAN, w))
            elif lw in ("rest", "r"):
                uit.append(("rest", "rest", w))
            elif soort_van(lw)[0]:
                uit.append(("eenheid", w, w))
            else:
                uit.append(("woord", w, w))
            i += len(w)
            continue
        else:
            return None
        i += 1
    return uit


def _getal(tekst):
    g = lees_getal(tekst)
    return None if g is None else Fraction(g)


class _Fout(Exception):
    pass


class _Lezer:
    """Rekent één deel (tussen twee =) uit. Eenheden tellen bij + en − niet mee, behalve bij omzetten."""

    def __init__(self, tokens):
        self.t = tokens
        self.i = 0
        self.ops, self.operanden = [], []

    def kijk(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None, None)

    def neem(self):
        tok = self.kijk()
        self.i += 1
        return tok

    def expr(self):
        w = self.term()
        while self.kijk()[0] == "op" and self.kijk()[1] in (PLUS, MIN):
            op = self.neem()[1]
            self.ops.append(op)
            r = self.term()
            w = _reken(op, w, r)
        return w

    def term(self):
        w = self.factor()
        while self.kijk()[0] == "op" and self.kijk()[1] in (MAAL, DEEL, VAN):
            op = self.neem()[1]
            self.ops.append(op)
            r = self.factor()
            w = _reken(op, w, r)
        return w

    def factor(self):
        soort, waarde, _ = self.kijk()
        if soort == "op" and waarde == MIN:
            self.neem()
            return -self.factor()
        if soort == "(":
            self.neem()
            w = self.expr()
            if self.neem()[0] != ")":
                raise _Fout("haakje")
            return w
        if soort == "eenheid" and waarde == "€":  # € 3,20
            self.neem()
            soort, waarde, _ = self.kijk()
        if soort != "getal":
            raise _Fout("getal verwacht")
        self.neem()
        g = _getal(waarde)
        if g is None:
            raise _Fout("getal")
        self.operanden.append(g)
        while self.kijk()[0] in ("eenheid", "woord"):  # 3 zakjes, 750 g
            self.neem()
        if self.kijk()[0] == "%":
            self.neem()
            return g / 100
        return g


def _reken(op, a, b):
    if a is None or b is None:
        return None
    if op == PLUS:
        return a + b
    if op == MIN:
        return a - b
    if op in (MAAL, VAN):
        return a * b
    return a / b if b else None


def _grootheid(tokens):
    """Een deel dat alleen een getal (met eenheden) is: 750 g, € 3,20, 2 u 15 min, 6 rest 1. Anders None."""
    euro_voor = bool(tokens) and tokens[0][:2] == ("eenheid", "€")
    toks = tokens[1:] if euro_voor else tokens
    if not toks or toks[0][0] != "getal":
        return None
    # 6 rest 1
    if len(toks) == 3 and toks[1][0] == "rest" and toks[2][0] == "getal":
        q, r = _getal(toks[0][1]), _getal(toks[2][1])
        return None if q is None or r is None else Grootheid(q, "", None, None, r)
    paren, j = [], 0
    while j < len(toks):
        if toks[j][0] != "getal":
            return None
        g = _getal(toks[j][1])
        if g is None:
            return None
        eenheid = ""
        j += 1
        while j < len(toks) and toks[j][0] in ("eenheid", "woord"):
            eenheid = (eenheid + " " + toks[j][1]).strip()
            j += 1
        if not eenheid and paren and paren[-1][1].lower() in KLEINER:  # 2 u 30 = 2 u 30 min
            eenheid = KLEINER[paren[-1][1].lower()]
        paren.append((g, eenheid))
    if euro_voor:
        paren[0] = (paren[0][0], "€")
    if len(paren) == 1:
        g, e = paren[0]
        soort, factor = soort_van(e)
        return Grootheid(g, e, soort, g * factor if factor else None)
    # samengesteld (2 u 15 min, 3 m 40 cm): alles van dezelfde soort, uitgedrukt in de laatste eenheid
    soorten = [soort_van(e) for _, e in paren]
    if any(s is None for s, _ in soorten) or len({s for s, _ in soorten}) > 1:
        return None
    basis = sum(g * f for (g, _), (_, f) in zip(paren, soorten))
    laatste = soorten[-1][1]
    return Grootheid(basis / laatste, paren[-1][1], soorten[0][0], basis)


def _decimalen(tekst):
    m = re.search(r"[.,](\d+)$", tekst)
    if not m or re.fullmatch(r"[1-9]\d{0,2}(\.\d{3})+", tekst):
        return 0
    return len(m.group(1))


def _afronding_ok(echt, gegeven_tekst, gegeven):
    """Is `gegeven` de afronding van `echt` op het aantal cijfers na de komma dat het kind schreef?"""
    if echt is None:
        return False
    n = _decimalen(gegeven_tekst)
    stap = Fraction(1, 10 ** n)
    return abs(echt - gegeven) <= stap / 2 and echt != gegeven


def _netjes(tokens):
    uit, plak = [], False
    for i, (soort, waarde, tekst) in enumerate(tokens):
        if soort == "getal":
            tekst = tekst.replace(".", ",") if _decimalen(tekst) else tekst
        elif soort == "op":
            fractie = tekst == "/" and i + 2 < len(tokens) and tokens[i + 2][1] == VAN  # 3/4 van 24
            tekst = "/" if fractie else waarde
            if fractie:
                uit.append(tekst)
                plak = True
                continue
        elif soort == "eenheid" and tekst[-1] in "23":
            tekst = tekst[:-1] + ("²" if tekst[-1] == "2" else "³")
        if uit and soort != ")" and tokens[i - 1][0] != "(" and not plak:
            uit.append(" ")
        plak = False
        uit.append(tekst)
    return "".join(uit)


def lees_regel(tekst):
    """Leest en kijkt één kladregel na → KladRegel."""
    regel = KladRegel(tekst)
    t = (tekst or "").strip()
    if not t:
        regel.leesbaar = False
        return regel
    m = re.match(r"\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]*?)\s*:\s*(?=\S)", t)
    if m and not re.search(r"\d", m.group(1)):
        regel.label, t = m.group(1), t[m.end():]
    tokens = _tokens(t)
    if tokens is None:
        regel.leesbaar = False
        regel.melding = "Dit kan ik niet lezen. Gebruik getallen en + - x : ="
        return regel
    delen, huidig = [], []
    for tok in tokens:
        if tok[0] == "=":
            delen.append(huidig)
            huidig = []
        else:
            huidig.append(tok)
    delen.append(huidig)
    # een label als eerste deel: `prijs = 0,75 x 3,20 = 2,40`
    if len(delen) > 1 and delen[0] and all(x[0] == "woord" for x in delen[0]):
        regel.label = (regel.label + " " + " ".join(x[1] for x in delen[0])).strip()
        delen = delen[1:]
        tokens = [x for d in delen for x in d + [("=", "=", "=")]][:-1]
    regel.netjes = (regel.label + ": " if regel.label else "") + _netjes(tokens)
    if any(not d for d in delen):
        if len(delen) == 2 and delen[0]:
            regel.melding = "Schrijf ook de uitkomst: … = ?"
        else:
            regel.leesbaar = False
            regel.melding = "Er ontbreekt iets rond het =-teken."
        return regel
    try:
        waarden = []
        for d in delen:
            lz = _Lezer(d)
            w = lz.expr()
            if lz.i != len(d) and _grootheid(d) is None:
                raise _Fout("rest")
            waarden.append((w, lz, _grootheid(d)))
    except (_Fout, ZeroDivisionError):
        regel.leesbaar = False
        regel.melding = "Dit kan ik niet lezen. Kijk je getallen en tekens na."
        return regel
    if len(delen) == 1:  # alleen een getal of een bewerking zonder =
        regel.melding = "" if not waarden[0][1].ops else "Schrijf ook de uitkomst: … = ?"
        return regel
    for (wl, ll, gl), (wr, lr, gr), dl in zip(waarden, waarden[1:], delen):
        gegeven = gr if gr is not None else Grootheid(wr, "")
        links_tekst = _netjes(dl)
        if not ll.ops and gl is not None:  # omzetten: 750 g = 0,75 kg
            if gl.basis is not None and gegeven.basis is not None and gl.soort == gegeven.soort:
                juist = gl.basis == gegeven.basis
            else:
                juist = gl.getal == gegeven.getal
            regel.schakels.append(Schakel([], [gl.getal], gegeven, gl.getal, juist, "omzet",
                                          links_tekst=links_tekst, links=gl))
            continue
        echt = wl
        if gegeven.rest is not None:  # 25 : 4 = 6 rest 1
            ok = (ll.ops == [DEEL] and len(ll.operanden) == 2 and gegeven.getal.denominator == 1
                  and gegeven.rest.denominator == 1 and 0 <= gegeven.rest < ll.operanden[1]
                  and gegeven.getal * ll.operanden[1] + gegeven.rest == ll.operanden[0])
            regel.schakels.append(Schakel(ll.ops, ll.operanden, gegeven, echt, ok, links_tekst=links_tekst))
            continue
        juist = echt is not None and echt == gegeven.getal
        afgerond = False
        if not juist and echt is not None and lr.ops == [] and gr is not None:
            getal_tekst = next(x[1] for x in delen[len(regel.schakels) + 1] if x[0] == "getal")
            afgerond = juist = _afronding_ok(echt, getal_tekst, gegeven.getal)
        ketting = False
        if not juist and lr.ops and lr.operanden and echt == lr.operanden[0]:
            # 3 x 4 = 12 + 3: links klopt met het begin van rechts, het kind rekende gewoon verder
            juist = ketting = True
            gegeven = Grootheid(lr.operanden[0], "")
        regel.schakels.append(Schakel(ll.ops, ll.operanden, gegeven, echt, juist, afgerond=afgerond,
                                      ketting=ketting, links_tekst=links_tekst))
    if any(s.ketting for s in regel.schakels):
        regel.melding = "Tip: schrijf elke stap op een nieuwe regel, dan klopt elk =-teken."
    fout = next((s for s in regel.schakels if not s.juist), None)
    if fout:
        regel.melding = rekenfout_tekst(fout)
    return regel


def rekenfout_tekst(s):
    """Wat er mis is met een schakel, zonder de juiste uitkomst te verklappen."""
    if s.echt is None:
        return f"{s.links_tekst} kan niet: je kan niet delen door 0."
    if s.soort == "omzet":
        if s.links and s.gegeven.basis is not None and s.links.basis is not None and s.links.basis:
            q = s.gegeven.basis / s.links.basis
            if q in (10, 100, 1000, Fraction(1, 10), Fraction(1, 100), Fraction(1, 1000)):
                return f"{s.links_tekst} omzetten: de komma staat verkeerd. Gebruik de eenhedentabel."
        if s.links and s.links.soort and s.gegeven.soort and s.links.soort != s.gegeven.soort:
            return f"{s.links.eenheid} en {s.gegeven.eenheid} kun je niet in elkaar omzetten."
        return f"Kijk je omzetting na: {s.links_tekst} = ?"
    if s.gegeven.rest is not None:
        return f"{s.links_tekst}: kijk de rest na (de rest moet kleiner zijn dan het getal waardoor je deelt)."
    g, e = s.gegeven.getal, s.echt
    if e and g:
        q = g / e
        if q in (10, 100, 1000, Fraction(1, 10), Fraction(1, 100), Fraction(1, 1000)):
            return f"{s.links_tekst}: bijna! Kijk naar de komma."
    if len(s.operanden) == 2 and len(s.ops) == 1:
        a, b = s.operanden
        for op in (PLUS, MIN, MAAL, DEEL):
            if op != s.ops[0] and _reken(op, a, b) == g and not (op == MAAL and s.ops[0] == VAN):
                return f"{s.links_tekst}: je schreef {s.ops[0]}, maar je rekende {op}."
    return f"Reken {s.links_tekst} nog eens na."


def lees_klad(regels):
    return [lees_regel(r) for r in regels]
