"""Getallen: plaatswaarde, afronden, deelbaarheid (en delers, veelvouden, priemgetallen, ggd, kgv) en de
getallenlijn (aflezen, aanduiden met inzoomen, sprongen, thermometer met negatieve getallen).
"""

import math
from decimal import ROUND_HALF_UP, Decimal

from ..getal import fmt, fmt_groot
from ..modellen import Getallenlijn
from ..onderwerp import Onderwerp, Vraag

D = Decimal

PLAATSEN = [  # (macht van 10, naam, afkorting)
    (6, "miljoenen", "M"), (5, "honderdduizendtallen", "HD"), (4, "tienduizendtallen", "TD"),
    (3, "duizendtallen", "D"), (2, "honderdtallen", "H"), (1, "tientallen", "T"), (0, "eenheden", "E"),
    (-1, "tienden", "t"), (-2, "honderdsten", "h"), (-3, "duizendsten", "d"),
]
NAAM = {k: n for k, n, _ in PLAATSEN}
AFK = {k: a for k, _, a in PLAATSEN}


def _getal(rng, cijfers, decimalen, verschillend=True):
    """Een getal met `cijfers` cijfers voor de komma en `decimalen` erna (liefst allemaal verschillend)."""
    for _ in range(100):
        tekst = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(cijfers - 1 + decimalen))
        if not verschillend or len(set(tekst)) == len(tekst) or cijfers + decimalen > 10:
            break
    return D(tekst).scaleb(-decimalen)


def _cijfer_op(getal, k):
    return int(abs(getal).scaleb(-k) // 1 % 10)


class _Getallen(Onderwerp):
    def spiekbrief(self):
        return SPIEKBRIEF


# ---- plaatswaarde ----------------------------------------------------------------------

class Plaatswaarde(_Getallen):
    id = "wiskunde.getallen.plaatswaarde"
    naam = "Plaatswaarde"
    omschrijving = "wat is elk cijfer waard? (E, T, H … t, h)"
    denkfouten = {"cijfer_ipv_waarde": "het cijfer gegeven in plaats van zijn waarde",
                  "verkeerde_plaats": "een plaats ernaast gekeken"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        cijfers = rng.randint(max(2, p["max_cijfers"] - 2), p["max_cijfers"])
        dec = rng.randint(0, p["decimalen"])
        g = _getal(rng, cijfers, dec)
        soort = data["soort"] if data and "soort" in data else rng.choice(["cijfer", "waarde", "samenstellen"])
        plaatsen = [k for k in range(cijfers - 1, -dec - 1, -1) if _cijfer_op(g, k) != 0]
        k = rng.choice(plaatsen)
        c = _cijfer_op(g, k)
        d = {"soort": soort, "getal": str(g), "k": k, "cijfers": cijfers, "dec": dec, "onderwerp": soort}
        if soort == "cijfer":
            return Vraag(self.id, f"{self.id}:cijfer:{fmt(g)}:{k}",
                         f"Welk cijfer staat bij de {NAAM[k]} in {fmt_groot(g)}?", D(c), data=d)
        if soort == "waarde":
            return Vraag(self.id, f"{self.id}:waarde:{fmt(g)}:{k}",
                         f"Hoeveel is de {c} waard in {fmt_groot(g)}?", D(c).scaleb(k), data=d)
        delen = [(kk, _cijfer_op(g, kk)) for kk in range(cijfers - 1, -dec - 1, -1) if _cijfer_op(g, kk)]
        rng.shuffle(delen)
        tekst = " + ".join(f"{c_} {AFK[kk]}" for kk, c_ in delen)
        d["delen"] = delen
        return Vraag(self.id, f"{self.id}:samenstellen:{fmt(g)}", f"Schrijf als getal: {tekst} =", g, data=d)

    def uitleg(self, v):
        d = v.data
        g, k = D(d["getal"]), d["k"]
        rij = "  ".join(f"{AFK[kk]}:{_cijfer_op(g, kk)}" for kk in range(d["cijfers"] - 1, -d["dec"] - 1, -1))
        if d["soort"] == "cijfer":
            return [f"Zet {fmt_groot(g)} in een tabel: {rij}", f"Bij de {NAAM[k]} staat een {_cijfer_op(g, k)}."]
        if d["soort"] == "waarde":
            c = _cijfer_op(g, k)
            return [f"De {c} staat bij de {NAAM[k]}.",
                    f"Hij is dus {c} × {fmt_groot(D(1).scaleb(k))} = {fmt_groot(v.antwoord)} waard."]
        return ["Zet elk cijfer op zijn plaats (E = eenheden, T = tientallen, H = honderdtallen, D = duizendtallen, "
                "t = tienden, h = honderdsten).", f"Je krijgt: {rij} → {fmt_groot(g)}",
                "Een plaats zonder cijfer krijgt een 0."]

    def tip(self, v):
        return "Tel vanaf de komma (of vanaf rechts): E, T, H, D, TD … en na de komma t, h, d."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        g, k = D(d["getal"]), d["k"]
        if d["soort"] == "waarde" and getal == _cijfer_op(g, k):
            return "cijfer_ipv_waarde", "Je gaf het cijfer. Gevraagd is wat het waard is: denk aan zijn plaats."
        if d["soort"] == "cijfer" and getal in (_cijfer_op(g, k + 1), _cijfer_op(g, k - 1)):
            return "verkeerde_plaats", "Dat cijfer staat één plaats ernaast. Tel de plaatsen nog eens."
        return None

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None


# ---- afronden ------------------------------------------------------------------------------

class Afronden(_Getallen):
    id = "wiskunde.getallen.afronden"
    naam = "Afronden"
    omschrijving = "op tientallen, honderdtallen … en tienden"
    denkfouten = {"afgekapt": "afgekapt in plaats van afgerond", "verkeerde_plaats_afronden": "op de verkeerde plaats afgerond"}
    vast = ("k",)

    def maak_met(self, p, rng, data=None):
        k = data["k"] if data and "k" in data else rng.choice(p["plaatsen"])
        cijfers = max(k + 2, rng.randint(2, p["max_cijfers"])) if k >= 0 else rng.randint(1, 3)
        dec = max(0, -k + 1) if k < 0 else rng.randint(0, p["decimalen"])
        g = _getal(rng, cijfers, dec, verschillend=False)
        uit = (g.scaleb(-k)).quantize(D(1), rounding=ROUND_HALF_UP).scaleb(k)
        d = {"getal": str(g), "k": k, "onderwerp": NAAM[k]}
        return Vraag(self.id, f"{self.id}:{k}:{fmt(g)}", f"Rond {fmt_groot(g)} af op {NAAM[k]}:", uit.normalize(),
                     data=d)

    def uitleg(self, v):
        g, k = D(v.data["getal"]), v.data["k"]
        rechts = _cijfer_op(g, k - 1)
        omhoog = rechts >= 5
        return [f"Kijk naar het cijfer rechts van de {NAAM[k]}: dat is een {rechts}.",
                f"{rechts} is {'5 of meer: naar boven' if omhoog else 'minder dan 5: naar beneden'} afronden.",
                f"{fmt_groot(g)} ≈ {fmt_groot(v.antwoord)}"]

    def tip(self, v):
        return "Kijk naar het cijfer net rechts van de plaats waarop je afrondt: 0-4 naar beneden, 5-9 naar boven."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        g, k = D(v.data["getal"]), v.data["k"]
        if getal == (g.scaleb(-k) // 1).scaleb(k):
            return "afgekapt", "Je liet de cijfers gewoon weg (afkappen). Kijk naar het cijfer rechts: is het 5 of meer?"
        for kk in (k - 1, k + 1):
            if getal == g.scaleb(-kk).quantize(D(1), rounding=ROUND_HALF_UP).scaleb(kk):
                return "verkeerde_plaats_afronden", f"Je rondde af op de {NAAM.get(kk, '?')}, niet op de {NAAM[k]}."
        return None

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return NAAM.get(int(delen[1])) if len(delen) >= 3 and delen[0] == self.id else None


# ---- deelbaarheid, delers, veelvouden ------------------------------------------------------------

REGELS = {
    2: "het laatste cijfer is even (0, 2, 4, 6 of 8)",
    3: "de som van de cijfers is deelbaar door 3",
    4: "het getal gevormd door de laatste twee cijfers is deelbaar door 4",
    5: "het laatste cijfer is 0 of 5",
    6: "het getal is deelbaar door 2 én door 3",
    9: "de som van de cijfers is deelbaar door 9",
    10: "het laatste cijfer is 0",
    25: "het eindigt op 00, 25, 50 of 75",
    100: "het eindigt op 00",
}


def _delers(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def _priem(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


class Deelbaarheid(_Getallen):
    id = "wiskunde.getallen.deelbaarheid"
    naam = "Deelbaarheid"
    omschrijving = "kenmerken, delers, priemgetallen, ggd, kgv"
    denkfouten = {"kenmerk": "het kenmerk van deelbaarheid verkeerd toegepast"}
    vast = ("soort", "deler")

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else rng.choice(p["soorten"])
        d = {"soort": soort, "onderwerp": soort}
        if soort == "deelbaar":
            deler = data["deler"] if data and "deler" in data else rng.choice(p["delers"])
            n = rng.randint(p["max"] // 20, p["max"])
            if rng.random() < 0.5:
                n -= n % deler  # een veelvoud
            n = max(n, deler)
            d.update(deler=deler, n=n, onderwerp=f"deelbaar door {deler}")
            return Vraag(self.id, f"{self.id}:deelbaar:{deler}:{n}", f"Is {fmt_groot(D(n))} deelbaar door {deler}? "
                         "(ja of nee)", "ja" if n % deler == 0 else "nee", data=d, invoer="janee")
        if soort == "priem":
            n = rng.randint(2, 100)
            d["n"] = n
            return Vraag(self.id, f"{self.id}:priem:{n}", f"Is {n} een priemgetal? (ja of nee)",
                         "ja" if _priem(n) else "nee", data=d, invoer="janee")
        if soort == "delers":
            n = rng.choice([12, 16, 18, 20, 24, 28, 30, 32, 36, 40, 42, 45, 48, 50, 60])
            d["n"] = n
            return Vraag(self.id, f"{self.id}:delers:{n}", f"Hoeveel delers heeft {n}?", D(len(_delers(n))), data=d)
        a, b = rng.sample([2, 3, 4, 5, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 24, 30], 2)
        d.update(a=a, b=b)
        if soort == "ggd":
            return Vraag(self.id, f"{self.id}:ggd:{a}:{b}", f"Wat is de grootste gemene deler van {a} en {b}?",
                         D(math.gcd(a, b)), data=d)
        return Vraag(self.id, f"{self.id}:kgv:{a}:{b}", f"Wat is het kleinste gemeen veelvoud van {a} en {b}?",
                     D(a * b // math.gcd(a, b)), data=d)

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "deelbaar":
            n, deler = d["n"], d["deler"]
            regels = [f"Deelbaar door {deler}: {REGELS[deler]}."]
            if deler in (3, 6, 9):
                som, door = sum(int(c) for c in str(n)), 9 if deler == 9 else 3
                regels.append(f"{' + '.join(str(n))} = {som}, en {som} is {'' if som % door == 0 else 'niet '}"
                              f"deelbaar door {door}.")
            regels.append(f"{fmt_groot(D(n))} : {deler} = {fmt(D(n) / deler)}, dus {'ja' if n % deler == 0 else 'nee'}.")
            return regels
        if s == "priem":
            n = d["n"]
            if _priem(n):
                return [f"{n} is alleen deelbaar door 1 en door {n} zelf: een priemgetal."]
            kleinste = next(x for x in range(2, n + 1) if n % x == 0)
            return [f"{n} = {kleinste} × {n // kleinste}, dus {n} heeft meer delers dan 1 en zichzelf: geen priemgetal."
                    if n > 1 else "1 is geen priemgetal."]
        if s == "delers":
            ds = _delers(d["n"])
            return [f"De delers van {d['n']}: {', '.join(map(str, ds))}.", f"Dat zijn er {len(ds)}.",
                    "Zoek ze in paren: 1 × …, 2 × …, 3 × … zo vind je ze allemaal."]
        a, b = d["a"], d["b"]
        if s == "ggd":
            return [f"Delers van {a}: {', '.join(map(str, _delers(a)))}", f"Delers van {b}: {', '.join(map(str, _delers(b)))}",
                    f"De grootste die in allebei zit: {math.gcd(a, b)}."]
        veelvouden_a = [a * i for i in range(1, 11)]
        return [f"Veelvouden van {a}: {', '.join(map(str, veelvouden_a[:8]))} …",
                f"Veelvouden van {b}: {', '.join(str(b * i) for i in range(1, 9))} …",
                f"Het kleinste dat in allebei zit: {a * b // math.gcd(a, b)}."]

    def tip(self, v):
        if v.data["soort"] == "deelbaar":
            return f"Kenmerk: {REGELS[v.data['deler']]}."
        return {"priem": "Een priemgetal heeft precies 2 delers: 1 en zichzelf.",
                "delers": "Zoek de delers in paren: 1 × 24, 2 × 12, 3 × 8 …",
                "ggd": "Schrijf de delers van allebei op en zoek de grootste die ze samen hebben.",
                "kgv": "Schrijf de veelvouden van allebei op en zoek het kleinste dat ze samen hebben."}[v.data["soort"]]

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord or v.data["soort"] != "deelbaar":
            return None
        return "kenmerk", f"Gebruik het kenmerk: {REGELS[v.data['deler']]}."

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        if len(delen) < 3 or delen[0] != self.id:
            return None
        return f"deelbaar door {delen[2]}" if delen[1] == "deelbaar" else delen[1]


# ---- de getallenlijn ----------------------------------------------------------------------------

class GetallenlijnOnderwerp(_Getallen):
    id = "wiskunde.getallen.getallenlijn"
    naam = "Getallenlijn"
    omschrijving = "aflezen, aanduiden, sprongen, thermometer"
    denkfouten = {"streepje_ernaast": "één streepje ernaast", "niet_ingezoomd": "niet ver genoeg ingezoomd",
                  "sprong_verkeerde_kant": "de verkeerde kant op gesprongen"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else rng.choice(p["soorten"])
        dec = p["decimalen"]
        d = {"soort": soort, "onderwerp": soort}
        if soort in ("aflezen", "aanduiden"):
            if dec and rng.random() < 0.7:
                stap = D(1).scaleb(-rng.randint(1, dec))
                van = D(rng.randint(0, 9)) * stap * 10 if stap < D("0.1") else D(rng.randint(0, 9))
            else:
                stap = D(rng.choice([1, 10, 100])) if p["max"] >= 1000 else D(rng.choice([1, 10]))
                van = D(rng.randint(0, max(0, p["max"] // int(stap) // 10 - 1))) * stap * 10
                if p["negatief"] and rng.random() < 0.4:
                    van = -stap * 5
            lijn = Getallenlijn(van, van + stap * 10, stap, label_elke=5)
            if soort == "aflezen":
                waarde = van + stap * rng.randint(1, 9)
                lijn.pijl = waarde
                d.update(waarde=str(waarde), stap=str(stap))
                return Vraag(self.id, f"{self.id}:aflezen:{fmt(van)}:{fmt(waarde)}",
                             "Welk getal staat bij de pijl ▼ ?", waarde, data=d, model=lijn)
            # aanduiden: soms tussen twee streepjes (dan moet het kind inzoomen)
            minste = D(1).scaleb(-dec)
            fijner = stap / 10 if stap / 10 >= minste and rng.random() < 0.5 else stap
            stukken = int(10 * stap / fijner)  # niet op een streepje met een getal eronder (te makkelijk)
            waarde = van + fijner * rng.choice([i for i in range(1, stukken) if fijner * i / stap % 5])
            d.update(waarde=str(waarde), stap=str(stap), fijn=str(fijner), minste=str(minste))
            return Vraag(self.id, f"{self.id}:aanduiden:{fmt(waarde)}", f"Duid {fmt(waarde)} aan op de getallenlijn.",
                         waarde, data=d, invoer="lijn", model=lijn)
        if soort == "sprong":
            grens = 10 if p["max"] <= 100 else 20
            a = rng.randint(-grens + 2, grens - 2) if p["negatief"] else rng.randint(0, grens - 2)
            sprong = rng.randint(2, grens // 2) * rng.choice([1, -1])
            if not p["negatief"]:
                sprong = abs(sprong) if a + abs(sprong) <= grens else -min(abs(sprong), a)
            b = a + sprong
            d.update(a=a, sprong=sprong)
            van = (min(a, b) - 2) // 5 * 5 if p["negatief"] else max(0, (min(a, b) - 2) // 5 * 5)
            tot = -(-(max(a, b) + 2) // 5) * 5
            lijn = Getallenlijn(D(van), D(tot), D(1), label_elke=5, markeringen={D(a): "start"})
            op = "+" if sprong >= 0 else "−"
            return Vraag(self.id, f"{self.id}:sprong:{a}{op}{abs(sprong)}", f"{fmt(D(a))} {op} {abs(sprong)} =",
                         D(b), data=d, model=lijn)
        # temperatuur (thermometer)
        nu = rng.randint(-10, 8)
        verschil = rng.randint(2, 9) * rng.choice([1, -1])
        d.update(nu=nu, verschil=verschil)
        lijn = Getallenlijn(D(-15), D(15), D(1), label_elke=5, eenheid="°C", vulling=D(nu), markeringen={D(nu): "nu"})
        wat = f"{verschil} graden warmer" if verschil > 0 else f"{-verschil} graden kouder"
        return Vraag(self.id, f"{self.id}:temperatuur:{nu}:{verschil}",
                     f"Het is {fmt(D(nu))} °C. Het wordt {wat}. Hoeveel °C is het dan?", D(nu + verschil),
                     eenheid="°C", data=d, model=lijn)

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "aflezen":
            return [f"Elk streepje is {fmt(D(d['stap']))} verder.", f"Tel vanaf {fmt(v.model.van)}: de pijl staat bij "
                    f"{fmt(v.antwoord)}."]
        if s == "aanduiden":
            regels = [f"De streepjes liggen {fmt(D(d['stap']))} uit elkaar."]
            if D(d["fijn"]) < D(d["stap"]):
                onder = (v.antwoord // D(d["stap"])) * D(d["stap"])
                regels.append(f"{fmt(v.antwoord)} ligt tussen {fmt(onder)} en {fmt(onder + D(d['stap']))}: "
                              f"zoom daar in met + (elk nieuw streepje is {fmt(D(d['fijn']))}).")
            regels.append(f"Zet de pijl op {fmt(v.antwoord)} en druk Enter.")
            return regels
        if s == "sprong":
            a, sp = d["a"], d["sprong"]
            richting = "rechts" if sp > 0 else "links"
            tussen = ", ".join(fmt(D(a + i * (1 if sp > 0 else -1))) for i in range(1, abs(sp) + 1))
            return [f"Start bij {fmt(D(a))} en spring {abs(sp)} naar {richting}: {tussen}.", f"Je komt uit bij {fmt(v.antwoord)}."]
        nu, vers = d["nu"], d["verschil"]
        return [f"Warmer = naar boven (naar rechts), kouder = naar beneden (naar links).",
                f"Van {fmt(D(nu))} °C {abs(vers)} graden {'omhoog' if vers > 0 else 'omlaag'}: {fmt(v.antwoord)} °C.",
                "Onder 0 wordt het getal na het minteken groter als het kouder wordt."]

    def tip(self, v):
        s = v.data["soort"]
        if s == "aanduiden":
            return "Beweeg de pijl met ← en →. Ligt het getal tussen twee streepjes? Zoom in met + (en terug met −)."
        if s == "aflezen":
            return "Kijk eerst hoeveel elk streepje waard is."
        return "Teken de sprong in gedachten op de getallenlijn: plus = naar rechts, min = naar links."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        if d["soort"] == "aanduiden":
            if D(d["fijn"]) < D(d["stap"]) and abs(getal - v.antwoord) < D(d["stap"]) and \
                    getal % D(d["stap"]) == 0:
                return "niet_ingezoomd", "Je stond bij het dichtstbijzijnde grote streepje. Zoom in met + om preciezer te zijn."
            if abs(getal - v.antwoord) in (D(d["fijn"]), D(d["stap"])):
                return "streepje_ernaast", "Bijna! Je stond één streepje ernaast."
        if d["soort"] == "sprong" and getal == d["a"] - d["sprong"]:
            return "sprong_verkeerde_kant", "Je sprong de verkeerde kant op: plus = naar rechts, min = naar links."
        if d["soort"] == "temperatuur" and getal == d["nu"] - d["verschil"]:
            return "sprong_verkeerde_kant", "Warmer is naar boven (hoger getal), kouder naar beneden."
        return None

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None


SPIEKBRIEF = [
    ("PLAATSWAARDE", "accent"),
    ("  M  HD  TD  D  H  T  E , t  h  d", "bold"),
    ("  M = miljoenen, HD = honderdduizendtallen, TD = tienduizendtallen,", ""),
    ("  D = duizendtallen, H = honderdtallen, T = tientallen, E = eenheden,", ""),
    ("  t = tienden, h = honderdsten, d = duizendsten", ""),
    ("  In 3 405,7 is de 4 vierhonderd waard (4 H), de 7 zeven tienden (0,7).", ""),
    ("", ""),
    ("AFRONDEN", "accent"),
    ("  Kijk naar het cijfer rechts: 0-4 naar beneden, 5-9 naar boven.", ""),
    ("  3 467 op honderdtallen: rechts van de 4 staat een 6, dus 3 500.", ""),
    ("", ""),
    ("DEELBAAR DOOR …", "accent"),
    *((f"  {d:>3}: {r}", "") for d, r in REGELS.items()),
    ("  Priemgetal: precies 2 delers (1 en zichzelf): 2, 3, 5, 7, 11, 13, 17 …", ""),
    ("  ggd = grootste gemene deler, kgv = kleinste gemeen veelvoud.", ""),
    ("", ""),
    ("GETALLENLIJN", "accent"),
    ("  Hoeveel is één streepje waard? Plus = naar rechts, min = naar links.", ""),
    ("  Tussen twee streepjes? Zoom in met +: 10 kleinere streepjes.", ""),
    ("  Onder nul: −5 is kouder (kleiner) dan −2. Hoe verder links, hoe kleiner.", ""),
]

PLAATSWAARDE = Plaatswaarde()
AFRONDEN = Afronden()
DEELBAARHEID = Deelbaarheid()
GETALLENLIJN = GetallenlijnOnderwerp()
ALLE = [PLAATSWAARDE, AFRONDEN, DEELBAARHEID, GETALLENLIJN]
