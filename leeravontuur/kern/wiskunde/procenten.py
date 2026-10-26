"""Procenten: het honderdveld (aflezen en kleuren), procent ↔ breuk ↔ kommagetal, procent van een getal
(met de procentstrook) en korting, btw en procentuele verandering.
"""

import math
from decimal import Decimal
from fractions import Fraction

from ..getal import GetypteBreuk, fmt, lees_getal
from ..klad import oplossing_van
from ..modellen import Honderdveld, Procentstrook
from ..onderwerp import Onderwerp, Vraag

D = Decimal
F = Fraction


def geld(x):
    """Een bedrag: 24 → '24', 24,2 → '24,20'."""
    x = D(x)
    return fmt(x) if x == x.to_integral_value() else f"{x.quantize(D('0.01')):f}".replace(".", ",")


SPIEKBRIEF = [
    ("PROCENT = PER HONDERD", "accent"),
    ("  35 % = 35 van de 100 = 35/100 = 0,35", ""),
    ("", ""),
    ("HANDIG OM TE KENNEN", "accent"),
    ("  100 % = alles      50 % = 1/2      25 % = 1/4      75 % = 3/4", ""),
    ("  20 % = 1/5         10 % = 1/10     5 % = 1/20      1 % = 1/100", ""),
    ("", ""),
    ("PROCENT VAN EEN GETAL", "accent"),
    ("  20 % van 80: 10 % = 80 : 10 = 8, dus 20 % = 2 × 8 = 16.", ""),
    ("  25 % van 80: 1/4 van 80 = 80 : 4 = 20.", ""),
    ("  Hoeveel % is 12 van 48? 12/48 = 1/4 = 25 %.", ""),
    ("", ""),
    ("KORTING EN BTW", "accent"),
    ("  Korting: nieuwe prijs = prijs − het procent van de prijs.", ""),
    ("  € 240 met 25 % korting: 25 % van 240 = 60, je betaalt 240 − 60 = € 180.", ""),
    ("  Btw: prijs met btw = prijs + het procent van de prijs (6 % of 21 %).", ""),
]

STRATEGIE = {50: "50 % is de helft", 25: "25 % is een vierde (: 4)", 10: "10 % is een tiende (: 10)",
             20: "20 % is een vijfde (: 5)", 75: "75 % is drie vierden", 1: "1 % is een honderdste (: 100)",
             100: "100 % is alles"}


def deel_regels(p, totaal):
    """p % van totaal als klad-regels, met dezelfde handige strategie als deel_uitleg."""
    deel, t = D(totaal) * D(p) / 100, D(totaal)
    if p == 50:
        return [f"{fmt(t)} : 2 = {fmt(deel)}"]
    if p == 25:
        return [f"{fmt(t)} : 4 = {fmt(deel)}"]
    if p == 75:
        return [f"{fmt(t)} : 4 = {fmt(t / 4)}", f"3 × {fmt(t / 4)} = {fmt(deel)}"]
    if p == 10:
        return [f"{fmt(t)} : 10 = {fmt(deel)}"]
    if p == 1:
        return [f"{fmt(t)} : 100 = {fmt(deel)}"]
    if p == 5:
        return [f"{fmt(t)} : 10 = {fmt(t / 10)}", f"{fmt(t / 10)} : 2 = {fmt(deel)}"]
    if p % 10 == 0:
        return [f"{fmt(t)} : 10 = {fmt(t / 10)}", f"{p // 10} × {fmt(t / 10)} = {fmt(deel)}"]
    return [f"{fmt(t)} : 100 = {fmt(t / 100)}", f"{p} × {fmt(t / 100)} = {fmt(deel)}"]


def deel_uitleg(p, totaal):
    """Hoe je p % van totaal uitrekent, met een handige strategie."""
    deel = D(totaal) * D(p) / 100
    t = fmt(D(totaal))
    if p == 50:
        return f"50 % is de helft: {t} : 2 = {fmt(deel)}."
    if p == 25:
        return f"25 % is een vierde: {t} : 4 = {fmt(deel)}."
    if p == 75:
        return f"25 % = {t} : 4 = {fmt(D(totaal) / 4)}, dus 75 % = 3 × {fmt(D(totaal) / 4)} = {fmt(deel)}."
    if p == 10:
        return f"10 % is een tiende: {t} : 10 = {fmt(deel)}."
    if p == 1:
        return f"1 % is een honderdste: {t} : 100 = {fmt(deel)}."
    if p == 5:
        return f"10 % = {fmt(D(totaal) / 10)}, dus 5 % is de helft daarvan: {fmt(deel)}."
    if p % 10 == 0:
        return f"10 % = {t} : 10 = {fmt(D(totaal) / 10)}, dus {p} % = {p // 10} × {fmt(D(totaal) / 10)} = {fmt(deel)}."
    return f"1 % = {t} : 100 = {fmt(D(totaal) / 100)}, dus {p} % = {p} × {fmt(D(totaal) / 100)} = {fmt(deel)}."


class _Procenten(Onderwerp):
    vast = ("soort",)

    def spiekbrief(self):
        return SPIEKBRIEF

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def soort(self, p, rng, data):
        return data["soort"] if data and "soort" in data else rng.choice(p["soorten"])

    def lees(self, tekst):
        return lees_getal((tekst or "").replace("%", "").replace("€", ""))


# ---- het honderdveld -------------------------------------------------------------------------------------

class Veld(_Procenten):
    id = "wiskunde.procenten.honderdveld"
    naam = "Het honderdveld"
    omschrijving = "procent = per honderd: aflezen en kleuren"
    denkfouten = {"wit_geteld": "de witte vakjes geteld in plaats van de gekleurde",
                  "kommagetal_ipv_procent": "een kommagetal gegeven in plaats van een percentage"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        d = {"soort": soort, "onderwerp": soort}
        if soort == "kleuren_breuk":
            t, n = rng.choice([(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5), (1, 10), (3, 10), (7, 10),
                               (1, 20), (3, 20), (1, 25), (1, 50)])
            pct = 100 * t // n
            d.update(t=t, n=n, pct=pct)
            return Vraag(self.id, f"{self.id}:kleuren_breuk:{t}/{n}", f"Kleur {t}/{n} van het honderdveld.", D(pct),
                         data=d, invoer="veld", model=Honderdveld(), verwacht_tekst=f"{pct} vakjes ({pct} %)")
        pct = rng.randint(1, 19) * 5 if p["vijfvouden"] else rng.randint(3, 97)
        d["pct"] = pct
        if soort == "kleuren":
            return Vraag(self.id, f"{self.id}:kleuren:{pct}", f"Kleur {pct} % van het honderdveld.", D(pct), data=d,
                         invoer="veld", model=Honderdveld(), verwacht_tekst=f"{pct} vakjes")
        return Vraag(self.id, f"{self.id}:aflezen:{pct}", "Welk percentage is gekleurd?", D(pct), eenheid="%",
                     data=d, model=Honderdveld(set(range(pct))), verwacht_tekst=f"{pct} %")

    def uitleg(self, v):
        d = v.data
        pct = d["pct"]
        rijen, rest = divmod(pct, 10)
        regels = []
        if d["soort"] == "kleuren_breuk":
            regels.append(f"{d['t']}/{d['n']} = {pct}/100 (teller en noemer × {100 // d['n']}) = {pct} %.")
        regels.append(f"{pct} % = {pct} van de 100 vakjes = {rijen} volle rij{'en' if rijen != 1 else ''} "
                      f"(× 10)" + (f" en nog {rest} vakje{'s' if rest != 1 else ''}." if rest else "."))
        return regels

    def tip(self, v):
        return "Het veld heeft 100 vakjes. Eén rij is 10 vakjes = 10 %."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        pct = v.data["pct"]
        if getal == 100 - pct:
            return "wit_geteld", "Je telde de witte vakjes. Gevraagd zijn de gekleurde."
        if getal == D(pct) / 100:
            return "kommagetal_ipv_procent", f"{fmt(D(pct) / 100)} is juist als kommagetal, maar in procent is het {pct} %."
        return None


# ---- procent, breuk en kommagetal -----------------------------------------------------------------------------

NETTE_BREUKEN = [(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5), (1, 10), (3, 10), (7, 10), (9, 10),
                 (1, 20), (3, 20), (1, 25), (1, 50), (1, 100)]


class Omzetten(_Procenten):
    id = "wiskunde.procenten.omzetten"
    naam = "Procent, breuk en kommagetal"
    omschrijving = "25 % = 1/4 = 0,25"
    denkfouten = {"komma_procent": "kommagetal en procent: de komma 2 plaatsen verkeerd",
                  "niet_vereenvoudigd": "niet volledig vereenvoudigd"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        t, n = rng.choice(NETTE_BREUKEN)
        pct = D(100 * t) / n
        d = {"soort": soort, "t": t, "n": n, "pct": str(pct), "onderwerp": soort}
        if soort == "procent_naar_breuk":
            return Vraag(self.id, f"{self.id}:{soort}:{fmt(pct)}", f"{fmt(pct)} % = ?  (als breuk, zo eenvoudig "
                         "mogelijk)", F(t, n), data={**d, "vereenvoudigd": True}, invoer="breuk")
        if soort == "breuk_naar_procent":
            return Vraag(self.id, f"{self.id}:{soort}:{t}/{n}", f"{t}/{n} = ?", pct, eenheid="%", data=d)
        komma = pct / 100
        if soort == "komma_naar_procent":
            return Vraag(self.id, f"{self.id}:{soort}:{fmt(komma)}", f"{fmt(komma)} = ?", pct, eenheid="%", data=d)
        return Vraag(self.id, f"{self.id}:{soort}:{fmt(pct)}", f"{fmt(pct)} % = ?  (als kommagetal)", komma, data=d)

    def uitleg(self, v):
        d = v.data
        t, n, pct = d["t"], d["n"], D(d["pct"])
        honderdsten = f"{fmt(pct)}/100"
        s = d["soort"]
        if s == "procent_naar_breuk":
            return [f"{fmt(pct)} % = {honderdsten}.", f"Vereenvoudig: {honderdsten} = {t}/{n}."]
        if s == "breuk_naar_procent" and n == 100:
            return [f"{t}/100 = {t} honderdsten = {t} %."]
        if s == "breuk_naar_procent":
            return [f"Maak de noemer 100: {t}/{n} = {t}×{100 // n} / {n}×{100 // n} = {honderdsten} = {fmt(pct)} %."]
        if s == "komma_naar_procent":
            return [f"{fmt(pct / 100)} = {fmt(pct)} honderdsten = {fmt(pct)} %.", "Kommagetal → procent: × 100."]
        return [f"{fmt(pct)} % = {fmt(pct)} honderdsten = {fmt(pct / 100)}.", "Procent → kommagetal: : 100."]

    def tip(self, v):
        return "Procent betekent 'per honderd': 35 % = 35/100 = 0,35."

    def diagnose(self, v, getal):
        if isinstance(getal, GetypteBreuk):
            if getal.waarde == v.antwoord and not getal.eenvoudigst:
                return "niet_vereenvoudigd", f"{getal} is juist, maar kan nog eenvoudiger."
            return None
        if getal is None or getal == v.antwoord:
            return None
        if getal in (v.antwoord * 100, v.antwoord / 100, v.antwoord * 10, v.antwoord / 10):
            return "komma_procent", "Let op de komma: 0,4 = 40 honderdsten = 40 %. Procent is altijd per 100."
        return None


# ---- procent van een getal ----------------------------------------------------------------------------------

class ProcentVan(_Procenten):
    id = "wiskunde.procenten.van"
    naam = "Procent van een getal"
    omschrijving = "20 % van 80, en hoeveel % is 12 van 48?"
    denkfouten = {"procent_als_antwoord": "het percentage zelf als antwoord gegeven",
                  "gedeeld_door_procent": "door het percentage gedeeld",
                  "rest_berekend": "het andere deel berekend (100 % − …)"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        pct = rng.choice(p["procenten"])
        # een totaal waarbij het deel een mooi getal is
        stap = 100 // math.gcd(pct, 100)
        totaal = stap * rng.randint(1, max(1, p["max"] // stap))
        while totaal < 10:
            totaal += stap
        deel = D(totaal) * pct / 100
        d = {"soort": soort, "pct": pct, "totaal": totaal, "onderwerp": soort}
        if soort == "welk_procent":
            return Vraag(self.id, f"{self.id}:welk_procent:{fmt(deel)}/{totaal}",
                         f"Hoeveel procent is {fmt(deel)} van {totaal}?", D(pct), eenheid="%", data=d,
                         model_na=Procentstrook(D(totaal), D(pct), toon_deel=True))
        return Vraag(self.id, f"{self.id}:van:{pct}:{totaal}", f"{pct} % van {totaal} =", deel, data=d,
                     model=Procentstrook(D(totaal), D(pct)), model_na=Procentstrook(D(totaal), D(pct), toon_deel=True))

    def uitleg(self, v):
        pct, totaal = v.data["pct"], v.data["totaal"]
        if v.data["soort"] == "welk_procent":
            deel = D(totaal) * pct / 100
            f = F(deel) / totaal
            return [f"Maak er een breuk van: {fmt(deel)}/{totaal} = {f.numerator}/{f.denominator}.",
                    f"{f.numerator}/{f.denominator} = {pct}/100 = {pct} %."]
        return [deel_uitleg(pct, totaal)]

    klad = "ja"

    def oplossing(self, v):
        pct, totaal = v.data["pct"], v.data["totaal"]
        if v.data["soort"] == "welk_procent":
            deel = D(totaal) * pct / 100
            return oplossing_van(f"{fmt(deel)} : {totaal} = {fmt(D(pct) / 100)}", f"{fmt(D(pct) / 100)} × 100 = {pct}")
        return oplossing_van(*deel_regels(pct, totaal))

    def tip(self, v):
        if v.data["soort"] == "welk_procent":
            return "Schrijf het als breuk (deel/geheel) en maak de noemer 100."
        return "Begin bij 10 % (: 10) of 1 % (: 100), of gebruik 50 % = de helft en 25 % = een vierde."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        pct, totaal = v.data["pct"], v.data["totaal"]
        if v.data["soort"] == "welk_procent":
            return None
        if getal == pct:
            return "procent_als_antwoord", f"{pct} is het percentage. Gevraagd is hoeveel {pct} % van {totaal} is."
        if pct and getal == D(totaal) / pct:
            return "gedeeld_door_procent", f"Deel niet door {pct}: deel door 100 (dat is 1 %) en neem dan × {pct}."
        if getal == totaal - v.antwoord:
            return "rest_berekend", f"Dat is {100 - pct} %, het andere deel."
        return None


# ---- korting, btw en procentuele verandering --------------------------------------------------------------------

DINGEN = ["een fiets", "een jas", "een spelcomputer", "een paar schoenen", "een tent", "een skateboard",
          "een gitaar", "een step", "een rugzak", "een voetbal"]


class Korting(_Procenten):
    id = "wiskunde.procenten.korting"
    naam = "Korting en btw"
    omschrijving = "wat betaal je met korting of met btw?"
    denkfouten = {"alleen_korting": "alleen de korting berekend (niet afgetrokken van de prijs)",
                  "korting_opgeteld": "de korting bij de prijs opgeteld",
                  "btw_vergeten": "de btw niet bij de prijs geteld",
                  "verkeerd_grondgetal": "het procent berekend van het verkeerde bedrag"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        ding = rng.choice(DINGEN)
        d = {"soort": soort, "ding": ding, "onderwerp": soort}
        if soort == "korting":
            pct = rng.choice([10, 20, 25, 30, 40, 50])
            stap = 100 // math.gcd(pct, 100)
            prijs = stap * rng.randint(max(1, 20 // stap), 400 // stap)
            nieuw = D(prijs) * (100 - pct) / 100
            d.update(pct=pct, prijs=prijs)
            return Vraag(self.id, f"{self.id}:korting:{pct}:{prijs}",
                         f"{ding.capitalize()} kost € {prijs}. Je krijgt {pct} % korting. Wat betaal je?", nieuw,
                         eenheid="euro", data=d, model_na=Procentstrook(D(prijs), D(pct), "euro", toon_deel=True),
                         verwacht_tekst=f"{geld(nieuw)} euro")
        if soort == "btw":
            pct = rng.choice([6, 21])
            prijs = rng.choice([10, 20, 50, 100]) * rng.randint(1, 5) if pct == 21 else 50 * rng.randint(1, 8)
            nieuw = D(prijs) * (100 + pct) / 100
            d.update(pct=pct, prijs=prijs)
            return Vraag(self.id, f"{self.id}:btw:{pct}:{prijs}",
                         f"{ding.capitalize()} kost € {prijs} zonder btw. Er komt {pct} % btw bij. Prijs met btw?",
                         nieuw, eenheid="euro", data=d, verwacht_tekst=f"{geld(nieuw)} euro")
        # procentuele verandering (stijging of daling)
        pct = rng.choice([10, 20, 25, 50])
        oud = (100 // math.gcd(pct, 100)) * rng.randint(1, 20)
        nieuw = D(oud) * (100 + pct if soort == "stijging" else 100 - pct) / 100
        d.update(pct=pct, oud=oud, nieuw=str(nieuw))
        woord = "duurder" if soort == "stijging" else "goedkoper"
        return Vraag(self.id, f"{self.id}:{soort}:{oud}:{fmt(nieuw)}",
                     f"De prijs gaat van € {oud} naar € {geld(nieuw)}. Hoeveel procent {woord}?", D(pct), eenheid="%",
                     data=d)

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "korting":
            korting = D(d["prijs"]) * d["pct"] / 100
            return [deel_uitleg(d["pct"], d["prijs"]).replace(f"= {fmt(korting)}.", f"= € {geld(korting)} korting."),
                    f"Je betaalt € {d['prijs']} − € {geld(korting)} = € {geld(v.antwoord)}."]
        if s == "btw":
            btw = D(d["prijs"]) * d["pct"] / 100
            return [deel_uitleg(d["pct"], d["prijs"]).replace(f"= {fmt(btw)}.", f"= € {geld(btw)} btw."),
                    f"Met btw: € {d['prijs']} + € {geld(btw)} = € {geld(v.antwoord)}."]
        verschil = abs(D(d["nieuw"]) - d["oud"])
        return [f"Het verschil is € {geld(verschil)}. Vergelijk met de oude prijs: {geld(verschil)}/{d['oud']}.",
                f"{geld(verschil)}/{d['oud']} = {d['pct']}/100 = {d['pct']} %."]

    klad = "ja"

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s in ("korting", "btw"):
            deel = D(d["prijs"]) * d["pct"] / 100
            return oplossing_van(*deel_regels(d["pct"], d["prijs"]),
                                 f"{d['prijs']} {'−' if s == 'korting' else '+'} {fmt(deel)} = {fmt(v.antwoord)}")
        nieuw, oud = D(d["nieuw"]), D(d["oud"])
        verschil = abs(nieuw - oud)
        return oplossing_van(f"{fmt(max(nieuw, oud))} − {fmt(min(nieuw, oud))} = {fmt(verschil)}",
                             f"{fmt(verschil)} : {fmt(oud)} = {fmt(D(d['pct']) / 100)}",
                             f"{fmt(D(d['pct']) / 100)} × 100 = {d['pct']}")

    def tip(self, v):
        s = v.data["soort"]
        if s == "korting":
            return "Reken eerst uit hoeveel de korting is. Trek dat dan af van de prijs."
        if s == "btw":
            return "Reken eerst uit hoeveel de btw is. Tel dat dan bij de prijs."
        return "Hoeveel is het verschil? Hoeveel procent is dat van de OUDE prijs?"

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        s = d["soort"]
        if s in ("korting", "btw"):
            deel = D(d["prijs"]) * d["pct"] / 100
            if getal == deel:
                return ("alleen_korting" if s == "korting" else "btw_vergeten",
                        f"€ {geld(deel)} is de {'korting' if s == 'korting' else 'btw'} zelf. "
                        f"{'Trek ze af van' if s == 'korting' else 'Tel ze bij'} de prijs.")
            if s == "korting" and getal == d["prijs"] + deel:
                return "korting_opgeteld", "Korting maakt het goedkoper: aftrekken, niet optellen."
            if s == "btw" and getal == d["prijs"]:
                return "btw_vergeten", "Je vergat de btw bij de prijs te tellen."
            return None
        verschil = abs(D(d["nieuw"]) - d["oud"])
        if getal == (verschil / D(d["nieuw"]) * 100).quantize(D(1)):
            return "verkeerd_grondgetal", "Vergelijk het verschil met de OUDE prijs, niet met de nieuwe."
        return None


VELD = Veld()
OMZETTEN = Omzetten()
PROCENT_VAN = ProcentVan()
KORTING = Korting()
ALLE = [VELD, OMZETTEN, PROCENT_VAN, KORTING]
