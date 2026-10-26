"""Hoofdrekenen: tafels, optellen en aftrekken, × en : met 10/100/1000, verdubbelen en halveren, slim × en : (splitsen).

Elke vraag krijgt een strategie mee die de uitleg stap voor stap toont (compenseren, splitsen, verdubbelen …).
"""

from decimal import Decimal
from fractions import Fraction

from ..getal import decimalen, fmt
from ..klad import DEEL, MAAL, MIN, PLUS, fout_pad, stap
from ..modellen import Oplossing
from ..onderwerp import Onderwerp, Vraag

D = Decimal


def _f(x):
    return fmt(D(x))


def _plaats(n, k):
    return {1: "tientallen", 2: "honderdtallen", 3: "duizendtallen"}.get(k, "cijfers")


# ---- tafels ---------------------------------------------------------------------------

class Tafels(Onderwerp):
    id = "wiskunde.hoofdrekenen.tafels"
    naam = "Maal- en deeltafels"
    omschrijving = "de tafels van vermenigvuldiging en de deeltafels"
    denkfouten = {"plus_ipv_maal": "opgeteld in plaats van vermenigvuldigd",
                  "buurtafel": "één stap ernaast in de tafel",
                  "deel_omgekeerd": "vermenigvuldigd in plaats van gedeeld"}
    vast = ("tafel",)

    def maak_met(self, p, rng, data=None):
        tafel = data["tafel"] if data and "tafel" in data else rng.choice(p["tafels"])
        f = rng.randint(1, p["max_factor"])
        veelvoud = p["veelvoud"] and rng.random() < 0.25
        delen = p["delen"] and rng.random() < 0.4
        a, b = tafel, f * (10 if veelvoud else 1)
        if p["negatief"] and rng.random() < 0.5:
            if rng.random() < 0.5:
                a = -a
            else:
                b = -b
        c = a * b
        d = {"tafel": tafel, "a": a, "b": b, "delen": delen, "veelvoud": veelvoud, "onderwerp": f"tafel {tafel}"}
        if delen and b != 0:
            return Vraag(self.id, f"{self.id}:t{tafel}:{c}:{a}", f"{_f(c)} : {_f(a)} =", D(b), data=d)
        links, rechts = (a, b) if rng.random() < 0.5 else (b, a)
        d["links"], d["rechts"] = links, rechts
        return Vraag(self.id, f"{self.id}:t{tafel}:{links}x{rechts}", f"{_f(links)} × {_f(rechts)} =", D(c), data=d)

    def kies_onderwerp(self, gewichten, p, rng):
        tafels = p["tafels"]
        w = [gewichten.get(f"tafel {t}", 1.0) for t in tafels]
        return {"tafel": rng.choices(tafels, weights=w, k=1)[0]}

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return f"tafel {delen[1][1:]}" if len(delen) >= 3 and delen[0] == self.id else None

    def uitleg(self, v):
        d = v.data
        a, b = d["a"], d["b"]
        c = a * b
        regels = []
        if d["delen"]:
            regels += [f"{_f(c)} : {_f(a)} = ? Denk: welk getal maal {_f(a)} is {_f(c)}?",
                       f"{_f(a)} × {_f(b)} = {_f(c)}, dus {_f(c)} : {_f(a)} = {_f(b)}."]
        else:
            t, m = abs(a), abs(b)
            if d["veelvoud"]:
                regels.append(f"Reken eerst {t} × {m // 10} = {t * m // 10}, en dan × 10: {t * m}.")
            elif 9 in (t, m):
                n = m if t == 9 else t
                regels.append(f"× 9 = × 10 min één keer: {n} × 10 = {10 * n}, min {n} = {9 * n}.")
            elif 5 in (t, m):
                n = m if t == 5 else t
                regels.append(f"× 5 = de helft van × 10: {n} × 10 = {10 * n}, de helft is {5 * n}.")
            elif m in (2, 4, 8) or t in (2, 4, 8):
                k, n = (m, t) if m in (2, 4, 8) else (t, m)
                keten, x = [str(n)], n
                while k > 1:
                    x, k = 2 * x, k // 2
                    keten.append(str(x))
                regels.append(f"× {abs(b) if m in (2, 4, 8) else abs(a)} = verdubbelen: " + " → ".join(keten) + ".")
            elif m > 1:
                regels.append(f"Ken je {t} × {m - 1} = {t * (m - 1)}? Dan nog {t} erbij: {t * m}.")
            regels.append(f"{_f(d.get('links', a))} × {_f(d.get('rechts', b))} = {_f(c)}")
        if a < 0 or b < 0:
            regels.append("Let op het teken: plus maal min is min, min maal min is plus.")
        return regels

    def tip(self, v):
        return "Zoek een tafel die je al kent en reken van daaruit verder." if not v.data["delen"] else \
            "Delen is omgekeerd vermenigvuldigen: welk getal maal …?"

    def diagnose(self, v, getal):
        d = v.data
        if getal is None or getal == v.antwoord:
            return None
        a, b = d["a"], d["b"]
        if d["delen"]:
            if getal == a * b * a:
                return "deel_omgekeerd", "Je vermenigvuldigde. Bij delen zoek je: welk getal maal … geeft …?"
            return None
        if getal == a + b:
            return "plus_ipv_maal", f"Je telde op ({_f(a)} + {_f(b)}). Hier moet je vermenigvuldigen."
        if getal in {a * (b + 1), a * (b - 1), (a + 1) * b, (a - 1) * b} and not d["veelvoud"]:
            return "buurtafel", "Bijna! Je zat één stap ernaast in de tafel. Tel nog eens na."
        return None

    def spiekbrief(self):
        return SPIEKBRIEF


# ---- optellen en aftrekken ----------------------------------------------------------------

class PlusMin(Onderwerp):
    id = "wiskunde.hoofdrekenen.plusmin"
    naam = "Optellen en aftrekken"
    omschrijving = "uit het hoofd optellen en aftrekken met strategieën"
    denkfouten = {"compenseren_verkeerd": "bij compenseren de verkeerde kant op verbeterd",
                  "onthouden": "een tiental of honderdtal vergeten (onthouden)",
                  "verkeerde_bewerking": "opgeteld en afgetrokken door elkaar"}
    vast = ("op", "strategie")

    def maak_met(self, p, rng, data=None):
        schaal = 10 ** p["decimalen"]
        maximum = p["max"] * schaal if not p["decimalen"] else p["max"] * schaal // 10
        op = data["op"] if data and "op" in data else rng.choice("+−")
        strategie = data["strategie"] if data and "strategie" in data else rng.choice(["compenseren", "splitsen"])
        d = {}
        if strategie == "compenseren":
            k = rng.randint(1, max(1, len(str(maximum)) - 2))
            rond = rng.randint(1, 4) * 10 ** k
            verschil = rng.choice([1, 2]) * (1 if rng.random() < 0.7 else 10 ** (k - 1) if k > 1 else 1)
            b = rond - verschil
            if b <= 0:
                b, rond, verschil = 9, 10, 1
            d.update(rond=rond, verschil=verschil)
        else:
            b = rng.randint(max(11, maximum // 50), max(12, maximum // 3))
        if op == "+":
            a = rng.randint(max(1, maximum // 20), max(2, maximum - b))
        else:
            a = rng.randint(b + 1, max(b + 2, maximum))
            if p["negatief"] and rng.random() < 0.35:
                a, b = rng.randint(1, max(2, b - 1)), b  # uitkomst onder nul
        if p["negatief"] and op == "+" and rng.random() < 0.3:
            a = -a
        uitkomst = a + b if op == "+" else a - b
        A_, B_, U = D(a) / schaal, D(b) / schaal, D(uitkomst) / schaal
        d.update(a=str(A_), b=str(B_), op=op, strategie=strategie, schaal=schaal,
                 onderwerp=f"{'plus' if op == '+' else 'min'} {strategie}")
        return Vraag(self.id, f"{self.id}:{d['onderwerp']}:{fmt(A_)}{op}{fmt(B_)}", f"{fmt(A_)} {op} {fmt(B_)} =",
                     U, data=d)

    def kies_onderwerp(self, gewichten, p, rng):
        opties = [(op, s) for op in "+−" for s in ("compenseren", "splitsen")]
        w = [gewichten.get(f"{'plus' if op == '+' else 'min'} {s}", 1.0) for op, s in opties]
        op, s = rng.choices(opties, weights=w, k=1)[0]
        return {"op": op, "strategie": s}

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def uitleg(self, v):
        d = v.data
        a, b, op = D(d["a"]), D(d["b"]), d["op"]
        regels = []
        if d["strategie"] == "compenseren" and "rond" in d:
            rond, verschil = D(d["rond"]) / d["schaal"], D(d["verschil"]) / d["schaal"]
            if op == "+":
                regels += [f"Compenseren: {fmt(b)} is bijna {fmt(rond)}.",
                           f"{fmt(a)} + {fmt(rond)} = {fmt(a + rond)}, en dan {fmt(verschil)} eraf: {fmt(a + b)}."]
            else:
                regels += [f"Compenseren: {fmt(b)} is bijna {fmt(rond)}.",
                           f"{fmt(a)} − {fmt(rond)} = {fmt(a - rond)}, en dan {fmt(verschil)} erbij: {fmt(a - b)}."]
        else:
            delen = _splits(b)
            x, stappen = a, []
            for deel in delen:
                x = x + deel if op == "+" else x - deel
                stappen.append(f"{op} {fmt(deel)} = {fmt(x)}")
            regels += [f"Splitsen: {fmt(b)} = " + " + ".join(fmt(dd) for dd in delen) + ".",
                       f"{fmt(a)} " + ", ".join(stappen) + "."]
        if v.antwoord < 0 or a < 0:
            regels.append("Op de getallenlijn: onder nul tel je verder naar links.")
        return regels

    def tip(self, v):
        if v.data["strategie"] == "compenseren":
            return "Maak er eerst een rond getal van, en verbeter daarna."
        return "Splits het tweede getal in honderdtallen, tientallen en eenheden."

    def diagnose(self, v, getal):
        d = v.data
        if getal is None or getal == v.antwoord:
            return None
        a, b, op, schaal = D(d["a"]), D(d["b"]), d["op"], d["schaal"]
        if "rond" in d:
            verschil = D(d["verschil"]) / schaal
            if abs(getal - v.antwoord) == 2 * verschil:
                wat = "aftrekken" if op == "+" else "erbij tellen"
                return ("compenseren_verkeerd",
                        f"Bij compenseren moest je {fmt(verschil)} {wat}, je deed het omgekeerd.")
        if getal == (a - b if op == "+" else a + b):
            return "verkeerde_bewerking", f"Je rekende {'min' if op == '+' else 'plus'}. Kijk goed naar het teken."
        verschil = abs(getal - v.antwoord)
        for k in (1, 2, 3):
            if verschil == 10 ** k:
                return "onthouden", f"Je zit er precies {10 ** k} naast: kijk naar de {_plaats(0, k)} (onthouden?)."
        return None

    def spiekbrief(self):
        return SPIEKBRIEF


def _splits(b):
    """345 -> [300, 40, 5]; 4,75 -> [4, 0,7, 0,05] (zonder nullen)."""
    b = D(b)
    teken = -1 if b < 0 else 1
    b = abs(b)
    uit = []
    tekst = format(b.normalize(), "f")
    geheel, _, komma = tekst.partition(".")
    for i, c in enumerate(geheel):
        if c != "0":
            uit.append(D(c) * D(10) ** (len(geheel) - i - 1))
    for i, c in enumerate(komma, 1):
        if c != "0":
            uit.append(D(c) * D(10) ** -i)
    return [teken * x for x in uit] or [D(0)]


# ---- × en : met 10, 100, 1000 -------------------------------------------------------------

class MaalDeel10(Onderwerp):
    id = "wiskunde.hoofdrekenen.maaldeel10"
    naam = "× en : met 10, 100, 1000"
    omschrijving = "vermenigvuldigen en delen met 10, 100, 1000 (de komma verschuift)"
    denkfouten = {"verkeerde_richting_10": "de komma de verkeerde kant op geschoven",
                  "plaatsen_10": "de komma te ver of te weinig geschoven"}
    vast = ("op", "m")

    def maak_met(self, p, rng, data=None):
        machten = [D(m) for m in p["machten"]]
        for _ in range(200):
            m = D(data["m"]) if data and "m" in data else rng.choice(machten)
            op = data["op"] if data and "op" in data else rng.choice("×:")
            n = rng.randint(1, 3)
            getal = D(rng.randint(10 ** (n - 1), 10 ** n - 1)).scaleb(-rng.randint(0, p["decimalen"]))
            if getal >= p["max"]:
                continue
            uit = getal * m if op == "×" else getal / m
            if decimalen(uit) > max(p["decimalen"], 0) + (3 if p["decimalen"] else 0):
                continue
            if not p["decimalen"] and uit != uit.to_integral_value():
                continue
            d = {"getal": str(getal), "m": str(m), "op": op, "onderwerp": f"{op} {fmt(m)}"}
            return Vraag(self.id, f"{self.id}:{op}{fmt(m)}:{fmt(getal)}", f"{fmt(getal)} {op} {fmt(m)} =",
                         uit.normalize(), data=d)
        return Vraag(self.id, f"{self.id}:×10:3", "3 × 10 =", D(30), data={"getal": "3", "m": "10", "op": "×",
                                                                          "onderwerp": "× 10"})

    def onderwerp_van_sleutel(self, sleutel):
        # sleutel = id:<op><m>:<getal>, en op kan zelf ':' zijn (id::10:3)
        if not sleutel.startswith(self.id + ":"):
            return None
        rest = sleutel[len(self.id) + 1:]
        if len(rest) < 2:
            return None
        return f"{rest[0]} {rest[1:].split(':')[0]}"

    def _stappen(self, m):
        m = D(m)
        if m >= 1:
            return len(str(int(m))) - 1, True
        return -m.normalize().as_tuple().exponent, False

    def uitleg(self, v):
        d = v.data
        m, op = D(d["m"]), d["op"]
        n, groot = self._stappen(m)
        rechts = (op == "×") == groot
        pl = "plaats" if n == 1 else "plaatsen"
        regels = []
        if not groot:
            regels.append(f"{op} {fmt(m)} is hetzelfde als {'×' if op == ':' else ':'} {10 ** n}.")
        regels.append(f"{op} {fmt(m)}: de komma schuift {n} {pl} naar {'rechts' if rechts else 'links'} "
                      f"(vul aan met nullen als het moet).")
        regels.append(f"{fmt(D(d['getal']))} {op} {fmt(m)} = {fmt(v.antwoord)}")
        return regels

    def tip(self, v):
        return "Hoeveel nullen heeft het getal waarmee je vermenigvuldigt of deelt? Zoveel plaatsen schuift de komma."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        g, m = D(d["getal"]), D(d["m"])
        omgekeerd = g / m if d["op"] == "×" else g * m
        if getal == omgekeerd:
            return "verkeerde_richting_10", "Je schoof de komma de verkeerde kant op."
        for k in range(1, 5):
            if getal in (v.antwoord.scaleb(k), v.antwoord.scaleb(-k)):
                return "plaatsen_10", f"De komma staat {k} {'plaats' if k == 1 else 'plaatsen'} verkeerd. Tel de nullen."
        return None

    def spiekbrief(self):
        return SPIEKBRIEF


# ---- verdubbelen en halveren ------------------------------------------------------------------

class DubbelHelft(Onderwerp):
    id = "wiskunde.hoofdrekenen.dubbelhelft"
    naam = "Verdubbelen en halveren"
    omschrijving = "het dubbel en de helft uit het hoofd"
    denkfouten = {"helft_dubbel": "het dubbel en de helft verwisseld", "dubbel_onthouden": "een tiental vergeten"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else rng.choice(["dubbel", "helft"])
        schaal = 10 ** p["decimalen"]
        n = rng.randint(max(11, p["max"] // 20), p["max"]) * (1 if not p["decimalen"] else 1)
        getal = D(n) / schaal if p["decimalen"] and rng.random() < 0.5 else D(n)
        if soort == "helft" and not p["decimalen"] and getal % 2:
            getal += 1
        uit = getal * 2 if soort == "dubbel" else getal / 2
        d = {"getal": str(getal), "soort": soort, "onderwerp": soort}
        tekst = f"Het dubbel van {fmt(getal)} =" if soort == "dubbel" else f"De helft van {fmt(getal)} ="
        return Vraag(self.id, f"{self.id}:{soort}:{fmt(getal)}", tekst, uit.normalize(), data=d)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def uitleg(self, v):
        g = D(v.data["getal"])
        if v.data["soort"] == "dubbel":
            delen = _splits(g)
            return ["Splits en verdubbel elk deel: " + ", ".join(f"dubbel van {fmt(x)} = {fmt(2 * x)}" for x in delen)
                    + ".", f"Samen: {fmt(2 * g)}."]
        geheel = int(g)
        tientallen = geheel // 10 * 10
        if (tientallen // 10) % 2 and tientallen:
            tientallen -= 10
        rest = g - tientallen
        return [f"Splits {fmt(g)} in {fmt(D(tientallen))} en {fmt(rest)} (twee getallen die je makkelijk halveert).",
                f"De helft van {fmt(D(tientallen))} = {fmt(D(tientallen) / 2)}, de helft van {fmt(rest)} = "
                f"{fmt(rest / 2)}. Samen: {fmt(g / 2)}."]

    def tip(self, v):
        return "Splits het getal in stukken die je makkelijk verdubbelt of halveert."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        g = D(v.data["getal"])
        if getal == (g / 2 if v.data["soort"] == "dubbel" else g * 2):
            return "helft_dubbel", "Je nam de helft in plaats van het dubbel (of omgekeerd)."
        if abs(getal - v.antwoord) in (10, 100):
            return "dubbel_onthouden", "Je zit er precies 10 of 100 naast: vergat je iets te onthouden?"
        return None

    def spiekbrief(self):
        return SPIEKBRIEF


# ---- slim × en : (splitsen) ----------------------------------------------------------------

class Splitsen(Onderwerp):
    """91 : 7 = 70 : 7 + 21 : 7 = 10 + 3 = 13. Het klad is verplicht: het gaat om de aanpak, niet alleen de uitkomst."""
    id = "wiskunde.hoofdrekenen.splitsen"
    naam = "Slim × en : (splitsen)"
    omschrijving = "× en : met splitsen in handige stukken, en compenseren (99 × 6)"
    denkfouten = {"split_deel_vergeten": "bij splitsen een stuk vergeten",
                  "split_niet_gedeeld": "bij splitsen een stuk niet gedeeld of vermenigvuldigd",
                  "compenseren_richting": "bij compenseren de verkeerde kant op verbeterd",
                  "compenseren_te_weinig": "bij compenseren maar 1 keer verbeterd in plaats van × het getal"}
    klad = "verplicht"
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and data.get("soort") in p["soorten"] else rng.choice(p["soorten"])
        if soort == "deel_splitsen":
            for _ in range(50):
                d = rng.randint(3, p["deler_max"])
                q_max = min(99, p["deeltal_max"] // d)
                if q_max >= 11:
                    break
            q = rng.choice([x for x in range(11, q_max + 1) if x % 10]) if q_max >= 11 else 13
            a, f, op, antwoord = D(d * q), D(d), ":", D(q)
            delen = [D(d * (q // 10) * 10), D(d * (q % 10))]  # een tafel met een 0, en de rest
        elif soort == "maal_compenseren":
            n = rng.choice(p["compenseer"])
            f = D(rng.randint(3, 9))
            a, op, antwoord = D(n), "×", D(n) * f
            delen = [D(n + 1), D(1)]  # 99 = 100 − 1
        else:
            soort = "maal_splitsen"
            f = D(rng.randint(3, 9))
            if p["komma"] and rng.random() < 0.4:
                a = D(rng.choice([x for x in range(11, 100) if x % 10])) / 10   # 2,4
            else:
                a = D(rng.choice([x for x in range(11, max(12, p["groot"]) + 1) if x % 10]))
            op, antwoord = "×", a * f
            delen = _splits(a)
        d_ = {"soort": soort, "a": str(a), "f": str(f), "op": op, "delen": [str(x) for x in delen], "onderwerp": soort}
        return Vraag(self.id, f"{self.id}:{soort}:{fmt(a)}{op}{fmt(f)}", f"{fmt(a)} {op} {fmt(f)} =", antwoord,
                     data=d_)

    def kies_onderwerp(self, gewichten, p, rng):
        w = [gewichten.get(s, 1.0) for s in p["soorten"]]
        return {"soort": rng.choices(p["soorten"], weights=w, k=1)[0]}

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    @staticmethod
    def _getallen(v):
        d = v.data
        return d["soort"], D(d["a"]), D(d["f"]), [D(x) for x in d["delen"]]

    def oplossing(self, v):
        soort, a, f, delen = self._getallen(v)
        if soort == "deel_splitsen":
            q = [x / f for x in delen]
            reken = (f"{fmt(a)} : {fmt(f)} = {fmt(delen[0])} : {fmt(f)} + {fmt(delen[1])} : {fmt(f)} = "
                     f"{fmt(q[0])} + {fmt(q[1])} = {fmt(sum(q))}")
            waarom = (f"{fmt(delen[0])} : {fmt(f)} = {fmt(q[0])}, want {fmt(f)} × {fmt(q[0])} = {fmt(delen[0])}. "
                      f"En {fmt(delen[1])} : {fmt(f)} = {fmt(q[1])}.")
            paden = [fout_pad("split_niet_gedeeld", f"Je deelde {fmt(delen[1])} niet door {fmt(f)}.",
                              f"{fmt(delen[0])} : {fmt(f)} + {fmt(delen[1])} = {fmt(q[0] + delen[1])}")]
        elif soort == "maal_compenseren":
            rond, c = delen
            reken = (f"{fmt(a)} × {fmt(f)} = {fmt(rond)} × {fmt(f)} − {fmt(c)} × {fmt(f)} = "
                     f"{fmt(rond * f)} − {fmt(c * f)} = {fmt(a * f)}")
            waarom = f"{fmt(a)} is {fmt(c)} minder dan {fmt(rond)}: reken {fmt(rond)} × {fmt(f)}, en neem er {fmt(c)} × {fmt(f)} af."
            paden = [fout_pad("compenseren_richting", "Je telde erbij, maar je moet er iets af: het getal was kleiner dan "
                              f"{fmt(rond)}.", f"{fmt(rond)} × {fmt(f)} + {fmt(c * f)} = {fmt(rond * f + c * f)}")]
        else:
            delen_x = [x * f for x in delen]
            reken = (f"{fmt(a)} × {fmt(f)} = " + " + ".join(f"{fmt(x)} × {fmt(f)}" for x in delen) + " = "
                     + " + ".join(fmt(x) for x in delen_x) + f" = {fmt(a * f)}")
            waarom = "Elk stuk × " + fmt(f) + ": " + ", ".join(f"{fmt(x)} × {fmt(f)} = {fmt(x * f)}" for x in delen) + "."
            paden = [fout_pad("split_niet_gedeeld", f"Je vermenigvuldigde {fmt(delen[-1])} niet met {fmt(f)}.",
                              f"{fmt(delen_x[0])} + {fmt(delen[-1])} = {fmt(delen_x[0] + delen[-1])}")] if len(delen) == 2 else []
        return Oplossing([stap(reken, hint=self.tip(v), waarom=waarom)], paden)

    def tip(self, v):
        soort, a, f, delen = self._getallen(v)
        if soort == "deel_splitsen":
            return f"Splits {fmt(a)} in een getal uit de tafel van {fmt(f)} met een 0 erachter, en de rest. Deel dan elk stuk door {fmt(f)}."
        if soort == "maal_compenseren":
            return f"{fmt(a)} is bijna {fmt(delen[0])}. Reken eerst {fmt(delen[0])} × {fmt(f)}, en verbeter dan."
        if a != a.to_integral_value():
            return f"Splits {fmt(a)} in een heel getal en de rest achter de komma, en vermenigvuldig elk stuk met {fmt(f)}."
        return (f"Splits {fmt(a)} in {'honderdtallen, ' if a >= 100 else ''}tientallen en eenheden, en vermenigvuldig "
                f"elk stuk met {fmt(f)}.")

    def uitleg(self, v):
        opl = self.oplossing(v)
        return [opl.stappen[0].reken, opl.stappen[0].waarom]

    def klad_klaar(self, v, regels):
        """Is er een splitsing (of compensatie) te zien? Elke splitsing telt (49 + 42 net zo goed als 70 + 21); een
        rekenfout erin mag: dan kijkt het nakijken (met een tweede kans) het antwoord gewoon na."""
        soort, a, f, delen = self._getallen(v)
        op = DEEL if soort == "deel_splitsen" else MAAL
        F, stukken = Fraction(f), 0
        for r in regels:
            if not r or not r.leesbaar:
                continue
            for s in r.schakels:
                if F not in s.operanden:
                    continue
                if s.ops.count(op) >= 2:
                    return True, ""
                if soort == "maal_compenseren" and op in s.ops and (MIN in s.ops or PLUS in s.ops):
                    return True, ""
                if s.ops == [op] and Fraction(a) not in s.operanden:
                    stukken += 1
        if stukken >= (1 if soort == "maal_compenseren" else 2):
            return True, ""
        if soort == "maal_compenseren":
            return False, f"Laat in je klad zien hoe je compenseert: begin met {fmt(delen[0])} × {fmt(f)}."
        return False, f"Laat in je klad zien hoe je splitst: in welke stukken verdeel je {fmt(a)}? (Tab = klad)"

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        soort, a, f, delen = self._getallen(v)
        if soort == "deel_splitsen":
            q = [x / f for x in delen]
            if getal in q:
                return ("split_deel_vergeten", f"Je deelde maar één stuk. {fmt(delen[0])} : {fmt(f)} en "
                                               f"{fmt(delen[1])} : {fmt(f)}: tel ze allebei op.")
            if getal in (q[0] + delen[1], q[1] + delen[0]):
                return "split_niet_gedeeld", f"Je deelde niet elk stuk door {fmt(f)}."
        elif soort == "maal_compenseren":
            rond, c = delen
            if getal == rond * f + c * f:
                return "compenseren_richting", f"{fmt(a)} is kleiner dan {fmt(rond)}: je moet er iets af doen, niet bij."
            if getal == rond * f - c:
                return ("compenseren_te_weinig", f"Je nam er maar {fmt(c)} af, maar je rekende {fmt(f)} keer te veel: "
                                                 f"neem er {fmt(c)} × {fmt(f)} af.")
        else:
            x = [d * f for d in delen]
            if len(delen) >= 2 and getal in (x[0], sum(x[:-1])):
                return "split_deel_vergeten", "Je vergat een stuk: vermenigvuldig elk stuk en tel ze allemaal op."
            if len(delen) >= 2 and getal == sum(x[:-1]) + delen[-1]:
                return "split_niet_gedeeld", f"Je vermenigvuldigde {fmt(delen[-1])} niet met {fmt(f)}."
        return None

    def spiekbrief(self):
        return SPIEKBRIEF


SPIEKBRIEF = [
    ("Slimme trucjes voor hoofdrekenen", "accent"),
    ("", ""),
    ("COMPENSEREN  (een getal dat bijna rond is)", "accent"),
    ("  47 + 99  = 47 + 100 − 1  = 146", ""),
    ("  523 − 198 = 523 − 200 + 2 = 325", ""),
    ("", ""),
    ("SPLITSEN", "accent"),
    ("  347 + 285 = 347 + 200 + 80 + 5 = 632", ""),
    ("  14 × 7 = 10 × 7 + 4 × 7 = 70 + 28 = 98", ""),
    ("  91 : 7 = 70 : 7 + 21 : 7 = 10 + 3 = 13   (70: de tafel van 7 met een 0)", ""),
    ("  99 × 6 = 100 × 6 − 1 × 6 = 600 − 6 = 594   (compenseren)", ""),
    ("", ""),
    ("TAFELS", "accent"),
    ("  × 9  = × 10 en dan één keer eraf:  9 × 7 = 70 − 7 = 63", ""),
    ("  × 5  = de helft van × 10:          5 × 8 = 80 : 2 = 40", ""),
    ("  × 4  = twee keer verdubbelen:       4 × 6 → 12 → 24", ""),
    ("  7 × 80 = 7 × 8 = 56, en dan × 10 = 560", ""),
    ("  Delen = omgekeerd vermenigvuldigen: 56 : 7 = ? → 7 × 8 = 56, dus 8", ""),
    ("", ""),
    ("× EN : MET 10, 100, 1000", "accent"),
    ("  × 10 : de komma 1 plaats naar rechts   3,5 × 10 = 35", ""),
    ("  : 100: de komma 2 plaatsen naar links  35 : 100 = 0,35", ""),
    ("  × 0,1 is hetzelfde als : 10", "dim"),
    ("", ""),
    ("VERDUBBELEN EN HALVEREN", "accent"),
    ("  dubbel van 37 = dubbel van 30 + dubbel van 7 = 60 + 14 = 74", ""),
    ("  helft van 74 = helft van 60 + helft van 14 = 30 + 7 = 37", ""),
    ("", ""),
    ("NEGATIEVE GETALLEN", "accent"),
    ("  −3 + 5 = 2   (op de getallenlijn 5 naar rechts)", ""),
    ("  plus maal min = min, min maal min = plus", "dim"),
]

TAFELS = Tafels()
PLUSMIN = PlusMin()
MAALDEEL10 = MaalDeel10()
DUBBELHELFT = DubbelHelft()
SPLITSEN = Splitsen()
ALLE = [TAFELS, PLUSMIN, MAALDEEL10, DUBBELHELFT, SPLITSEN]
