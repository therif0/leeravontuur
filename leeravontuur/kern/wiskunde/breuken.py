"""Breuken: herkennen en arceren op de breukbalk, gelijkwaardig en vereenvoudigen, vergelijken,
optellen en aftrekken, een breuk van een getal (en vermenigvuldigen/delen), breuk en kommagetal.

Antwoorden zijn Fraction (exact). Een getypte breuk wordt gelezen als GetypteBreuk, zodat de vorm telt
waar de vraag de eenvoudigste vorm eist (data["vereenvoudigd"]).
"""

import math
from decimal import Decimal
from fractions import Fraction

from ..getal import GetypteBreuk, fmt, fmt_breuk
from ..klad import oplossing_van
from ..modellen import Breukbalk, Breukbalken, Groepjes
from ..onderwerp import Onderwerp, Vraag

F = Fraction
D = Decimal
BALK_MAX = 20     # meer stukken passen niet mooi op een balk van 80 kolommen


def _kgv(a, b):
    return a * b // math.gcd(a, b)


def _b(f, gemengd=False):
    return fmt_breuk(f, gemengd)


def _kb(f):
    """Een breuk zoals in het klad: 7/4 (een heel getal zonder noemer)."""
    f = F(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def _ketting(*delen):
    """'a = b = c', zonder twee keer hetzelfde na elkaar (3/4 = 3/4)."""
    uit = []
    for d in delen:
        if not uit or uit[-1] != d:
            uit.append(d)
    return " = ".join(uit)


def _waarde(getal):
    """Getypt antwoord → Fraction (of None)."""
    if isinstance(getal, GetypteBreuk):
        return getal.waarde
    if isinstance(getal, Decimal):
        return F(getal)
    return None


def _breuk(rng, noemer_max, eenvoudig=True, echt=True, noemer_min=2):
    """Een breuk t/n (0 < t < n als echt), liefst in de eenvoudigste vorm."""
    for _ in range(100):
        n = rng.randint(noemer_min, noemer_max)
        t = rng.randint(1, n - 1) if echt else rng.randint(1, 2 * n)
        if not eenvoudig or math.gcd(t, n) == 1:
            return t, n
    return 1, 2


def _gelijknamig_tekst(fs):
    """'1/2 = 3/6 en 1/3 = 2/6' (met de kleinste gemeenschappelijke noemer)."""
    k = math.lcm(*(f.denominator for f in fs))
    delen = [f"{_b(f)} = {f.numerator * (k // f.denominator)}/{k}" for f in fs if f.denominator != k]
    return k, " en ".join(delen)


def balken_gelijknamig(fs):
    """Balken voor de breuken fs, allemaal met de gemeenschappelijke noemer (als die op een balk past)."""
    k = math.lcm(*(f.denominator for f in fs))
    if k > BALK_MAX or any(f < 0 or f > 1 for f in fs):
        return None
    return Breukbalken([Breukbalk.van(f.numerator * (k // f.denominator), k,
                                      _b(f) + (f" = {f.numerator * (k // f.denominator)}/{k}" if f.denominator != k else ""))
                        for f in fs])


SPIEKBRIEF = [
    ("DE BREUKBALK", "accent"),
    ("  3/4: de noemer (4) zegt in hoeveel gelijke stukken je verdeelt,", ""),
    ("  de teller (3) hoeveel stukken je neemt.   ███│███│███│░░░", ""),
    ("", ""),
    ("GELIJKWAARDIG EN VEREENVOUDIGEN", "accent"),
    ("  Teller en noemer × of : hetzelfde getal: 1/2 = 2/4 = 4/8.", ""),
    ("  Vereenvoudigen: deel door de grootste gemene deler. 18/24 → : 6 → 3/4.", ""),
    ("", ""),
    ("VERGELIJKEN EN OPTELLEN", "accent"),
    ("  Zelfde noemer? Vergelijk/tel de tellers. De noemer blijft!", ""),
    ("  Andere noemers? Eerst gelijknamig maken: 1/2 + 1/3 = 3/6 + 2/6 = 5/6.", ""),
    ("  Zelfde teller? Hoe groter de noemer, hoe kleiner de stukken: 1/3 > 1/5.", ""),
    ("", ""),
    ("BREUK VAN EEN GETAL", "accent"),
    ("  2/3 van 12: eerst : 3 (= 4), dan × 2 → 8.", ""),
    ("  Breuk × breuk: teller × teller en noemer × noemer.", ""),
    ("  Delen door een breuk: vermenigvuldigen met het omgekeerde.", ""),
    ("", ""),
    ("BREUK EN KOMMAGETAL", "accent"),
    ("  1/2 = 0,5   1/4 = 0,25   3/4 = 0,75   1/5 = 0,2   1/10 = 0,1   1/100 = 0,01", ""),
]


class _Breuken(Onderwerp):
    vast = ("soort",)

    def spiekbrief(self):
        return SPIEKBRIEF

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def soort(self, p, rng, data):
        return data["soort"] if data and "soort" in data else rng.choice(p["soorten"])

    def niet_vereenvoudigd(self, v, getal):
        if isinstance(getal, GetypteBreuk) and getal.waarde == v.antwoord and not getal.eenvoudigst:
            g = math.gcd(getal.teller, getal.noemer)
            return ("niet_vereenvoudigd", f"{getal} is juist, maar kan nog eenvoudiger: deel teller en noemer "
                    f"door {g}.")
        return None


# ---- herkennen en arceren ------------------------------------------------------------------------

class Herkennen(_Breuken):
    id = "wiskunde.breuken.herkennen"
    naam = "Breuken herkennen"
    spiek_kop = "DE BREUKBALK"
    omschrijving = "welke breuk is gearceerd? zelf arceren"
    denkfouten = {"teller_noemer_omgewisseld": "teller en noemer omgewisseld",
                  "ongearceerd_geteld": "de stukken die niet gearceerd zijn geteld",
                  "deel_tegen_deel": "gearceerd tegen niet-gearceerd vergeleken (in plaats van tegen het geheel)"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        n = rng.choice(p["noemers"])
        t = rng.randint(1, n - 1)
        d = {"soort": soort, "t": t, "n": n, "onderwerp": soort}
        if soort == "aflezen":
            balk = Breukbalk(n, set(rng.sample(range(n), t)))
            return Vraag(self.id, f"{self.id}:aflezen:{t}/{n}", "Welke breuk is gearceerd?", F(t, n), data=d,
                         invoer="breuk", model=balk, verwacht_tekst=f"{t}/{n}")
        d["noemer_vast"] = True
        return Vraag(self.id, f"{self.id}:arceren:{t}/{n}", f"Arceer {t}/{n} van de balk.", F(t, n), data=d,
                     invoer="balk", model=Breukbalk(n), verwacht_tekst=f"{t}/{n}")

    def uitleg(self, v):
        t, n = v.data["t"], v.data["n"]
        return [f"De balk is verdeeld in {n} gelijke stukken: de noemer is {n}.",
                f"{t} {'stuk is' if t == 1 else 'stukken zijn'} gearceerd: de teller is {t}. Dus {t}/{n}."]

    def tip(self, v):
        return "Tel eerst alle stukken (de noemer), dan de gearceerde stukken (de teller)."

    def diagnose(self, v, getal):
        w = _waarde(getal)
        if w is None or w == v.antwoord:
            return None
        t, n = v.data["t"], v.data["n"]
        if w == F(n - t, n):
            return "ongearceerd_geteld", "Je telde de stukken die NIET gearceerd zijn."
        if t and w == F(n, t):
            return "teller_noemer_omgewisseld", "Teller en noemer staan omgekeerd: de noemer (onder) = alle stukken."
        if n - t and w == F(t, n - t):
            return "deel_tegen_deel", f"De noemer is het aantal stukken van de hele balk ({n}), niet alleen de witte."
        return None


# ---- gelijkwaardig en vereenvoudigen ---------------------------------------------------------------

class Gelijkwaardig(_Breuken):
    id = "wiskunde.breuken.gelijkwaardig"
    naam = "Gelijkwaardig en vereenvoudigen"
    spiek_kop = "GELIJKWAARDIG EN VEREENVOUDIGEN"
    omschrijving = "2/3 = ?/12, vereenvoudigen, met de balk"
    denkfouten = {"niet_vereenvoudigd": "niet volledig vereenvoudigd",
                  "alleen_teller": "alleen de teller (of alleen de noemer) veranderd",
                  "opgeteld_ipv_vermenigvuldigd": "bij teller en noemer iets opgeteld in plaats van vermenigvuldigd"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        f = rng.randint(2, p["factor_max"])
        t, n = _breuk(rng, max(2, p["noemer_max"] // f))
        d = {"soort": soort, "t": t, "n": n, "f": f, "onderwerp": soort}
        voor, na = Breukbalk.van(t * f, n * f, f"{t * f}/{n * f}"), Breukbalk.van(t, n, f"{t}/{n}")
        balken = Breukbalken([voor, na]) if n * f <= BALK_MAX else None
        if soort == "aanvullen":
            if rng.random() < 0.5:
                return Vraag(self.id, f"{self.id}:aanvullen:{t}/{n}={t * f}/?", f"{t}/{n} = {t * f}/?  (noemer?)",
                             D(n * f), data={**d, "vraag": "noemer"}, model_na=balken)
            return Vraag(self.id, f"{self.id}:aanvullen:{t}/{n}=?/{n * f}", f"{t}/{n} = ?/{n * f}  (teller?)",
                         D(t * f), data={**d, "vraag": "teller"}, model_na=balken)
        if soort == "vereenvoudigen":
            return Vraag(self.id, f"{self.id}:vereenvoudigen:{t * f}/{n * f}",
                         f"Vereenvoudig {t * f}/{n * f} zo ver mogelijk:", F(t, n),
                         data={**d, "vereenvoudigd": True}, invoer="breuk", model_na=balken)
        # met de balk: toon t/n met een fijnere noemer
        if n * f > BALK_MAX:
            f = max(2, BALK_MAX // n)
            d["f"] = f
        return Vraag(self.id, f"{self.id}:balk:{t}/{n}:{n * f}",
                     f"Toon {t}/{n} met {n * f} stukken (↑↓ noemer, arceer, Enter):", F(t, n),
                     data={**d, "noemer": n * f}, invoer="balk", model=Breukbalk(n),
                     verwacht_tekst=f"{t * f}/{n * f}")

    def nakijken(self, v, getal):
        if v.data["soort"] == "balk":
            return isinstance(getal, GetypteBreuk) and getal.noemer == v.data["noemer"] and getal.waarde == v.antwoord
        return super().nakijken(v, getal)

    def uitleg(self, v):
        t, n, f = v.data["t"], v.data["n"], v.data["f"]
        s = v.data["soort"]
        if s == "aanvullen":
            return [f"Kijk naar wat je weet: {n * f if v.data['vraag'] == 'teller' else t * f} = "
                    f"{n if v.data['vraag'] == 'teller' else t} × {f}.",
                    f"Doe met de andere hetzelfde: {t}/{n} = {t}×{f} / {n}×{f} = {t * f}/{n * f}."]
        if s == "vereenvoudigen":
            return [f"De grootste gemene deler van {t * f} en {n * f} is {math.gcd(t * f, n * f)}.",
                    f"{t * f} : {f} = {t} en {n * f} : {f} = {n}, dus {t}/{n}.",
                    "Dezelfde hoeveelheid, maar grotere stukken."]
        f = v.data["noemer"] // n
        return [f"Zet de noemer op {n * f}: elk stuk van {t}/{n} wordt {f} kleinere stukken.",
                f"Arceer {t} × {f} = {t * f} stukken: {t}/{n} = {t * f}/{n * f}."]

    def tip(self, v):
        if v.data["soort"] == "vereenvoudigen":
            return "Zoek een getal waardoor teller én noemer deelbaar zijn. Kan het daarna nog eens?"
        return "Wat je met de noemer doet, doe je ook met de teller (en omgekeerd)."

    def diagnose(self, v, getal):
        d = self.niet_vereenvoudigd(v, getal)
        if d:
            return d
        t, n, f = v.data["t"], v.data["n"], v.data["f"]
        s = v.data["soort"]
        if s == "aanvullen" and isinstance(getal, Decimal):
            if v.data["vraag"] == "teller" and getal == t + (n * f - n):
                return "opgeteld_ipv_vermenigvuldigd", f"Je telde {n * f - n} bij. De noemer werd × {f}, dus de teller ook."
            if v.data["vraag"] == "noemer" and getal == n + (t * f - t):
                return "opgeteld_ipv_vermenigvuldigd", f"Je telde {t * f - t} bij. De teller werd × {f}, dus de noemer ook."
        if s == "vereenvoudigen" and isinstance(getal, GetypteBreuk):
            if getal.waarde in (F(t, n * f), F(t * f, n)):
                return "alleen_teller", "Deel teller én noemer door hetzelfde getal, niet alleen één van de twee."
        if s == "balk" and isinstance(getal, GetypteBreuk) and getal.waarde == v.antwoord:
            return "alleen_teller", f"{getal} is evenveel, maar gebruik {v.data['noemer']} stukken (↑↓ verandert de noemer)."
        return None


# ---- vergelijken ------------------------------------------------------------------------------------

class Vergelijken(_Breuken):
    id = "wiskunde.breuken.vergelijken"
    naam = "Breuken vergelijken"
    spiek_kop = "VERGELIJKEN EN OPTELLEN"
    omschrijving = "groter, kleiner of gelijk? (<, > of =)"
    denkfouten = {"grotere_noemer_groter": "gedacht dat een grotere noemer een grotere breuk geeft",
                  "alleen_tellers": "alleen de tellers vergeleken bij verschillende noemers"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        nm = p["noemer_max"]
        for _ in range(100):
            if soort == "gelijknamig":
                n = rng.randint(3, nm)
                a, c = rng.sample(range(1, n), 2)
                b = d_ = n
            elif soort == "gelijke_teller":
                a = c = rng.randint(1, 4)
                b, d_ = rng.sample(range(a + 1, nm + 1), 2)
            else:
                a, b = _breuk(rng, nm)
                if rng.random() < 0.2:  # soms gelijkwaardig
                    k = rng.randint(2, 3)
                    c, d_ = a * k, b * k
                else:
                    c, d_ = _breuk(rng, nm)
                if b == d_ or a == c or _kgv(b, d_) > 60:
                    continue
            if (a, b) != (c, d_):
                break
        x, y = F(a, b), F(c, d_)
        antw = "<" if x < y else ">" if x > y else "="
        d = {"soort": soort, "a": a, "b": b, "c": c, "d": d_, "onderwerp": soort}
        return Vraag(self.id, f"{self.id}:{soort}:{a}/{b}?{c}/{d_}", f"{a}/{b}  ?  {c}/{d_}     Typ <, > of =", antw,
                     data=d, invoer="vergelijk", model_na=balken_gelijknamig([x, y]) or
                     (Breukbalken([Breukbalk.van(a, b, f"{a}/{b}"), Breukbalk.van(c, d_, f"{c}/{d_}")])
                      if max(b, d_) <= BALK_MAX else None))

    def uitleg(self, v):
        a, b, c, d = (v.data[k] for k in "abcd")
        if b == d:
            return [f"Zelfde noemer ({b}): vergelijk de tellers. {a} {v.antwoord} {c}, dus {a}/{b} {v.antwoord} {c}/{d}."]
        if a == c:
            return [f"Zelfde teller: hoe groter de noemer, hoe kleiner de stukken.",
                    f"1/{b} {'>' if b < d else '<'} 1/{d}, dus {a}/{b} {v.antwoord} {c}/{d}."]
        k = _kgv(b, d)
        tekst = " en ".join(f"{t}/{n} = {t * k // n}/{k}" for t, n in ((a, b), (c, d)) if n != k)
        return [f"Maak gelijknamig (noemer {k}): {tekst}.",
                f"{a * k // b} {v.antwoord} {c * k // d}, dus {a}/{b} {v.antwoord} {c}/{d}."]

    def tip(self, v):
        return "Zelfde noemer? Kijk naar de tellers. Anders: maak eerst gelijknamig."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        a, b, c, d = (v.data[k] for k in "abcd")
        if a == c and getal == ("<" if b < d else ">"):
            return ("grotere_noemer_groter", f"Een grotere noemer betekent kleinere stukken: 1/{max(b, d)} is kleiner "
                    f"dan 1/{min(b, d)}.")
        if b != d and a != c and getal == ("<" if a < c else ">" if a > c else "="):
            return "alleen_tellers", "Je vergeleek alleen de tellers. Met andere noemers moet je eerst gelijknamig maken."
        return None


# ---- optellen en aftrekken ----------------------------------------------------------------------------

class Optellen(_Breuken):
    id = "wiskunde.breuken.optellen"
    naam = "Optellen en aftrekken"
    spiek_kop = "VERGELIJKEN EN OPTELLEN"
    omschrijving = "gelijknamig, ongelijknamig, gemengde getallen"
    denkfouten = {"tellers_en_noemers": "tellers én noemers opgeteld (1/2 + 1/3 = 2/5)",
                  "niet_gelijknamig": "niet gelijknamig gemaakt (tellers opgeteld, één noemer gehouden)"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        nm = p["noemer_max"]
        op = rng.choice(["+", "−"])
        for _ in range(200):
            if soort == "gelijknamig":
                n = rng.randint(3, nm)
                a, c = rng.randint(1, n - 1), rng.randint(1, n - 1)
                if op == "−" and a < c:
                    a, c = c, a
                x, y = F(a, n), F(c, n)
            elif soort == "ongelijknamig":
                if p["kgv"]:
                    (a, b), (c, d) = _breuk(rng, nm), _breuk(rng, nm)
                else:
                    a, b = _breuk(rng, max(2, nm // 2))
                    d = b * rng.randint(2, max(2, nm // b))
                    c = rng.randint(1, d - 1)
                    if rng.random() < 0.5:
                        a, b, c, d = c, d, a, b
                x, y = F(a, b), F(c, d)
                if x.denominator == y.denominator or _kgv(x.denominator, y.denominator) > 3 * nm:
                    continue
            elif soort == "gemengd":
                x = rng.randint(1, 3) + F(*_breuk(rng, min(nm, 8)))
                y = rng.randint(1, 3) + F(*_breuk(rng, min(nm, 8)))
            else:  # negatief
                x = F(*_breuk(rng, min(nm, 10))) * rng.choice([1, -1])
                y = F(*_breuk(rng, min(nm, 10)))
            if soort != "negatief" and op == "−" and x < y:
                x, y = y, x
            if x == y and op == "−":
                continue
            break
        uit = x + y if op == "+" else x - y
        gemengd = soort == "gemengd"
        tx, ty = _b(x, gemengd), _b(y, gemengd)
        d = {"soort": soort, "x": str(x), "y": str(y), "op": op, "onderwerp": soort,
             "vereenvoudigd": p["vereenvoudigd"]}
        if soort == "gelijknamig":  # zoals getoond: zelfde noemer, niet vereenvoudigd
            tx, ty = f"{a}/{n}", f"{c}/{n}"
            d["n"] = n
        tekst = f"{tx} {op} {ty} ="
        return Vraag(self.id, f"{self.id}:{soort}:{tx}{op}{ty}", tekst, uit, data=d, invoer="breuk",
                     verwacht_tekst=_b(uit, gemengd or abs(uit) > 1) if uit.denominator != 1 else _b(uit),
                     model_na=balken_gelijknamig([x, y, uit]) if 0 <= uit <= 1 and x >= 0 and y >= 0 else None)

    def xy(self, v):
        return F(v.data["x"]), F(v.data["y"])

    klad = "ja"

    def oplossing(self, v):
        x, y = self.xy(v)
        op = v.data["op"]
        n = v.data.get("n") or (x.denominator if x.denominator == y.denominator else
                                x.denominator * y.denominator // math.gcd(x.denominator, y.denominator))
        tx, ty = int(x * n), int(y * n)
        som = tx + ty if op == "+" else tx - ty
        if "n" in v.data or x.denominator == y.denominator:
            return oplossing_van(_ketting(f"{tx}/{n} {op} {ty}/{n}", f"{som}/{n}", _kb(v.antwoord)))
        return oplossing_van(_ketting(f"{_kb(x)} {op} {_kb(y)}", f"{tx}/{n} {op} {ty}/{n}", f"{som}/{n}",
                                      _kb(v.antwoord)))

    def uitleg(self, v):
        x, y = self.xy(v)
        op = v.data["op"]
        regels = []
        if "n" in v.data or x.denominator == y.denominator:
            k = v.data.get("n", x.denominator)
            regels.append(f"Zelfde noemer: {'tel de tellers op' if op == '+' else 'trek de tellers af'}, de noemer "
                          f"({k}) blijft.")
        else:
            k, tekst = _gelijknamig_tekst([x, y])
            regels.append(f"Maak eerst gelijknamig (noemer {k}): {tekst}.")
        tx, ty = x * k, y * k
        uit = v.antwoord
        som = f"{tx + ty if op == '+' else tx - ty}/{k}"
        regels.append(f"{tx}/{k} {op} {ty}/{k} = {som}" + (f" = {v.verwacht}" if v.verwacht != som else "") + ".")
        if uit.denominator != k and v.data.get("vereenvoudigd"):
            regels.append("Vereenvoudig op het einde zo ver mogelijk.")
        return regels

    def tip(self, v):
        x, y = self.xy(v)
        if "n" in v.data or x.denominator == y.denominator:
            return "Zelfde noemer: werk alleen met de tellers. De noemer blijft hetzelfde!"
        return f"Maak eerst gelijknamig. Zoek een getal dat in de tafel van {x.denominator} en van {y.denominator} zit."

    def diagnose(self, v, getal):
        w = _waarde(getal)
        if w is None:
            return None
        d = self.niet_vereenvoudigd(v, getal)
        if d:
            return d
        if w == v.antwoord:
            return None
        x, y = self.xy(v)
        plus = v.data["op"] == "+"
        if isinstance(getal, GetypteBreuk) and not getal.geheel and x.denominator + y.denominator and \
                getal.noemer == (x.denominator + y.denominator if plus else abs(x.denominator - y.denominator)):
            return ("tellers_en_noemers", "Je telde (of trok) ook de noemers op. De noemer zegt hoe groot de stukken "
                    "zijn: die blijft hetzelfde als de breuken gelijknamig zijn.")
        if "n" not in v.data and x.denominator != y.denominator:
            for k in (x.denominator, y.denominator):
                t = x.numerator + y.numerator if plus else x.numerator - y.numerator
                if w == F(t, k):
                    return "niet_gelijknamig", "Je telde de tellers samen zonder eerst gelijknamig te maken."
        return None


# ---- breuk van een getal, vermenigvuldigen en delen -------------------------------------------------------

class BreukVan(_Breuken):
    id = "wiskunde.breuken.van"
    naam = "Breuk van een getal"
    spiek_kop = "BREUK VAN EEN GETAL"
    omschrijving = "2/3 van 12, × en : met breuken"
    denkfouten = {"alleen_gedeeld": "alleen door de noemer gedeeld (de teller vergeten)",
                  "omgekeerd_breuk": "door de teller gedeeld en met de noemer vermenigvuldigd",
                  "noemer_ook_maal": "bij een breuk × getal ook de noemer vermenigvuldigd",
                  "niet_omgekeerd": "bij delen door een breuk niet met het omgekeerde vermenigvuldigd"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        nm = p["noemer_max"]
        d = {"soort": soort, "onderwerp": soort, "vereenvoudigd": True}
        if soort == "van":
            n = rng.randint(2, min(nm, 10))
            t = 1 if p["stambreuk"] else rng.randint(1, n - 1)
            if math.gcd(t, n) != 1:
                t = 1
            m = rng.randint(2, max(2, p["max"] // n))
            g = n * m
            d.update(t=t, n=n, g=g)
            return Vraag(self.id, f"{self.id}:van:{t}/{n}:{g}", f"{t}/{n} van {g} =", D(t * m), data=d,
                         model=Groepjes(g, n), model_na=Groepjes(g, n, t))
        if soort == "maal_nat":
            t, n = _breuk(rng, nm)
            k = rng.randint(2, 9)
            x, y = F(k), F(t, n)
            tekst = f"{k} × {t}/{n} ="
            uit = x * y
        elif soort == "maal_breuk":
            x, y = F(*_breuk(rng, nm)), F(*_breuk(rng, nm))
            tekst, uit = f"{_b(x)} × {_b(y)} =", x * y
        elif soort == "deel_nat":
            x, k = F(*_breuk(rng, nm)), rng.randint(2, 6)
            y = F(k)
            tekst, uit = f"{_b(x)} : {k} =", x / k
        else:  # deel_breuk
            x, y = F(*_breuk(rng, nm)), F(*_breuk(rng, nm))
            tekst, uit = f"{_b(x)} : {_b(y)} =", x / y
        d.update(x=str(x), y=str(y))
        return Vraag(self.id, f"{self.id}:{soort}:{tekst}", tekst, uit, data=d, invoer="breuk",
                     verwacht_tekst=_b(uit, abs(uit) > 1))

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "van":
            t, n, g = d["t"], d["n"], d["g"]
            regels = [f"Verdeel {g} in {n} gelijke groepjes: {g} : {n} = {g // n}."]
            if t > 1:
                regels.append(f"Neem er {t}: {t} × {g // n} = {t * g // n}.")
            return regels
        x, y = F(d["x"]), F(d["y"])
        if s == "maal_nat":
            return [f"Vermenigvuldig alleen de teller: {x.numerator} × {y.numerator} = {x.numerator * y.numerator}. "
                    f"De noemer ({y.denominator}) blijft: {x.numerator * y.numerator}/{y.denominator}"
                    + (f" = {v.verwacht}." if v.verwacht != f"{x.numerator * y.numerator}/{y.denominator}" else ".")]
        if s == "maal_breuk":
            return [f"Teller × teller en noemer × noemer: {x.numerator}×{y.numerator} / {x.denominator}×{y.denominator}"
                    f" = {x.numerator * y.numerator}/{x.denominator * y.denominator}" +
                    (f" = {v.verwacht}." if F(x.numerator * y.numerator, x.denominator * y.denominator).denominator
                     != x.denominator * y.denominator else ".")]
        if s == "deel_nat":
            tekst = f"{x.numerator}/{x.denominator * y.numerator}"
            return [f"Delen door {y.numerator} = de noemer × {y.numerator}: {tekst}" +
                    (f" = {v.verwacht}." if tekst != v.verwacht else ".")]
        return [f"Delen door {_b(y)} = vermenigvuldigen met het omgekeerde ({y.denominator}/{y.numerator}).",
                f"{_b(x)} × {y.denominator}/{y.numerator} = {v.verwacht}."]

    klad = "ja"

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s == "van":
            t, n, g = d["t"], d["n"], d["g"]
            return oplossing_van(f"{g} : {n} = {g // n}", f"{t} × {g // n} = {t * g // n}" if t > 1 else "")
        x, y, uit = F(d["x"]), F(d["y"]), F(v.antwoord)
        if s == "maal_nat":
            k = x.numerator
            return oplossing_van(_ketting(f"{k} × {_kb(y)}", f"{k * y.numerator}/{y.denominator}", _kb(uit)))
        if s == "maal_breuk":
            return oplossing_van(_ketting(f"{_kb(x)} × {_kb(y)}",
                                          f"{x.numerator * y.numerator}/{x.denominator * y.denominator}", _kb(uit)))
        if s == "deel_nat":
            k = y.numerator
            return oplossing_van(_ketting(f"{_kb(x)} : {k}", f"{x.numerator}/{x.denominator * k}", _kb(uit)))
        return oplossing_van(_ketting(f"{_kb(x)} : {_kb(y)}", f"{_kb(x)} × {y.denominator}/{y.numerator}",
                                      f"{x.numerator * y.denominator}/{x.denominator * y.numerator}", _kb(uit)))

    def tip(self, v):
        return {"van": "Eerst delen door de noemer, dan vermenigvuldigen met de teller.",
                "maal_nat": "Getal × breuk: vermenigvuldig de teller, de noemer blijft.",
                "maal_breuk": "Teller × teller, noemer × noemer. Vereenvoudig op het einde.",
                "deel_nat": "Een breuk delen door een getal: vermenigvuldig de noemer met dat getal.",
                "deel_breuk": "Delen door een breuk = vermenigvuldigen met het omgekeerde."}[v.data["soort"]]

    def diagnose(self, v, getal):
        d = self.niet_vereenvoudigd(v, getal)
        if d:
            return d
        w = _waarde(getal)
        if w is None or w == v.antwoord:
            return None
        s = v.data["soort"]
        if s == "van":
            t, n, g = v.data["t"], v.data["n"], v.data["g"]
            if t > 1 and w == g // n:
                return "alleen_gedeeld", f"Je deelde door {n}, maar vergat daarna × {t} te doen."
            if w == F(g * n, t):
                return "omgekeerd_breuk", f"Omgekeerd: eerst : {n} (de noemer), dan × {t} (de teller)."
            return None
        x, y = F(v.data["x"]), F(v.data["y"])
        if s == "maal_nat" and isinstance(getal, GetypteBreuk) and \
                getal.noemer == y.denominator * x.numerator:
            return "noemer_ook_maal", "Bij getal × breuk wordt alleen de teller vermenigvuldigd."
        if s == "deel_breuk" and w == x * y:
            return "niet_omgekeerd", "Je vermenigvuldigde gewoon. Bij delen door een breuk keer je ze eerst om."
        return None


# ---- breuk en kommagetal ----------------------------------------------------------------------------------

class Kommagetal(_Breuken):
    id = "wiskunde.breuken.kommagetal"
    naam = "Breuk en kommagetal"
    spiek_kop = "BREUK EN KOMMAGETAL"
    omschrijving = "3/4 = 0,75 en 0,6 = 3/5"
    denkfouten = {"breuk_als_komma": "de breuk gelezen als kommagetal (3/4 = 3,4)",
                  "tiende_honderdste": "tienden en honderdsten verwisseld"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        n = rng.choice(p["noemers"])
        t = rng.randint(1, n - 1)
        while math.gcd(t, n) != 1:
            t = rng.randint(1, n - 1)
        komma = D(t) / D(n)
        d = {"soort": soort, "t": t, "n": n, "onderwerp": soort, "vereenvoudigd": True}
        if soort == "naar_komma":
            return Vraag(self.id, f"{self.id}:naar_komma:{t}/{n}", f"{t}/{n} = ?  (als kommagetal)", komma, data=d)
        return Vraag(self.id, f"{self.id}:naar_breuk:{fmt(komma)}",
                     f"{fmt(komma)} = ?  (als breuk, zo eenvoudig mogelijk)", F(t, n), data=d, invoer="breuk")

    def uitleg(self, v):
        t, n = v.data["t"], v.data["n"]
        komma = D(t) / D(n)
        dec = max(1, -komma.normalize().as_tuple().exponent)
        macht = 10 ** dec
        noem = {10: "tienden", 100: "honderdsten", 1000: "duizendsten"}[macht]
        if t * macht // n == 1:
            noem = noem[:-1] if macht == 10 else noem[:-1]
        if v.data["soort"] == "naar_komma":
            return [f"Maak een noemer 10, 100 of 1000: {t}/{n} = {t * macht // n}/{macht}.",
                    f"{t * macht // n} {noem} = {fmt(komma)}."]
        return [f"{fmt(komma)} = {t * macht // n} {noem} = {t * macht // n}/{macht}.",
                f"Vereenvoudig: {t * macht // n}/{macht} = {t}/{n}."]

    def tip(self, v):
        return "Denk aan tienden en honderdsten: 0,25 = 25/100. En 1/4 = 25/100."

    def diagnose(self, v, getal):
        d = self.niet_vereenvoudigd(v, getal)
        if d:
            return d
        w = _waarde(getal)
        if w is None or w == F(v.antwoord):
            return None
        t, n = v.data["t"], v.data["n"]
        if v.data["soort"] == "naar_komma" and getal == D(f"{t}.{n}"):
            return "breuk_als_komma", "Een breukstreep is geen komma: 3/4 betekent 3 : 4."
        if w in (F(v.antwoord) * 10, F(v.antwoord) / 10):
            return "tiende_honderdste", "Let op tienden (0,1) en honderdsten (0,01)."
        return None


HERKENNEN = Herkennen()
GELIJKWAARDIG = Gelijkwaardig()
VERGELIJKEN = Vergelijken()
OPTELLEN = Optellen()
BREUK_VAN = BreukVan()
KOMMAGETAL = Kommagetal()
ALLE = [HERKENNEN, GELIJKWAARDIG, VERGELIJKEN, OPTELLEN, BREUK_VAN, KOMMAGETAL]
