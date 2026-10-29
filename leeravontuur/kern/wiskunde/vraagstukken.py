"""Vraagstukken: een verhaalmachine (rekenstructuur × wereld × verwoording × getallen) en het nakijken van het klad.

- Een **rekenstructuur** (hieronder, als Python) kiest mooie getallen en beschrijft de oplossing als stappen
  (bewerking, operanden, wat je ermee vindt, een tip zonder getallen en het waarom met getallen).
- Een **wereld** (inhoud/vraagstukken/werelden.json) levert de woorden en realistische bereiken: een bakker met
  platen broodjes, een metselaar met rijen bakstenen … Dezelfde structuur in een andere wereld = een ander verhaal
  met dezelfde bewerking. Zo werkt de herhaling: het onderwerp is de structuur.
- De **verwoordingen** (inhoud/vraagstukken/zinnen.json) maken er zinnen van, soms in een andere volgorde en
  soms met een overbodig gegeven.
- De **foute paden** komen automatisch uit de stappen: een andere bewerking, gestopt na een tussenstap, een stap
  vergeten, niet omgezet, een overbodig gegeven gebruikt, de komma … Zo herkent de diagnose ze bij elk verhaal.
"""

import json
import math
import re
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from .. import verhaal as V
from ..getal import fmt, fmt_groot, lees_getal
from ..klad import analyseer, lees_regel
from ..modellen import Gegeven, Keuze, Rekenstap, Speur, Verhaal
from ..onderwerp import Onderwerp, Vraag
from .grootheden import duur_tekst, klok_tekst, lees_duur, lees_klok
from .procenten import geld

D, F = Decimal, Fraction
MAP = Path(__file__).resolve().parent.parent.parent / "inhoud" / "vraagstukken"
BREEDTE, REGELS = 56, 4  # het verhaal: zoveel tekens per regel, zoveel regels

VOLTOOID = {"+": "opgeteld", "−": "afgetrokken", "×": "vermenigvuldigd", ":": "gedeeld"}
NAAM_OP = {"+": "plus", "−": "min", "×": "maal", ":": "deel"}
BRIEFJES = [5, 10, 20, 50, 100, 200, 500]


def _laad(naam):
    with open(MAP / naam, encoding="utf-8") as f:
        return json.load(f)


WERELDEN = _laad("werelden.json")
ZINNEN = _laad("zinnen.json")
NAMEN = WERELDEN["namen"]
STAPPENPLAN = ZINNEN["stappenplan"]


class Opnieuw(Exception):
    """De getallen zijn niet mooi (of het verhaal is te lang): kies opnieuw."""


# ---- rekenen -------------------------------------------------------------------------------------------

def bereken(op, w, negatief=False):
    """Exact rekenen (Fraction). None als het niet kan (delen door 0, of negatief tenzij dat mag)."""
    if op == "+":
        r = sum(w, F(0))
    elif op == "−":
        r = w[0] - sum(w[1:], F(0))
    elif op in ("×", "omzet"):
        r = F(1)
        for x in w:
            r *= x
    elif op == ":":
        r = w[0] / w[1] if w[1] else None
    elif op == "pct":
        r = w[0] * w[1] / 100
    elif op == "heel":
        r = F(math.floor(w[0] / w[1])) if w[1] else None
    elif op == "rest":
        r = w[0] - w[1] * math.floor(w[0] / w[1]) if w[1] else None
    elif op == "boven":
        r = F(math.ceil(w[0] / w[1])) if w[1] else None
    else:
        raise ValueError(op)
    return None if r is None or (r < 0 and not negatief) else r


def mooi(x, decimalen=2):
    """Fraction → Decimal als het hoogstens zoveel cijfers na de komma heeft, anders None."""
    x = F(x)
    if (x * 10 ** decimalen).denominator != 1:
        return None
    return D(x.numerator) / D(x.denominator)


def tekst_getal(x, eenheid=""):
    """Een getal zoals in het verhaal: '€ 3,20', '750 g', '1 250', '9.45 u' (klok), '1 u 35 min' (duur)."""
    if eenheid == "€":
        return "€ " + geld(x)
    if eenheid == "klok":
        return klok_tekst(x)
    if eenheid == "duur":
        return duur_tekst(x)
    t = fmt_groot(x) if abs(x) >= 10000 else fmt(x)
    return f"{t} {eenheid}" if eenheid else t


def _breuk_tekst(teller, noemer):
    if (teller, noemer) == (1, 2):
        return "de helft"
    return f"{teller}/{noemer}"


# ---- een vraagstuk opbouwen ------------------------------------------------------------------------------

class Bouw:
    """Hier zet een rekenstructuur de gegevens en stappen in."""

    def __init__(self, rng, p, ctx):
        self.rng, self.p, self.ctx = rng, p, ctx
        self.g = {}        # id → Gegeven
        self.w = {}        # id → Fraction (gegevens en stappen)
        self.stappen = []
        self.extra = []    # structuur-eigen foute paden: (code, waarde, tekst)
        self.ook_juist = set()  # tussenuitkomsten van een andere juiste weg: in het klad nooit een denkfout
        self.controle = None

    # getallen kiezen
    def getal(self, lo, hi, stap=1, hoogstens=None):
        lo, hi = D(str(lo)), D(str(hi))
        if hoogstens is not None:
            hi = min(hi, D(hoogstens))
        stap = D(str(stap))
        a, b = math.ceil(lo / stap), math.floor(hi / stap)
        if b < a:
            raise Opnieuw("bereik")
        return self.rng.randint(a, b) * stap

    def bedrag(self, lo, hi):
        return self.getal(lo, hi, self.p["geld"]).normalize() if D(self.p["geld"]) < 1 else self.getal(lo, hi, 1)

    # gegevens en stappen
    def geg(self, id, waarde, naam, eenheid="", tekst=None, nodig=True):
        waarde = D(waarde)
        g = Gegeven(id, waarde, tekst or tekst_getal(waarde, eenheid), V.vul_tekst(naam, self.ctx), eenheid, nodig)
        self.g[id] = g
        self.w[id] = F(waarde)
        self.ctx[id] = g
        return g

    def stap(self, op, operanden, id, naam, hint, waarom, eenheid=""):
        waarden = [self.w[o] if isinstance(o, str) else F(o) for o in operanden]
        r = bereken(op, waarden)
        if r is None or (op != "omzet" and r == 0):
            raise Opnieuw("stap")
        d = mooi(r, 3 if op == "omzet" else 2)
        if d is None:
            raise Opnieuw("niet mooi")
        self.w[id] = r
        st = Rekenstap(op, list(operanden), id, d, V.vul_tekst(naam, self.ctx), V.vul_tekst(hint, self.ctx, True),
                       "", "", eenheid)
        self.ctx[id] = Gegeven(id, d, tekst_getal(d, eenheid), st.naam, eenheid)
        st.reken = self.reken_tekst(st, waarden, d)
        st.waarom = V.vul_tekst(waarom, self.ctx, True)
        self.stappen.append(st)
        return d

    def reken_tekst(self, st, waarden, d):
        def getal(x, eenheid=""):
            if eenheid in ("klok", "duur"):
                return tekst_getal(x, eenheid)
            return geld(x) if eenheid == "€" else fmt_groot(x) if abs(x) >= 10000 else fmt(x)

        def t(i):
            o = st.operanden[i]
            if isinstance(o, str):
                g = self.ctx[o]
                return getal(g.waarde, g.eenheid)
            return getal(D(o))
        uit = getal(d, st.eenheid)
        if st.op == "omzet":
            g = self.ctx[st.operanden[0]]
            return f"{g.tekst} = {fmt(d)} {st.eenheid}"
        if st.op == "pct":
            return f"{t(0)} % van {t(1)} = {uit}"
        if st.op in ("heel", "boven"):
            q, r = divmod(waarden[0], waarden[1])
            return f"{t(0)} : {t(1)} = {fmt(D(q.numerator) / q.denominator)} rest {fmt(mooi(r, 3))}"
        if st.op == "rest":
            q = math.floor(waarden[0] / waarden[1])
            return f"{t(0)} : {t(1)} = {q} rest {uit}"
        teken = f" {st.op} "
        return teken.join(t(i) for i in range(len(st.operanden))) + f" = {uit}"

    def kan(self, lo, hi, uitleg):
        self.controle = (lo, hi, V.vul_tekst(uitleg, self.ctx, True))

    def t(self, sjabloon):
        return V.vul_tekst(sjabloon, self.ctx, True)


class Structuur:
    """Een rekenstructuur. soort = welk item uit een wereld ze nodig heeft."""
    id = ""
    naam = ""
    soort = ""

    def bouw(self, b, variant, item):
        raise NotImplementedError


def _woorden(item, b):
    for k in ("ding", "houder", "groep", "plek", "rond", "bedek"):
        if k in item:
            b.ctx[k] = V.woord(item[k])
    for k in ("werkt", "op", "liggen", "waar", "gerecht", "knipt", "wat"):
        if k in item:
            b.ctx[k] = item[k]
    if "momenten" in item:
        b.ctx["m1"], b.ctx["m2"] = item["momenten"]
    if "rest" in item:
        b.ctx["m0"], b.ctx["m3"] = item["rest"]  # het geheel en het derde moment


class Samen(Structuur):
    id, naam, soort = "samen", "samen tellen", "tel"

    def bouw(self, b, variant, item):
        lo, hi = item["bereik"]
        hi = min(hi, b.p["max"] // 2)
        a, x = b.getal(lo // 2, hi), b.getal(lo // 2, hi)
        if variant == "samen":
            b.geg("a", a, "het aantal {ding.mv} {m1}")
            b.geg("b", x, "het aantal {ding.mv} {m2}")
            b.stap("+", ["a", "b"], "s", "het aantal {ding.mv} samen",
                   "Je zoekt hoeveel het er samen zijn: tel op.", "{m1} {a} en {m2} {b}: samen is dat {a} + {b}.")
            b.kan(max(a, x), None, "Samen zijn het er meer dan {m1} of {m2} alleen.")
        elif variant == "rest":
            if "rest" not in item:
                raise Opnieuw("geen derde moment")
            hi = min(item["bereik"][1], b.p["max"] // 3)
            a, x, r = (b.getal(max(1, lo // 3), hi) for _ in range(3))
            if a == x:
                raise Opnieuw("twee keer hetzelfde")
            # het grootste eerst: dan is "de twee delen van elkaar afgetrokken" (a − b) een fout pad dat het klad kent
            a, x = max(a, x), min(a, x)
            b.ook_juist |= {F(x + r), F(a + r)}  # eerst één deel aftrekken (t − a of t − b), dan het andere
            b.geg("t", a + x + r, "het aantal {ding.mv} {m0}")
            b.geg("a", a, "het aantal {ding.mv} {m1}")
            b.geg("b", x, "het aantal {ding.mv} {m2}")
            b.stap("+", ["a", "b"], "s", "het aantal {ding.mv} samen",  # kort: past naast de rekenregel
                   "Tel eerst op wat je al kent: {m1} en {m2} samen.", "{m1} {a} en {m2} {b}: samen {a} + {b}.")
            b.stap("−", ["t", "s"], "r", "het aantal {m3}",
                   "Trek dat af van het totaal: wat overblijft, is {m3}.",
                   "{m0} {t}, waarvan {s} {m1} en {m2}: {m3} is dat {t} − {s}.")
            b.kan(0, a + x + r, "Er kunnen {m3} niet meer {ding.mv} zijn dan {m0} in totaal.")
        else:
            b.geg("t", a + x, "het aantal {ding.mv} samen")
            b.geg("a", a, "het aantal {ding.mv} {m1}")
            b.stap("−", ["t", "a"], "r", "het aantal {ding.mv} {m2}",
                   "Je weet hoeveel het er samen zijn en hoeveel {m1}: trek af wat je al kent.",
                   "Samen {t}, waarvan {a} {m1}: {m2} is dat {t} − {a}.")
            b.kan(0, a + x, "{m2} kunnen het er niet meer zijn dan samen.")


class Verschil(Structuur):
    id, naam, soort = "verschil", "verschil en vergelijken", "tel"

    def bouw(self, b, variant, item):
        lo, hi = item["bereik"]
        hi = min(hi, b.p["max"])
        a = b.getal(lo, hi)
        d = b.getal(max(1, lo // 4), max(2, hi // 3))
        if variant == "meer":
            b.geg("a", a, "het aantal {ding.mv} {m1}")
            b.geg("b", a + d, "het aantal {ding.mv} {m2}")
            b.stap("−", ["b", "a"], "v", "hoeveel {ding.mv} meer",
                   "Hoeveel meer? Dat is het verschil: trek het kleinste getal af van het grootste.",
                   "{m2} {b}, {m1} {a}: het verschil is {b} − {a}.")
            b.kan(0, a + d, "Het verschil is kleiner dan het grootste getal.")
        else:
            b.geg("a", a, "het aantal {ding.mv} {m1}")
            b.geg("d", d, "hoeveel {m1} minder is" if variant == "minder" else "hoeveel {m2} meer is")
            hint = ("Let op: {m1} zijn het er *minder* dan {m2}. Dus {m2} zijn het er meer: tel op."
                    if variant == "minder" else "{m2} zijn het er meer dan {m1}: tel erbij.")
            b.stap("+", ["a", "d"], "r", "het aantal {ding.mv} {m2}", hint,
                   "{m1} {a}, {m2} {d} meer: {a} + {d}.")
            b.kan(a, None, "{m2} zijn het er meer dan {m1}.")
            if variant == "minder" and a > d:
                b.extra.append(("vs_signaalwoord", F(a - d),
                                b.t("Let op het woord 'minder': {m1} zijn het er minder dan {m2}. Dus {m2} zijn "
                                    "het er meer: tel op.")))


class Groepen(Structuur):
    id, naam, soort = "groepen", "groepjes: × en :", "groep"

    def bouw(self, b, variant, item):
        a = b.getal(*item["aantal"], hoogstens=b.p["factor"])
        x = b.getal(*item["per"])
        if a * x > b.p["max"]:
            raise Opnieuw("te groot")
        if variant == "totaal":
            b.geg("a", a, "het aantal {houder.mv}")
            b.geg("b", x, "het aantal {ding.mv} {op} één {houder.enk}")
            b.stap("×", ["a", "b"], "t", "het aantal {ding.mv} in totaal",
                   "Er zijn een paar {houder.mv}, met {op} elke {houder.enk} evenveel {ding.mv}: vermenigvuldig.",
                   "{a} {houder.mv} met elk {b} {ding.mv}: {a} keer {b}.")
            b.kan(max(a, x), None, "In totaal zijn het er meer dan {op} één {houder.enk}.")
        elif variant == "per":
            b.geg("t", a * x, "het aantal {ding.mv} in totaal")
            b.geg("a", a, "het aantal {houder.mv}")
            b.stap(":", ["t", "a"], "r", "het aantal {ding.mv} {op} één {houder.enk}",
                   "Je verdeelt eerlijk: deel het totaal door het aantal {houder.mv}.",
                   "{t} {ding.mv} eerlijk verdeeld over {a} {houder.mv}: {t} : {a}.")
            b.kan(0, a * x, "{op} één {houder.enk} kunnen niet meer {ding.mv} komen dan er in totaal zijn.")
        else:
            b.geg("t", a * x, "het aantal {ding.mv} in totaal")
            b.geg("b", x, "het aantal {ding.mv} {op} één {houder.enk}")
            b.stap(":", ["t", "b"], "r", "het aantal {houder.mv}",
                   "Hoeveel keer past wat {op} één {houder.enk} gaat in het totaal? Deel.",
                   "{t} {ding.mv}, {b} per {houder.enk}: {t} : {b}.")
            b.kan(0, a * x, "Er zijn niet meer {houder.mv} dan {ding.mv}.")


class Rest(Structuur):
    id, naam, soort = "rest", "delen met rest", "groep"

    def bouw(self, b, variant, item):
        x = b.getal(*item["per"], hoogstens=max(3, b.p["factor"] * 3))
        q = b.getal(*item["aantal"], hoogstens=b.p["factor"])
        r = b.getal(1, x - 1)
        n = q * x + r
        if n > b.p["max"]:
            raise Opnieuw("te groot")
        b.geg("n", n, "het aantal {ding.mv}")
        b.geg("b", x, "het aantal {ding.mv} {op} één {houder.enk}")
        if variant == "over":
            b.stap("rest", ["n", "b"], "r", "het aantal {ding.mv} dat overblijft",
                   "Deel: wat er overblijft na het delen, is de rest.",
                   "{n} : {b} = {q} rest {r}: er blijven er {r} over.".replace("{q}", str(q)).replace("{r}", str(r)))
            b.kan(0, x - 1, "Wat overblijft, is minder dan wat {op} één {houder.enk} past.")
            return
        b.stap("heel", ["n", "b"], "q", "het aantal volle {houder.mv}",
               "Deel het aantal {ding.mv} door wat {op} één {houder.enk} past.",
               "{n} : {b} = {q} rest " + str(r) + ".")
        if variant == "nodig":
            b.stap("+", ["q", 1], "t", "het aantal {houder.mv} voor alle {ding.mv}",
                   "Er blijven er nog over: daarvoor heb je nog 1 {houder.enk} extra nodig.",
                   "{q} volle {houder.mv}, en voor de " + str(r) + " die overblijven nog 1: {q} + 1.")
            b.kan(1, n, "Je hebt niet meer {houder.mv} nodig dan er {ding.mv} zijn.")
        else:
            b.extra.append(("vs_niet_vol", F(q + 1), b.t("De laatste {houder.enk} is niet vol: tel alleen de "
                                                         "volle.")))
            b.kan(0, n, "Er zijn niet meer {houder.mv} dan {ding.mv}.")


class SamenDelen(Structuur):
    id, naam, soort = "samen_delen", "samen en dan eerlijk verdelen", "groep"

    def bouw(self, b, variant, item):
        n = b.getal(*item["aantal"], hoogstens=b.p["factor"])
        per = b.getal(*item["per"])
        totaal = n * per
        if totaal > b.p["max"] or totaal < 4:
            raise Opnieuw("te groot")
        a = b.getal(max(1, totaal // 4), totaal * 3 // 4)
        b.geg("a", a, "wat {wie} eerst heeft")
        b.geg("b", totaal - a, "wat er bij komt")
        b.geg("n", n, "het aantal {houder.mv}")
        b.stap("+", ["a", "b"], "s", "alle {ding.mv} samen", "Tel eerst alles samen.",
               "{a} en {b} erbij: samen {a} + {b}.")
        b.stap(":", ["s", "n"], "r", "het aantal {ding.mv} {op} één {houder.enk}",
               "Verdeel daarna eerlijk: deel door het aantal {houder.mv}.",
               "{s} {ding.mv} eerlijk over {n} {houder.mv}: {s} : {n}.")
        b.kan(0, totaal, "{op} één {houder.enk} komen niet meer {ding.mv} dan er in totaal zijn.")


def _briefje(b, bedrag):
    """Een briefje (of bedrag) dat groter is dan wat je moet betalen."""
    kandidaten = [x for x in BRIEFJES if x > bedrag]
    if not kandidaten:
        raise Opnieuw("te duur")
    if len(kandidaten) > 1 and kandidaten[1] <= 4 * bedrag and b.rng.random() < 0.3:
        return kandidaten[1]
    return kandidaten[0]


class Wisselgeld(Structuur):
    id, naam, soort = "wisselgeld", "wisselgeld", "koop"

    def bouw(self, b, variant, item):
        p = b.bedrag(*item["prijs"])
        if variant == "een":
            b.geg("p", p, "de prijs van {de:ding}", "€")
            b.geg("b", _briefje(b, p), "het bedrag waarmee {wie} betaalt", "€")
            b.stap("−", ["b", "p"], "w", "het wisselgeld", "Wisselgeld = wat je betaalt − wat het kost.",
                   "{wie} betaalt {b} en het kost {p}: {b} − {p}.", "€")
        else:
            a = b.getal(2, max(2, min(b.p["factor"], 9)))
            b.geg("a", a, "het aantal {ding.mv}")
            b.geg("p", p, "de prijs van één {ding.enk}", "€")
            b.stap("×", ["a", "p"], "k", "de prijs van alle {ding.mv}",
                   "Alle {ding.mv} kosten evenveel: reken eerst uit wat ze samen kosten (×).",
                   "{a} {ding.mv} van {p}: {a} × {p}.", "€")
            b.geg("b", _briefje(b, a * p), "het bedrag waarmee {wie} betaalt", "€")
            b.stap("−", ["b", "k"], "w", "het wisselgeld", "Daarna: wisselgeld = wat je betaalt − wat het kost.",
                   "{wie} betaalt {b} en alles kost {k}: {b} − {k}.", "€")
        b.kan(0, b.w["b"], "Het wisselgeld is minder dan de {b} waarmee {wie} betaalt.")


class TweeSoorten(Structuur):
    id, naam, soort = "twee_soorten", "twee soorten kopen", "koop"

    def bouw(self, b, variant, item):
        item2 = b.ctx.get("_item2")
        if not item2:
            raise Opnieuw("geen tweede item")
        b.ctx["ding2"] = V.woord(item2["ding"])
        a, c = b.getal(2, min(b.p["factor"], 6)), b.getal(2, min(b.p["factor"], 6))
        p, q = b.bedrag(*item["prijs"]), b.bedrag(*item2["prijs"])
        b.geg("a", a, "het aantal {ding.mv}")
        b.geg("p", p, "de prijs van één {ding.enk}", "€")
        b.geg("c", c, "het aantal {ding2.mv}")
        b.geg("q", q, "de prijs van één {ding2.enk}", "€")
        b.stap("×", ["a", "p"], "k1", "de prijs van de {ding.mv}", "Reken eerst uit wat de {ding.mv} samen kosten.",
               "{a} {ding.mv} van {p}: {a} × {p}.", "€")
        b.stap("×", ["c", "q"], "k2", "de prijs van de {ding2.mv}", "Dan wat de {ding2.mv} samen kosten.",
               "{c} {ding2.mv} van {q}: {c} × {q}.", "€")
        b.stap("+", ["k1", "k2"], "t", "wat {wie} in totaal betaalt", "Tel die twee bedragen op.",
               "De {ding.mv} en de {ding2.mv} samen: {k1} + {k2}.", "€")
        if variant == "wissel":
            b.geg("b", _briefje(b, a * p + c * q), "het bedrag waarmee {wie} betaalt", "€")
            b.stap("−", ["b", "t"], "w", "het wisselgeld", "Wisselgeld = wat je betaalt − wat alles kost.",
                   "{wie} betaalt {b} en alles kost {t}: {b} − {t}.", "€")
            b.kan(0, b.w["b"], "Het wisselgeld is minder dan de {b} waarmee {wie} betaalt.")
        else:
            b.kan(max(p, q), None, "Samen kost het meer dan één {ding.enk}.")


class PerKg(Structuur):
    id, naam, soort = "per_kg", "prijs per kg (omzetten)", "kg"

    def bouw(self, b, variant, item):
        gram = b.getal(*item["gram"], stap=b.p["gram"] or 250)  # (0 = niet in dit leerjaar: bv. bij herhalen)
        if gram % 1000 == 0:
            raise Opnieuw("hele kg")
        k = b.bedrag(*item["prijs"])
        b.geg("m", gram, "hoeveel {ding.mv} {wie} koopt", "g")
        b.geg("k", k, "de prijs van 1 kg", "€")
        b.stap("omzet", ["m", F(1, 1000)], "kg", "het gewicht in kg",
               "De prijs is per kg, het gewicht in gram: zet eerst om naar kg.", "1000 g = 1 kg, dus {m} = {kg}.",
               "kg")
        b.stap("×", ["kg", "k"], "t", "de prijs die {wie} betaalt",
               "1 kg kost de prijs per kg; voor een ander gewicht vermenigvuldig je met het aantal kg.",
               "{kg} kg van {k} per kg: {kg} × {k}.", "€")
        if variant == "wissel":
            b.geg("b", _briefje(b, b.w["t"]), "het bedrag waarmee {wie} betaalt", "€")
            b.stap("−", ["b", "t"], "w", "het wisselgeld", "Wisselgeld = wat je betaalt − wat het kost.",
                   "{wie} betaalt {b} en de {ding.mv} kosten {t}: {b} − {t}.", "€")
            b.kan(0, b.w["b"], "Het wisselgeld is minder dan de {b} waarmee {wie} betaalt.")
        elif gram < 1000:
            b.kan(0, k, "Minder dan 1 kg kost minder dan {k}.")
        else:
            b.kan(k, None, "Meer dan 1 kg kost meer dan {k}.")


class Korting(Structuur):
    id, naam, soort = "korting", "korting (procent)", "duur"

    def bouw(self, b, variant, item):
        pct = b.rng.choice(b.p["procenten"] or [10, 50])
        prijs = b.getal(*item["prijs"], stap=5 if pct in (10, 20, 50) else 4)
        if mooi(F(prijs * pct) / 100) is None:
            raise Opnieuw("niet mooi")
        b.geg("P", prijs, "de prijs zonder korting", "€")
        b.geg("k", pct, "het procent korting", "%", tekst=f"{pct} %")
        b.stap("pct", ["k", "P"], "K", "de korting in euro",
               "Reken eerst uit hoeveel euro de korting is: zoveel procent van de prijs.",
               "{k} van {P}: " + ("{P} : 10" if pct == 10 else "{P} : 100 × " + str(pct)) + ".", "€")
        if variant == "gewoon":
            b.stap("−", ["P", "K"], "n", "de prijs met korting", "Trek de korting af van de prijs.",
                   "De prijs min de korting: {P} − {K}.", "€")
            b.kan(0, prijs, "Met korting betaal je minder dan {P}.")
            b.extra.append(("vs_procent_euro", F(prijs - pct),
                            b.t("{k} korting is niet hetzelfde als € " + str(pct) + " korting: reken eerst uit "
                                "hoeveel euro {k} van {P} is.")))
        else:
            b.kan(0, prijs, "De korting is kleiner dan de prijs.")


class Sparen(Structuur):
    id, naam, soort = "sparen", "sparen (hoeveel weken?)", "duur"

    def bouw(self, b, variant, item):
        prijs = b.getal(*item["prijs"], stap=5)
        al = b.getal(prijs // 10, prijs // 2, stap=1)
        s = b.getal(2, 25)
        weken = math.ceil((prijs - al) / s)
        if not 2 <= weken <= 30:
            raise Opnieuw("te lang sparen")
        b.geg("P", prijs, "de prijs van {de:ding}", "€")
        b.geg("h", al, "wat {wie} al gespaard heeft", "€")
        b.geg("s", s, "wat {wie} elke week spaart", "€")
        b.stap("−", ["P", "h"], "nog", "wat {wie} nog moet sparen", "Hoeveel moet er nog bij? Trek af wat er al is.",
               "{de:ding} kost {P} en er is al {h}: {P} − {h}.", "€")
        if (prijs - al) % s == 0:
            b.stap(":", ["nog", "s"], "t", "het aantal weken", "Hoeveel keer moet {wie} sparen? Deel.",
                   "Nog {nog} sparen, {s} per week: {nog} : {s}.")
        else:
            b.stap("heel", ["nog", "s"], "q", "het aantal volle weken", "Hoeveel keer moet {wie} sparen? Deel.",
                   "{nog} : {s} = {q} rest " + str((prijs - al) % s) + ".")
            b.stap("+", ["q", 1], "t", "het aantal weken",
                   "Na die weken is er nog niet genoeg: er moet nog 1 week bij.",
                   "{q} weken is nog net te weinig, dus {q} + 1.")
        b.kan(1, None, "{wie} moet minstens 1 week sparen.")


class Recept(Structuur):
    id, naam, soort = "recept", "recept (verhouding)", "recept"

    def bouw(self, b, variant, item):
        ing = b.rng.choice(item["ingredienten"])
        b.ctx["ing"], b.ctx["eenheid"] = ing["naam"], ing["eenheid"]
        per = b.getal(*ing["per_persoon"], stap=5)
        n1 = b.rng.choice([2, 4, 5, 10] if b.p["factor"] >= 10 else [2, 4])
        n2 = b.rng.choice([x for x in range(2, 13) if x != n1])
        b.geg("n1", n1, "het aantal personen in het recept", tekst=f"{n1}")
        b.geg("x", per * n1, "hoeveel {ing} voor {n1} personen", ing["eenheid"])
        b.geg("n2", n2, "voor hoeveel personen {wie} kookt", tekst=f"{n2}")
        b.stap(":", ["x", "n1"], "e", "hoeveel {ing} voor 1 persoon",
               "Reken eerst uit hoeveel je nodig hebt voor 1 persoon: deel.", "{x} voor {n1} personen: {x} : {n1}.",
               ing["eenheid"])
        b.stap("×", ["e", "n2"], "t", "hoeveel {ing} voor {n2} personen",
               "Daarna voor alle personen: vermenigvuldig.", "{e} per persoon, {n2} personen: {e} × {n2}.",
               ing["eenheid"])
        if n2 > n1:
            b.kan(per * n1, None, "Voor meer personen heb je meer nodig dan {x}.")
        else:
            b.kan(0, per * n1, "Voor minder personen heb je minder nodig dan {x}.")


class BreukVan(Structuur):
    id, naam, soort = "breuk_van", "een breuk van een aantal", "deel"

    def bouw(self, b, variant, item):
        noemer = b.rng.choice(b.p["noemers"] or [2, 4])
        teller = b.rng.randint(1, noemer - 1)
        if math.gcd(teller, noemer) != 1:
            raise Opnieuw("niet vereenvoudigd")
        lo, hi = item["totaal"]
        t = b.getal(max(noemer, lo), hi, stap=noemer)
        b.geg("t", t, "het aantal {groep.mv}")
        b.geg("f", D(teller) / D(noemer), "het deel", tekst=_breuk_tekst(teller, noemer))
        b.stap(":", ["t", noemer], "e", "1/" + str(noemer) + " van de {groep.mv}",
               "Zoek eerst één deel: deel door de noemer.",
               "1/" + str(noemer) + " van {t}: {t} : " + str(noemer) + ".")
        laatste = "e"
        if teller > 1:
            b.stap("×", ["e", teller], "d", "{f} van de {groep.mv}", "Neem dan zoveel delen als de teller zegt.",
                   "{f} is " + str(teller) + " keer 1/" + str(noemer) + ": {e} × " + str(teller) + ".")
            laatste = "d"
        if variant == "niet":
            b.stap("−", ["t", laatste], "n", "de andere {groep.mv}",
                   "Gevraagd is het andere deel: trek af van het totaal.",
                   "Alle {t} min het deel: {t} − {" + laatste + "}.")
        b.kan(0, t, "Een deel is nooit meer dan alle {t}.")


class Omtrek(Structuur):
    id, naam, soort = "omtrek", "omtrek (hek, lint)", "tuin"

    def bouw(self, b, variant, item):
        l = b.getal(*item["lengte"])
        br = b.getal(item["breedte"][0], min(item["breedte"][1], l - 1))
        if l * br == 2 * (l + br):
            raise Opnieuw("omtrek = oppervlakte")
        b.geg("l", l, "de lengte", "m")
        b.geg("b", br, "de breedte", "m")
        b.ctx["doel"] = item["doel"]
        b.stap("+", ["l", "b"], "h", "de lengte en de breedte samen (de helft van de omtrek)",
               "Rondom = alle 4 de zijden. Tel eerst een lengte en een breedte op.",
               "Eén lengte en één breedte: {l} + {b}.", "m")
        b.stap("×", ["h", 2], "o", "de omtrek", "Er zijn 2 lengtes en 2 breedtes: neem dat 2 keer.",
               "Rondom zijn er 2 lengtes en 2 breedtes: {h} × 2.", "m")
        b.extra.append(("vs_oppervlakte", F(l * br), b.t("Dat is de oppervlakte (lengte × breedte). Rondom gaat "
                                                         "over de rand: de omtrek.")))
        if variant == "prijs":
            q = b.bedrag(*item["prijs"])
            b.geg("q", q, "de prijs van 1 meter", "€")
            b.stap("×", ["o", "q"], "k", "de prijs van {de:rond}", "Elke meter kost evenveel: vermenigvuldig.",
                   "{o} {rond.enk}, elke meter kost {q}: {o} × {q}.", "€")
            b.kan(q, None, "Meer dan 1 meter kost meer dan {q}.")
        else:
            b.kan(2 * l, None, "Rondom is langer dan 2 keer de lengte.")


DAGEN = ["op maandag", "op dinsdag", "op woensdag", "op donderdag"]


class Gemiddelde(Structuur):
    id, naam, soort = "gemiddelde", "gemiddelde", "tel"

    def bouw(self, b, variant, item):
        n = 3 if variant == "drie" else 4
        b.ctx.update({f"m{i + 1}": d for i, d in enumerate(DAGEN)})
        lo, hi = item["bereik"]
        hi = min(hi, b.p["max"] // n)
        gem = b.getal(lo + (hi - lo) // 4, hi - (hi - lo) // 4)
        spreiding = max(1, (hi - lo) // 4)
        afwijking = [b.rng.randint(-spreiding, spreiding) for _ in range(n - 1)]
        waarden = [gem + a for a in afwijking] + [gem - sum(afwijking)]
        if min(waarden) < 1 or len(set(waarden)) < n:
            raise Opnieuw("niet mooi")
        ids = "abcd"[:n]
        for i, (gid, w) in enumerate(zip(ids, waarden)):
            b.geg(gid, w, "het aantal {ding.mv} {m" + str(i + 1) + "}")
        b.stap("+", list(ids), "s", "alle {ding.mv} samen", "Tel eerst alles samen.",
               "Alle dagen samen: " + " + ".join("{" + i + "}" for i in ids) + ".")
        b.stap(":", ["s", n], "g", "het gemiddelde per dag",
               "Gemiddeld = samen gedeeld door het aantal dagen.",
               "Samen {s} op " + str(n) + " dagen: {s} : " + str(n) + ".")
        if mooi(F(sum(waarden)) / (n - 1)) is not None:
            b.extra.append(("vs_gemiddelde_aantal", F(sum(waarden)) / (n - 1),
                            "Je deelde door het verkeerde aantal. Tel hoeveel dagen het zijn."))
        b.kan(min(waarden), max(waarden), "Het gemiddelde ligt tussen het kleinste en het grootste getal.")


class Snelheid(Structuur):
    id, naam, soort = "snelheid", "snelheid, afstand en tijd", "rit"

    def bouw(self, b, variant, item):
        b.ctx["werkt"] = item["werkt"]
        v = b.getal(*item["snelheid"])
        b.geg("v", v, "de snelheid", "km/u", tekst=f"{fmt(v)} km per uur")
        if variant == "minuten":
            minuten = b.rng.choice([15, 30, 45, 90, 150])
            b.geg("t", minuten, "hoe lang {wie} onderweg is", "min")
            b.stap("omzet", ["t", F(1, 60)], "u", "de tijd in uren",
                   "De snelheid is per uur: zet de minuten eerst om naar uren (60 min = 1 u).",
                   "60 min = 1 u, dus {t} = {u} u.", "u")
            b.stap("×", ["u", "v"], "s", "de afstand", "Elk uur kom je even ver: vermenigvuldig met het aantal uren.",
                   "{u} uur aan {v}: {u} × {v}.", "km")
            if minuten < 60:
                b.kan(0, v, "In minder dan een uur kom je minder ver dan {v}.")
            else:
                b.kan(v, None, "In meer dan een uur kom je verder dan {v}.")
            return
        uren = b.getal(max(2, item["uren"][0]), max(2, item["uren"][1]))
        if variant == "afstand":
            b.geg("t", uren, "hoe lang {wie} onderweg is", "uur")
            b.stap("×", ["v", "t"], "s", "de afstand", "Elk uur kom je even ver: vermenigvuldig met het aantal uren.",
                   "{t} lang aan {v}: {v} × {t}.", "km")
            b.kan(v, None, "In meer dan 1 uur kom je verder dan in 1 uur.")
        else:
            b.geg("s", v * uren, "de afstand", "km")
            b.stap(":", ["s", "v"], "t", "de tijd in uren",
                   "Hoeveel keer past de afstand van 1 uur in de hele afstand? Deel.",
                   "{s} aan {v}: {s} : {v}.", "uur")
            b.kan(0, v * uren, "Het aantal uren is kleiner dan het aantal kilometer.")


class Tegels(Structuur):
    id, naam, soort = "tegels", "oppervlakte (tegels)", "vloer"

    def bouw(self, b, variant, item):
        l, br = b.getal(*item["lengte"]), b.getal(*item["breedte"])
        if l == br:
            raise Opnieuw("vierkant")
        b.geg("l", l, "de lengte", "m")
        b.geg("b", br, "de breedte", "m")
        b.stap("×", ["l", "b"], "a", "de oppervlakte", "Tegels liggen óp de vloer: reken eerst de oppervlakte uit "
               "(lengte × breedte).", "Een rechthoek van {l} op {b}: {l} × {b}.", "m²")
        if variant == "prijs":
            q = b.bedrag(*item["prijs"])
            b.geg("q", q, "de prijs per m²", "€")
            b.stap("×", ["a", "q"], "k", "de prijs van de {bedek.mv}", "Elke m² kost evenveel: vermenigvuldig.",
                   "{a} m² aan {q} per m²: {a} × {q}.", "€")
            extra = 2 * (l + br) * q
        else:
            n = b.getal(*item["per"])
            b.geg("n", n, "het aantal {bedek.mv} per m²")
            b.stap("×", ["a", "n"], "t", "het aantal {bedek.mv}", "Voor elke m² evenveel: vermenigvuldig.",
                   "{a} m² met elk {n} {bedek.mv}: {a} × {n}.")
            extra = 2 * (l + br) * n
        b.extra.append(("vs_omtrek", F(extra), "Je rekende met de omtrek (rondom). Tegels liggen óp de vloer: "
                                              "oppervlakte = lengte × breedte."))
        b.kan(b.w["l"] * b.w["b"], None, "Je hebt meer nodig dan voor 1 m².")


class Schaal(Structuur):
    id, naam, soort = "schaal", "schaal (kaart en werkelijkheid)", "kaart"

    def bouw(self, b, variant, item):
        b.ctx["wat"] = item["wat"]
        k = b.getal(*item["cm"])
        s = b.rng.choice(item["schalen"])
        b.geg("k", k, "de lengte op de kaart", "cm")
        b.geg("s", s, "de schaal", tekst=f"1 : {fmt_groot(s)}")
        b.stap("×", ["k", "s"], "c", "de echte lengte in cm",
               "1 cm op de kaart is in het echt zoveel cm als de schaal zegt: vermenigvuldig.",
               "{k} op de kaart, schaal {s}: {k} × " + fmt_groot(s) + ".", "cm")
        b.stap("omzet", ["c", F(1, 100000)], "km", "de echte lengte in km",
               "Zet de cm om naar km (100 000 cm = 1 km).", "100 000 cm = 1 km, dus {c} = {km} km.", "km")
        b.kan(F(k) / 10, None, "Met deze schaal is elke cm op de kaart minstens 100 m in het echt.")


class Lint(Structuur):
    id, naam, soort = "lint", "in stukken knippen (m en cm)", "lint"

    def bouw(self, b, variant, item):
        b.ctx["knipt"] = item["knipt"]
        m = b.getal(*item["meter"])
        c = b.rng.choice(item["stuk"])
        if (variant == "stukken") != (m * 100 % c == 0):
            raise Opnieuw("deelbaar")
        b.geg("m", m, "de lengte van {de:ding}", "m")
        b.geg("c", c, "de lengte van één stuk", "cm")
        b.stap("omzet", ["m", 100], "cm", "de lengte in cm", "De stukken zijn in cm: zet eerst om (1 m = 100 cm).",
               "1 m = 100 cm, dus {m} = {cm} cm.", "cm")
        if variant == "stukken":
            b.stap(":", ["cm", "c"], "n", "het aantal stukken", "Hoeveel keer past één stuk erin? Deel.",
                   "{cm} cm in stukken van {c}: {cm} : {c}.")
            b.kan(1, m * 100, "Je kan niet meer stukken knippen dan er cm zijn.")
        else:
            b.stap("rest", ["cm", "c"], "r", "wat er overblijft", "Deel: wat overblijft, is de rest.",
                   "{cm} : {c}: wat overblijft, is de rest.", "cm")
            b.kan(0, c - 1, "Wat overblijft, is korter dan één stuk.")


class PerStuk(Structuur):
    id, naam, soort = "per_stuk", "de prijs van één (regel van drie)", "koop"

    def bouw(self, b, variant, item):
        p = b.bedrag(*item["prijs"])
        a = b.getal(2, min(b.p["factor"], 12))
        if p == 1:
            raise Opnieuw("dan is het totaal gelijk aan het aantal")
        b.geg("a", a, "het aantal {ding.mv} in de reclame")
        b.geg("t", a * p, "wat ze samen kosten", "€")
        b.stap(":", ["t", "a"], "p", "de prijs van één {ding.enk}", "Reken eerst uit wat één {ding.enk} kost: deel.",
               "{a} {ding.mv} kosten {t}: één kost {t} : {a}.", "€")
        if variant == "drie":
            c = b.getal(2, min(b.p["factor"], 15))
            if c == a:
                raise Opnieuw("hetzelfde")
            b.geg("c", c, "hoeveel {ding.mv} {wie} wil")
            b.stap("×", ["p", "c"], "k", "wat {wie} betaalt", "Daarna voor zoveel als {wie} wil: vermenigvuldig.",
                   "Eén kost {p}, {wie} wil er {c}: {p} × {c}.", "€")
            if c > a:
                b.kan(a * p, None, "Meer {ding.mv} kosten meer dan {t}.")
            else:
                b.kan(0, a * p, "Minder {ding.mv} kosten minder dan {t}.")
        else:
            b.kan(0, a * p, "Eén {ding.enk} kost minder dan alle {a} samen.")


class Tijdsduur(Structuur):
    """Tijdstippen en tijdsduur (alles in minuten na middernacht)."""
    id, naam, soort = "tijdsduur", "tijdsduur en aankomstuur", "agenda"

    def bouw(self, b, variant, item):
        for k in ("wat", "start", "einde", "start_v", "einde_v"):
            b.ctx[k] = item[k]
        stap = 1 if b.p["factor"] >= 25 else 5
        begin = b.getal(item["van"][0] * 60, item["van"][1] * 60, stap)
        duur = b.getal(*item["duur"], stap=stap)
        if duur < 20 or begin + duur >= 24 * 60 or (variant == "twee" and "stuk2" not in item):
            raise Opnieuw("tijd")
        if variant == "duur":
            b.geg("b", begin, "het begin-uur", "klok")
            b.geg("e", begin + duur, "het eind-uur", "klok")
            b.stap("−", ["e", "b"], "d", "hoe lang het duurt",
                   "Hoe lang? Van het begin tot het einde: tel in stapjes tot het volle uur, en dan verder.",
                   "Van {b} tot {e}: tel tot het volle uur en dan verder.", "duur")
            b.kan(0, 12 * 60, "Het duurt minder dan een halve dag.")
        elif variant == "begin":
            b.geg("e", begin + duur, "het eind-uur", "klok")
            b.geg("d", duur, "hoe lang het duurt", "duur")
            b.stap("−", ["e", "d"], "b", "het begin-uur", "Tel terug van het einde: eerst tot het volle uur.",
                   "Het eindigt om {e} en duurt {d}: tel {d} terug.", "klok")
            if (begin + duur) % 60 < duur % 60:
                b.extra.append(("vs_uur_vergeten", F(begin + 60), "Over het volle uur terug: er gaat een uur af."))
            b.kan(0, begin + duur, "Het begint vóór het eindigt.")
        else:
            b.geg("b", begin, "het begin-uur", "klok")
            b.geg("d", duur, "hoe lang het duurt", "duur")
            b.stap("+", ["b", "d"], "e", "het eind-uur", "Tel de tijd erbij: eerst de uren, dan de minuten. "
                   "Na 59 minuten komt er een uur bij.", "Vanaf {b}: {d} erbij.", "klok")
            einde = begin + duur
            if begin % 60 + duur % 60 >= 60:
                b.extra.append(("vs_uur_vergeten", F(einde - 60), "60 minuten zijn een uur: er komt een uur bij."))
            if variant == "twee":
                d2 = b.getal(*item["d2"], stap=stap)
                if einde + d2 >= 24 * 60:
                    raise Opnieuw("te laat")
                b.geg("d2", d2, "hoe lang het tweede stuk duurt", "duur")
                b.stap("+", ["e", "d2"], "a", "het uur van aankomst", "Daarna nog het tweede stuk erbij.",
                       "Vanaf {e}: nog {d2} erbij.", "klok")
                einde += d2
            b.kan(begin, 24 * 60, "Je komt later aan dan je vertrekt.")


STRUCTUREN = {s.id: s for s in [Samen(), Verschil(), Groepen(), Rest(), SamenDelen(), Wisselgeld(), TweeSoorten(),
                                PerKg(), Korting(), Sparen(), Recept(), BreukVan(), Omtrek(), Gemiddelde(),
                                Snelheid(), Tegels(), Schaal(), Lint(), PerStuk(), Tijdsduur()]}

# ---- foute paden ------------------------------------------------------------------------------------------

DENKFOUTEN = {
    "vs_omzetten": "niet (goed) omgezet naar de juiste eenheid",
    "vs_overbodig": "een overbodig gegeven gebruikt",
    "vs_stap_vergeten": "een stap vergeten",
    "vs_tussenstap": "gestopt na een tussenstap",
    "vs_komma": "10, 100 of 1000 keer te groot of te klein (komma of eenheid)",
    "vs_niet_vol": "de laatste (niet volle) meegeteld",
    "vs_rest": "het aantal keer gegeven in plaats van de rest",
    "vs_procent": "het procent als gewoon getal gebruikt",
    "vs_procent_euro": "het procent gelezen als euro",
    "vs_oppervlakte": "de oppervlakte berekend in plaats van de omtrek",
    "vs_signaalwoord": "'minder' gelezen als aftrekken (het verhaal zegt iets anders)",
    "vs_rekenfout": "een rekenfout in het klad",
    "vs_kan_niet": "een antwoord dat niet kan kloppen",
    "vs_gemiddelde_aantal": "gedeeld door het verkeerde aantal",
    "vs_omtrek": "de omtrek berekend in plaats van de oppervlakte",
    "vs_uur_vergeten": "60 minuten niet omgezet in een uur",
    **{f"vs_{NAAM_OP[a]}_ipv_{NAAM_OP[b]}": f"{VOLTOOID[a]} in plaats van {VOLTOOID[b]}"
       for a in VOLTOOID for b in VOLTOOID if a != b},
}


def _reken_alles(stappen, waarden, i_wijzig=None, op_nieuw=None, ops_nieuw=None, resultaat=None):
    """Alle stappen opnieuw met één wijziging. Geeft {id: waarde} of None als het niet kan.
    Onder '_sig' staat per stap (bewerking, operanden, uitkomst): zo herkent het klad een fout pad."""
    w = dict(waarden)
    w["_sig"], w["_regels"] = [], []  # _regels: (stap, bewerking, operanden in volgorde, uitkomst) voor de Speurneus
    for i, st in enumerate(stappen):
        ops = [w[o] if isinstance(o, str) else F(o) for o in st.operanden]
        op = st.op
        if i == i_wijzig:
            if resultaat is not None:
                w[st.id] = resultaat
                continue
            op = op_nieuw or op
            ops = ops_nieuw or ops
        r = bereken(op, ops, negatief=True)
        if r is None:
            return None
        w[st.id] = r
        w["_sig"].append((op, sorted(ops), r))
        w["_regels"].append((st, op, ops, r))
    return w


def foute_paden(b, gevraagd):
    """[(code, tekst, eindwaarde, {stap-id: waarde}, [(op, operanden, uitkomst) van de stappen die anders zijn])]."""
    st_ = b.stappen
    eind = st_[-1].id
    juist = b.w[eind]
    basis = {k: v for k, v in b.w.items() if k in b.g}
    paden = []

    juiste_sig = _reken_alles(st_, basis)["_sig"]

    def voeg(code, tekst, w):
        if w is None or w[eind] == juist:
            return
        sig = [x for x in w.get("_sig", []) if x not in juiste_sig and x[2] not in b.ook_juist]
        paden.append((code, tekst, w[eind], w, sig))

    for code, waarde, tekst in b.extra:
        voeg(code, tekst, {eind: waarde})
    for i, st in enumerate(st_):
        ops = [b.w[o] if isinstance(o, str) else F(o) for o in st.operanden]
        if st.op in VOLTOOID and len(ops) == 2 and 1 not in st.operanden:  # (+ 1 extra doos: geen andere bewerking)
            for alt in VOLTOOID:
                if alt == st.op or (st.eenheid in ("klok", "duur") and alt in ("×", ":")):
                    continue
                w = _reken_alles(st_, basis, i, alt)
                if w is None or (alt == ":" and mooi(w[st.id], 2) is None):
                    continue
                tekst = f"Het lijkt erop dat je {VOLTOOID[alt]} hebt in plaats van {VOLTOOID[st.op]}. {st.hint}"
                voeg(f"vs_{NAAM_OP[alt]}_ipv_{NAAM_OP[st.op]}", tekst, w)
        if st.op == "omzet":
            g = b.ctx[st.operanden[0]]  # een gegeven of de uitkomst van een vorige stap
            tekst = f"Je vergat {g.tekst} eerst om te zetten naar {st.eenheid}. {st.hint}"
            voeg("vs_omzetten", tekst, _reken_alles(st_, basis, i, resultaat=ops[0]))
            voeg("vs_omzetten", tekst, _reken_alles(st_, basis, i, resultaat=ops[0] / ops[1]))
        if st.op == "pct":
            voeg("vs_procent", f"{b.g['k'].tekst} van iets is niet {b.g['k'].tekst} keer zoveel. {st.hint}",
                 _reken_alles(st_, basis, i, "×"))
        if st.op == "rest":
            voeg("vs_rest", "Dat is hoeveel keer het past. Gevraagd is wat er overblijft: de rest.",
                 _reken_alles(st_, basis, i, "heel"))
        # een overbodig gegeven gebruikt in plaats van een nodig gegeven
        for o in (g for g in b.g.values() if not g.nodig):
            for j, oid in enumerate(st.operanden):
                if isinstance(oid, str) and oid in b.g and b.g[oid].eenheid == o.eenheid:
                    nieuw = list(ops)
                    nieuw[j] = F(o.waarde)
                    tekst = f"{o.tekst} ({o.naam}) heb je niet nodig om dit op te lossen."
                    voeg("vs_overbodig", tekst, _reken_alles(st_, basis, i, ops_nieuw=nieuw))
        if i < len(st_) - 1:
            # een stap vergeten: verder gerekend met een gegeven in plaats van de uitkomst van deze stap
            for o in st.operanden:
                if isinstance(o, str) and o in b.g:
                    voeg("vs_stap_vergeten", f"Je vergat een stap: eerst moet je {st.naam} berekenen.",
                         _reken_alles(st_, basis, i, resultaat=b.w[o]))
    for st in st_[:-1]:
        voeg("vs_tussenstap", f"Dat is {st.naam}. Gevraagd is {gevraagd}: je bent nog niet klaar.",
             {**b.w, eind: b.w[st.id]})
    for factor in (() if st_[-1].eenheid in ("klok", "duur") else (10, 100, 1000)):
        for w in (juist * factor, juist / factor):
            voeg("vs_komma", "Je antwoord is 10, 100 of 1000 keer te groot of te klein. Kijk naar de komma "
                             "(en de eenheid).", {eind: w})
    return paden  # bij hetzelfde eindantwoord wint het eerste pad (de diagnose zoekt van voor naar achter)


# ---- het verhaal samenstellen ------------------------------------------------------------------------------

def _items(soort):
    return [(w, i) for w in WERELDEN["werelden"] for i in w.get(soort, [])]


def _naam(rng, behalve=()):
    return rng.choice([n for n in NAMEN if n not in behalve])


def _wie(rng, item):
    keuze = rng.choice(item.get("wie", ["@naam"]))
    return _naam(rng) if keuze == "@naam" else keuze


def stel_samen(structuur, variant, wereld, item, p, rng, zin_keuze=None):
    """Bouwt één vraagstuk. Geeft (Verhaal, gewone tekst, sleuteldeel) of gooit Opnieuw."""
    s = STRUCTUREN[structuur]
    ctx = {}
    b = Bouw(rng, p, ctx)
    _woorden(item, b)
    ctx["wie"] = _wie(rng, item)
    ctx["wie2"] = _naam(rng, (ctx["wie"],))
    if structuur == "twee_soorten":
        andere = [i for i in wereld.get("koop", []) if i is not item]
        zelfde = [i for i in andere if i.get("waar") == item.get("waar")]
        ctx["_item2"] = rng.choice(zelfde or andere) if andere else None
    s.bouw(b, variant, item)
    tpl = ZINNEN["structuren"][structuur][variant]
    eigen = {k: v for k, v in item.items() if isinstance(v, str)}

    def sjabloon(t):
        return eigen[t[1:]] if t.startswith("@") and t[1:] in eigen else t.replace("@doel", item.get("doel", ""))

    groepen = [sjabloon(rng.choice(alts)) for alts in tpl["zinnen"]]
    if tpl.get("schud"):
        rng.shuffle(groepen)
    # af en toe een overbodig gegeven
    weetjes = [w for w in wereld.get("weetjes", []) if structuur != "tijdsduur"
               or ("uur" not in w["zin"] and w.get("eenheid") != "min")]  # geen tweede uur in een verhaal over tijd
    if rng.random() < p["overbodig"] and weetjes:
        weetje = rng.choice(weetjes)
        eenheid = weetje.get("eenheid", "")
        nodig_waarden = {g.waarde for g in b.g.values()} | {st.uitkomst for st in b.stappen}
        x = b.getal(*weetje["x"], stap=1)
        if x not in nodig_waarden:
            b.geg("x_", x, weetje["naam"], eenheid, nodig=False)
            # vooraan of vlak voor de vraag (niet ertussen: een zin met 'er' verwijst naar de zin ervoor)
            groepen.insert(rng.choice([0, len(groepen)]), weetje["zin"].replace("{x}", "{x_}"))
    vraag = sjabloon(rng.choice(tpl["vraag"]))
    if wereld.get("intro") and rng.random() < p.get("intro", 0.3):
        groepen.insert(0, rng.choice(wereld["intro"]))
    zinnen = [V.vul(z, ctx) for z in groepen] + [V.vul(vraag, ctx)]
    while len(V.regels(zinnen, BREEDTE)) > REGELS and len(zinnen) > 2 and not any(
            st.gegeven for st in zinnen[0]):
        zinnen = zinnen[1:]  # de inleiding weg als het te lang wordt
    if len(V.regels(zinnen, BREEDTE)) > REGELS:
        raise Opnieuw("te lang")
    in_verhaal = {st.gegeven for z in zinnen for st in z if st.gegeven}
    if set(b.g) - in_verhaal:
        raise Opnieuw(f"gegeven ontbreekt: {set(b.g) - in_verhaal}")
    gevraagd = V.vul_tekst(sjabloon(tpl["gevraagd"]), ctx)
    andere = []
    for k, t in ZINNEN["structuren"][structuur].items():
        try:
            if k != variant:
                andere.append(V.vul_tekst(sjabloon(t["gevraagd"]), ctx))
        except V.SjabloonFout:  # een variant die dit item niet kent (bv. 'rest' zonder derde moment)
            pass
    andere +=[st.naam for st in b.stappen[:-1]] + [g.naam for g in b.g.values() if g.nodig]
    opties = [gevraagd]
    for o in andere:
        if o not in opties and len(opties) < 3:
            opties.append(o)
    rng.shuffle(opties)
    zin = V.tekst(V.vul(sjabloon(tpl["antwoord"]), ctx))
    voor, _, na = zin.partition(V.VAK)
    laatste = b.stappen[-1]
    eenheid = laatste.eenheid
    paden = foute_paden(b, gevraagd)
    model = Verhaal(zinnen, b.g, b.stappen, gevraagd, opties, (voor, na), eenheid, b.controle, paden,
                    eenheid if eenheid in ("klok", "duur") else "getal")
    waarden = "/".join(geld(g.waarde) if g.eenheid == "€" else fmt(g.waarde) for g in b.g.values())
    return model, " ".join(V.tekst(z) for z in zinnen), f"{wereld['id']}:{waarden}"


# ---- het klad nakijken --------------------------------------------------------------------------------------

def analyseer_klad(model, regels):
    """Kijkt het klad na tegenover de stappen en de foute paden (kern/klad.analyseer)."""
    overbodig = {F(g.waarde) for g in model.gegevens.values() if not g.nodig}
    return analyseer(model.stappen, model.paden, regels, overbodig, rekenfout="vs_rekenfout")


# ---- het onderwerp -----------------------------------------------------------------------------------------

def lees_antwoord(tekst):
    """Een antwoord: '7,60', '€ 7,60', '7,60 euro', '135 broodjes' → Decimal of None."""
    t = (tekst or "").replace("€", " ").strip()
    woorden = t.split()
    while woorden and lees_getal(" ".join(woorden)) is None:
        woorden = woorden[:-1]
    return lees_getal(" ".join(woorden)) if woorden else None


def antwoordzin(model, waarde):
    voor, na = model.antwoordzin
    soort = getattr(model, "soort", "getal")
    if soort == "klok":
        return f"{voor}{klok_tekst(waarde)[:-2]}{na}"  # 'om 11.20 u': de u staat al in de zin
    if soort == "duur":
        return f"{voor}{duur_tekst(waarde)}{na}"
    return f"{voor}{geld(waarde) if voor.rstrip().endswith('€') else fmt(waarde)}{na}"


SPIEKBRIEF = [
    ("EEN VRAAGSTUK IN 4 STAPPEN", "accent"),
    *[(f"  {s['nr']} {s['naam']:<9}{s['uitleg']}", "") for s in STAPPENPLAN],
    ("  (op school: Gegeven · Gevraagd · Oplossing · Antwoord)", "dim"),
    ("", ""),
    ("SLEUTELWOORDEN (lees de hele zin!)", "accent"),
    ("  samen, in totaal, erbij           → meestal +", ""),
    ("  meer dan, minder dan, verschil    → meestal − (lees goed!)", ""),
    ("  elk, per, keer                    → ×", ""),
    ("  eerlijk verdelen, hoeveel keer    → :", ""),
    ("  terug, wisselgeld                 → betaald − prijs", ""),
    ("  over, blijft over                 → de rest bij het delen", ""),
    ("", ""),
    ("IN HET KLAD", "accent"),
    ("  Typ x voor maal, : of / voor delen, - voor min.", ""),
    ("  Elke stap op een nieuwe regel.", ""),
    ("  750 g = 0,75 kg         0,75 x 3,20 = 2,40         10 - 2,40 = 7,60", ""),
    ("  25 : 4 = 6 rest 1       25 % van 80 = 20           3/4 van 24 = 18", ""),
    ("", ""),
    ("KAN DAT KLOPPEN?", "accent"),
    ("  Wisselgeld is minder dan wat je betaalt.", ""),
    ("  Een deel is minder dan het geheel.", ""),
    ("  Schat eerst: 0,75 kg van € 3,20 is iets minder dan € 3,20.", ""),
    ("  Zet de eenheid erbij: € 7,60 — niet 760 en niet 7600.", ""),
]


class Vraagstukken(Onderwerp):
    id = "wiskunde.vraagstukken.oplossen"
    naam = "Vraagstukken oplossen"
    spiek_kop = "EEN VRAAGSTUK IN 4 STAPPEN"
    omschrijving = "verhaaltjes lezen, plannen, rekenen in je klad en controleren"
    denkfouten = DENKFOUTEN
    vast = ("structuur", "variant")

    def keuzes(self, p):
        return [k.split("/") for k in p["structuren"]]

    def kies_onderwerp(self, gewichten, p, rng):
        structuren = sorted({s for s, _ in self.keuzes(p)})
        w = [gewichten.get(s, 1.0) for s in structuren]
        return {"structuur": rng.choices(structuren, weights=w, k=1)[0]}

    def maak_met(self, p, rng, data=None):
        keuzes = self.keuzes(p)
        data = data or {}
        for poging in range(300):
            structuur = data.get("structuur") or rng.choice(sorted({s for s, _ in keuzes}))
            varianten = [v for s, v in keuzes if s == structuur] or [data.get("variant")]
            variant = data.get("variant") if data.get("variant") in varianten else rng.choice(varianten)
            if structuur not in STRUCTUREN or not variant:
                data = {}
                continue
            items = _items(STRUCTUREN[structuur].soort)
            wereld, item = rng.choice(items)
            try:
                model, tekst, sleutel = stel_samen(structuur, variant, wereld, item, p, rng)
            except Opnieuw:
                continue
            laatste = model.stappen[-1]
            verwacht = tekst_getal(laatste.uitkomst, laatste.eenheid if laatste.eenheid in ("€", "m", "g", "ml", "kg",
                                                                                                "klok", "duur") else "")
            return Vraag(self.id, f"{self.id}:{structuur}/{variant}:{sleutel}", tekst, laatste.uitkomst,
                         "", {"structuur": structuur, "variant": variant, "onderwerp": structuur}, invoer="vraagstuk",
                         model=model, verwacht_tekst=verwacht)
        raise RuntimeError("geen vraagstuk gevonden")  # komt niet voor (de tests maken er duizenden)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1].split("/")[0] if len(delen) >= 3 and delen[0] == self.id else None

    def lees(self, tekst):
        return lees_antwoord(tekst)

    def lees_vraag(self, v, tekst):
        soort = getattr(v.model, "soort", "getal")
        if soort == "klok":
            return lees_klok(tekst)
        if soort == "duur":
            return lees_duur(tekst) or lees_antwoord(tekst)  # 1 u 35 min, of 95 (minuten)
        return lees_antwoord(tekst)

    def diagnose(self, v, getal):
        m = v.model
        if getal is None or m is None:
            return None
        getal = F(getal)
        pad = next((p for p in m.paden if p[2] == getal), None)
        if pad:
            return pad[0], pad[1]
        if m.controle:
            lo, hi, uitleg = m.controle
            if (lo is not None and getal < lo) or (hi is not None and getal > hi):
                return "vs_kan_niet", f"Kan dat? {uitleg}"
        return None

    def uitleg(self, v):
        m = v.model
        regels = [f"Gevraagd: {m.gevraagd}."]
        for i, st in enumerate(m.stappen, 1):
            regels.append(f"Stap {i}: {st.reken}   ({st.waarom})")
        regels.append(f"Antwoord: {antwoordzin(m, v.antwoord)}")
        return regels

    def tip(self, v):
        return v.model.stappen[0].hint

    def spiekbrief(self):
        return SPIEKBRIEF


VRAAGSTUKKEN = Vraagstukken()


# ---- Speurneus: zoek de fout in het klad van een ander kind ------------------------------------------------

REKENFOUT = "een rekenfout: de uitkomst van die regel klopt niet"
SPEUR_CODES = {"vs_tussenstap", "vs_stap_vergeten", "vs_omzetten", "vs_overbodig", "vs_procent", "vs_rest",
               *(c for c in DENKFOUTEN if "_ipv_" in c)}
REDENEN = [REKENFOUT, DENKFOUTEN["vs_tussenstap"], DENKFOUTEN["vs_overbodig"], DENKFOUTEN["vs_omzetten"],
           DENKFOUTEN["vs_stap_vergeten"], DENKFOUTEN["vs_plus_ipv_maal"], DENKFOUTEN["vs_min_ipv_deel"],
           DENKFOUTEN["vs_maal_ipv_deel"], DENKFOUTEN["vs_plus_ipv_min"]]


def _eenheden(model):
    return {**{g.id: g.eenheid for g in model.gegevens.values()}, **{st.id: st.eenheid for st in model.stappen}}


def _getal(x, eenheid):
    if eenheid in ("klok", "duur"):
        return tekst_getal(int(x) % 1440 if eenheid == "klok" else int(x), eenheid)
    x = F(x)
    d = mooi(x, 3) if mooi(x, 3) is not None else D(round(float(x), 2)).normalize()
    return geld(d) if eenheid == "€" else fmt_groot(d) if abs(d) >= 10000 else fmt(d)


def regel_tekst(model, st, op, ops, r):
    """Eén stap zoals een kind ze in zijn klad schrijft."""
    e = _eenheden(model)
    t = [_getal(x, e.get(o, "") if isinstance(o, str) else "") for o, x in zip(st.operanden, ops)]
    uit = _getal(r, st.eenheid)
    if op == "omzet":
        bron = st.operanden[0]
        return f"{_getal(ops[0], '')} {e.get(bron, '')} = {uit} {st.eenheid}".replace("  ", " ")
    if op == "pct":
        return f"{t[0]} % van {t[1]} = {uit}"
    if op in ("heel", "boven", "rest"):
        q = math.floor(ops[0] / ops[1]) if ops[1] else 0
        rest = ops[0] - ops[1] * q
        return f"{t[0]} : {t[1]} = {q} rest {_getal(rest, st.eenheid if op == 'rest' else '')}"
    return f" {op} ".join(t) + f" = {uit}"


class Speurneus(Onderwerp):
    id = "wiskunde.vraagstukken.speurneus"
    naam = "Speurneus: zoek de fout"
    spiek_kop = "IN HET KLAD"
    omschrijving = "een ander kind loste het op: zit er een fout in, en waarom?"
    denkfouten = {"vs_speur_regel": "de foute regel niet gevonden", "vs_speur_reden": "de fout gevonden, maar niet waarom",
                  "vs_speur_niets": "een fout gezien waar er geen was", "vs_speur_gemist": "de fout niet gezien"}
    vast = ("structuur", "variant")

    def kies_onderwerp(self, gewichten, p, rng):
        return VRAAGSTUKKEN.kies_onderwerp(gewichten, p, rng)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1].split("/")[0] if len(delen) >= 3 and delen[0] == self.id else None

    def maak_met(self, p, rng, data=None):
        for poging in range(200):
            v = VRAAGSTUKKEN.maak_met(p, rng, data)
            m = v.model
            if len(m.stappen) > 4:
                data = None
                continue
            soort = rng.choices(p["fouten"], weights=[{"alles_juist": 1, "rekenfout": 1.3, "denkfout": 1.7}.get(f, 1)
                                                      for f in p["fouten"]])[0]
            uit = getattr(self, "_" + soort)(m, rng, v)
            if uit is None:
                continue
            regels, fout, reden, uitleg, sleutel = uit
            if fout:
                andere = [r for r in REDENEN if r != reden]
                rng.shuffle(andere)
                redenen = [reden] + andere[:2]
                rng.shuffle(redenen)
                juist = redenen.index(reden)
                antwoord = f"{fout}{'abc'[juist]}"
                verwacht = f"regel {fout}, reden {'abc'[juist]}"
            else:  # ook dan 3 redenen: zo verraadt het scherm niet dat er geen fout is
                redenen, juist, antwoord, verwacht = rng.sample(REDENEN, 3), -1, "0", "alles is juist"
            wie = _naam(rng, tuple(n for n in NAMEN if n in v.tekst))  # iemand anders dan in het verhaal
            model = Speur(m, wie, regels, fout, redenen, juist, uitleg)
            return Vraag(self.id, f"{self.id}:{v.sleutel.split(':', 1)[1]}:{soort}{sleutel}", v.tekst, antwoord, "",
                         {**v.data, "soort": soort}, invoer="speur", model=model, verwacht_tekst=verwacht)
        raise RuntimeError("geen speurneus-vraag gevonden")

    @staticmethod
    def _juiste_regels(m):
        return [st.reken for st in m.stappen]

    def _alles_juist(self, m, rng, v):
        return self._juiste_regels(m) + [antwoordzin(m, v.antwoord)], 0, None, "Alles klopt: elke regel en het " \
            "antwoord.", ""

    def _rekenfout(self, m, rng, v):
        kandidaten = [i for i, st in enumerate(m.stappen) if st.op in ("+", "−", "×", ":")]
        if not kandidaten:
            return None
        i = rng.choice(kandidaten)
        st = m.stappen[i]
        juist = F(st.uitkomst)
        mogelijk = (juist + 60, juist - 60, juist + 10, juist - 10) if st.eenheid in ("klok", "duur") else \
            (juist * 10, juist / 10, juist + 10, juist - 1, juist + 1)
        keuzes = [x for x in mogelijk if x > 0 and x != juist and mooi(x, 2) is not None]
        fout = rng.choice(keuzes)
        basis = {k: F(g.waarde) for k, g in m.gegevens.items()}
        w = _reken_alles(m.stappen, basis, i, resultaat=fout)
        if w is None:
            return None
        ops = [basis[o] if isinstance(o, str) and o in basis else w.get(o) if isinstance(o, str) else F(o)
               for o in st.operanden]
        regels = [x.reken for x in m.stappen[:i]] + [regel_tekst(m, st, st.op, ops, fout)]
        regels += [regel_tekst(m, *r) for r in w["_regels"] if m.stappen.index(r[0]) > i]
        eind = w[m.stappen[-1].id]
        if eind < 0 or len(regels) != len(m.stappen):
            return None
        regels.append(antwoordzin(m, mooi(eind, 2) or D(round(float(eind), 2))))
        uitleg = f"Regel {i + 1}: {st.reken.split(' = ')[0]} is {_getal(juist, st.eenheid)}, niet {_getal(fout, st.eenheid)}."
        return regels, i + 1, REKENFOUT, uitleg, f"/r{i}"

    def _denkfout(self, m, rng, v):
        paden = [p for p in m.paden if p[0] in SPEUR_CODES and p[2] > 0 and mooi(p[2], 2) is not None]
        rng.shuffle(paden)
        juiste = self._juiste_regels(m)
        for code, tekst, eind, w, _ in paden:
            if code == "vs_tussenstap":
                k = next((j for j, st in enumerate(m.stappen) if F(st.uitkomst) == eind), None)
                if k is None:
                    continue
                regels = juiste[:k + 1] + [antwoordzin(m, mooi(eind, 2))]
                return regels, len(regels), DENKFOUTEN[code], tekst, f"/{code}"
            if "_regels" not in w:
                continue
            regels = [regel_tekst(m, *r) for r in w["_regels"]]
            fout = next((j for j, r in enumerate(regels) if j >= len(juiste) or r != juiste[j]), None)
            if fout is None:
                continue
            regels.append(antwoordzin(m, mooi(eind, 2)))
            return regels, fout + 1, DENKFOUTEN[code], f"Regel {fout + 1}: {tekst}", f"/{code}"
        return None

    def lees(self, tekst):
        """'2b', 'regel 2, reden b', '0' of 'alles is juist' → '2b' of '0'."""
        t = (tekst or "").strip().lower()
        if t in ("0", "alles is juist", "alles juist"):
            return "0"
        m = re.fullmatch(r"(?:regel\s*)?(\d+)\s*,?\s*(?:reden\s*)?([abc])", t)
        return f"{m.group(1)}{m.group(2)}" if m else None

    def lees_vraag(self, v, tekst):
        return self.lees(tekst)

    def diagnose(self, v, getal):
        m = v.model
        if not isinstance(getal, str) or getal == v.antwoord:
            return None
        if m.fout == 0:
            return "vs_speur_niets", "Er zat geen fout in: elke regel en het antwoord klopten."
        if getal == "0":
            return "vs_speur_gemist", f"Er zat wel een fout in: in regel {m.fout}."
        if not getal.startswith(str(m.fout)):
            return "vs_speur_regel", f"De fout zit in regel {m.fout}."
        return "vs_speur_reden", f"Goed gevonden: regel {m.fout}! Maar de reden is: {m.redenen[m.reden]}."

    def uitleg(self, v):
        m = v.model
        return [m.uitleg] + VRAAGSTUKKEN.uitleg(Vraag(v.vaardigheid, v.sleutel, v.tekst, D(0), model=m.verhaal))[1:-1]

    def tip(self, v):
        return "Reken elke regel na. Past de bewerking bij het verhaal? Klopt het antwoord?"

    def spiekbrief(self):
        return SPIEKBRIEF


SPEURNEUS = Speurneus()


# ---- Schatten en controleren -------------------------------------------------------------------------------

def schat(x):
    """Afronden op 1 beduidend cijfer: 336 → 300, 7,40 → 7, 0,73 → 0,7."""
    x = F(x)
    if x <= 0:
        return D(0)
    macht = math.floor(math.log10(float(x)))
    stap = F(10) ** macht
    return mooi(round(x / stap) * stap, 6).normalize()


class Schatten(Onderwerp):
    id = "wiskunde.vraagstukken.schatten"
    naam = "Schatten en controleren"
    spiek_kop = "KAN DAT KLOPPEN?"
    omschrijving = "ongeveer hoeveel? en: kan dat antwoord kloppen?"
    denkfouten = {"vs_schat_10": "10 keer te groot of te klein geschat",
                  "vs_kan_ja": "een antwoord dat niet kan kloppen, niet opgemerkt",
                  "vs_kan_nee": "een antwoord dat kan kloppen, afgewezen"}
    vast = ("structuur", "variant", "soort")

    def kies_onderwerp(self, gewichten, p, rng):
        return VRAAGSTUKKEN.kies_onderwerp(gewichten, p, rng)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1].split("/")[0] if len(delen) >= 3 and delen[0] == self.id else None

    def maak_met(self, p, rng, data=None):
        for poging in range(200):
            v = VRAAGSTUKKEN.maak_met(p, rng, data)
            soort = (data or {}).get("soort") if (data or {}).get("soort") in p["soorten"] else rng.choice(p["soorten"])
            uit = (self._ongeveer if soort == "ongeveer" else self._kan)(v, rng)
            if uit is None:
                data = None  # (bv. een tijdstip uit de herhaalbak: kies een ander soort vraagstuk)
                continue
            vraag, opties, juist, uitleg, sleutel = uit
            model = Keuze(v.model, vraag, opties, juist, uitleg)
            return Vraag(self.id, f"{self.id}:{v.sleutel.split(':', 1)[1]}:{soort}{sleutel}", v.tekst, "abc"[juist],
                         "", {**v.data, "soort": soort}, invoer="keuze", model=model,
                         verwacht_tekst=f"{'abc'[juist]}: {opties[juist]}")
        raise RuntimeError("geen schat-vraag gevonden")

    def _ongeveer(self, v, rng):
        m = v.model
        if m.soort != "getal":
            return None  # een tijdstip schat je niet in ordes van grootte
        x = schat(v.antwoord)
        if x == 0:
            return None
        e = m.eenheid if m.eenheid in ("€", "m", "km", "cm", "g", "kg", "ml", "m²") else ""
        waarden = [x, schat(x * 10), schat(x / 10)]
        if len(set(waarden)) < 3:
            return None
        rng.shuffle(waarden)
        opties = [f"ongeveer {tekst_getal(w, e)}" for w in waarden]
        juist = waarden.index(x)
        vraag = f"Reken nog niet uit, maar schat: hoeveel is {m.gevraagd} ongeveer?"
        uitleg = [f"Het juiste antwoord is {v.verwacht}: dat is ongeveer {tekst_getal(x, e)}."]
        if m.controle:
            uitleg.append(f"Controle: {m.controle[2]}")
        return vraag, opties, juist, uitleg, ""

    def _kan(self, v, rng):
        m = v.model
        if not m.controle or m.soort != "getal":
            return None
        lo, hi, waarom = m.controle
        a = F(v.antwoord)
        fout = [w for w in (a * 10, a * 100, a / 10, a / 100) if mooi(w, 2) is not None and w > 0
                and ((lo is not None and w < lo) or (hi is not None and w > hi))]
        wie = _naam(rng)
        if fout and rng.random() < 0.6:
            w, kan = mooi(rng.choice(fout), 2), False
        else:
            w, kan = v.antwoord, True
        vraag = f"{wie} zegt: \"{antwoordzin(m, w)}\" Kan dat kloppen? (Je hoeft het niet uit te rekenen.)"
        opties = ["ja, dat kan kloppen", "nee, dat kan niet"]
        uitleg = [waarom if not kan else f"Ja. {waarom}",
                  f"Het juiste antwoord is {v.verwacht}."]
        return vraag, opties, 0 if kan else 1, uitleg, f"/{'ja' if kan else 'nee'}"

    def lees(self, tekst):
        t = (tekst or "").strip().lower()[:1]
        return t if t in ("a", "b", "c") else None

    def lees_vraag(self, v, tekst):
        return self.lees(tekst)

    def diagnose(self, v, getal):
        if not isinstance(getal, str) or getal == v.antwoord:
            return None
        if v.data.get("soort") == "ongeveer":
            return "vs_schat_10", "Dat is 10 keer te groot of te klein."
        if v.antwoord == "b":
            return "vs_kan_ja", "Dat kan niet kloppen."
        return "vs_kan_nee", "Dat kan wel kloppen."

    def uitleg(self, v):
        return list(v.model.uitleg)

    def tip(self, v):
        return "Rond de getallen af en reken ruw: 4 × € 2,95 is ongeveer 4 × € 3."

    def spiekbrief(self):
        return SPIEKBRIEF


SCHATTEN = Schatten()
ALLE = [VRAAGSTUKKEN, SPEURNEUS, SCHATTEN]
