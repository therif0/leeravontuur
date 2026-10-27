"""Tijd, geld en snelheid: grootheden die niet (alleen) met de eenhedentabel werken.

Tijd rekent met 60 (niet met 100): daar gaat het vaak mis, en daar zoekt de diagnose naar.
Een tijdsduur typt het kind als '2 u 15 min', een tijdstip als '11.15 u'.
"""

import re
from decimal import Decimal

from ..getal import fmt, lees_getal
from ..klad import oplossing_van
from ..onderwerp import Onderwerp, Vraag
from .procenten import geld

D = Decimal


def duur_tekst(minuten):
    """95 → '1 u 35 min', 120 → '2 u', 45 → '45 min'."""
    u, m = divmod(int(minuten), 60)
    if u and m:
        return f"{u} u {m} min"
    return f"{u} u" if u else f"{m} min"


def klok_tekst(minuten):
    """Een tijdstip in minuten na middernacht → '9.05 u'."""
    u, m = divmod(int(minuten) % (24 * 60), 60)
    return f"{u}.{m:02d} u"


def lees_duur(tekst):
    """'2 u 15 min', '2u15', '2 uur', '45 min' → minuten (Decimal). Met uren moeten de minuten onder 60 blijven;
    zonder uren mag het niet meer dan 59 minuten zijn (anders schreef het kind de vraag gewoon over)."""
    t = (tekst or "").strip().lower()
    m = re.fullmatch(r"(?:(\d+)\s*(?:uur|u)\s*)?(?:(\d+)\s*(?:minuten|min|m)?)?", t)
    if not t or not m or (m.group(1) is None and m.group(2) is None):
        return None
    minuten = int(m.group(2) or 0)
    if minuten > 59:
        return None
    return D(int(m.group(1) or 0) * 60 + minuten)


def lees_klok(tekst):
    """'11.15 u', '11:15', '11 u 15', '11u15', '1115', '9.05', '11 u' → minuten na middernacht (Decimal) of None."""
    t = (tekst or "").strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d{1,2})(?:[.:h]|u)?(\d{2})u?", t)
    u, minuten = (int(m.group(1)), int(m.group(2))) if m else (None, 0)
    if not m and (m := re.fullmatch(r"(\d{1,2})u?", t)):
        u = int(m.group(1))
    if u is None or u > 23 or minuten > 59:
        return None
    return D(u * 60 + minuten)


def klok_cijfers(tekst):
    """Wat een digitaal klokje toont terwijl het kind een tijdstip typt (#21): 4 tekens (uur, uur, min, min),
    '_' = nog leeg, ' ' = geen cijfer. '16.1' → '161_', '9.45' en '945' → ' 945', '' → '____'.
    None als het geen tijdstip kan worden ('abc', '12345')."""
    t = (tekst or "").strip().lower().replace(" ", "")
    if t.endswith("u"):
        t = t[:-1]
    if m := re.fullmatch(r"(\d{0,2})[.:hu](\d{0,2})", t):
        uur, minuten = m.groups()
        return (uur.rjust(2) if uur else "__") + minuten.ljust(2, "_")
    if not re.fullmatch(r"\d{0,4}", t):
        return None
    return (" " + t) if len(t) == 3 else t.ljust(4, "_")


class _Grootheid(Onderwerp):
    vast = ("soort",)
    klad = "ja"

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def soort(self, p, rng, data):
        return data["soort"] if data and "soort" in data else rng.choice(p["soorten"])

    def spiekbrief(self):
        return SPIEKBRIEF

    def lees(self, tekst):
        return lees_getal((tekst or "").replace("€", "").strip())


# ---- tijd ------------------------------------------------------------------------------------------------

OMREKENEN = [  # (groot, groot meervoud, klein, factor)
    ("u", "u", "min", 60), ("min", "min", "s", 60), ("dag", "dagen", "u", 24), ("week", "weken", "dagen", 7),
    ("jaar", "jaar", "maanden", 12)]


class Tijd(_Grootheid):
    id = "wiskunde.eenheden.tijd"
    naam = "Tijd"
    omschrijving = "uren, minuten, seconden en tijdsduur"
    denkfouten = {"tijd_met_100": "met 100 gerekend in plaats van met 60",
                  "tijd_uur_vergeten": "60 minuten niet omgezet in een uur",
                  "tijd_verkeerde_kant": "vermenigvuldigd in plaats van gedeeld (of omgekeerd)"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        d = {"soort": soort, "onderwerp": soort}
        stap = p["stap"]
        if soort == "omrekenen":
            i = rng.randrange(p["omrekenen"])
            groot, mv, klein, f = OMREKENEN[i]
            n = rng.randint(2, 9)
            d.update(i=i, n=n, richting=rng.choice(["naar_klein", "naar_groot"]))
            if d["richting"] == "naar_klein":
                return Vraag(self.id, f"{self.id}:omrekenen:{n}{groot}>{klein}", f"{n} {mv} = ? {klein}",
                             D(n * f), eenheid=klein, data=d)
            return Vraag(self.id, f"{self.id}:omrekenen:{n * f}{klein}>{groot}", f"{n * f} {klein} = ? {mv}",
                         D(n), eenheid=mv, data=d)
        if soort in ("gemengd_naar", "naar_gemengd"):
            u, m = rng.randint(1, 4), rng.randrange(stap, 60, stap)
            totaal = u * 60 + m
            d.update(u=u, m=m)
            if soort == "gemengd_naar":
                return Vraag(self.id, f"{self.id}:gemengd_naar:{u}u{m}", f"{u} u {m} min = ? min", D(totaal),
                             eenheid="min", data=d)
            return Vraag(self.id, f"{self.id}:naar_gemengd:{totaal}", f"{totaal} min = ? u ? min", D(totaal),
                         data=d, invoer="duur", verwacht_tekst=duur_tekst(totaal))
        # tijdsduur of eindtijdstip, met tijdstippen overdag
        stap = max(stap, 5)
        begin = rng.randrange(7 * 60, 17 * 60, stap)
        duur = rng.randrange(2 * stap, p["max_duur"] + 1, stap)
        d.update(begin=begin, duur=duur)
        if soort == "duur":
            return Vraag(self.id, f"{self.id}:duur:{begin}+{duur}",
                         f"Van {klok_tekst(begin)} tot {klok_tekst(begin + duur)}: hoeveel minuten is dat?", D(duur),
                         eenheid="min", data=d)
        return Vraag(self.id, f"{self.id}:eindtijd:{begin}+{duur}",
                     f"Je vertrekt om {klok_tekst(begin)}. De rit duurt {duur_tekst(duur)}. Hoe laat kom je aan?",
                     D(begin + duur), data=d, invoer="klok", verwacht_tekst=klok_tekst(begin + duur))

    def lees_vraag(self, v, tekst):
        if v.invoer == "duur":
            return lees_duur(tekst)
        if v.invoer == "klok":
            return lees_klok(tekst)
        return self.lees(tekst)

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "omrekenen":
            groot, mv, klein, f = OMREKENEN[d["i"]]
            if d["richting"] == "naar_klein":
                return [f"1 {groot} = {f} {klein}, dus {d['n']} {mv} = {d['n']} × {f} = {d['n'] * f} {klein}."]
            return [f"1 {groot} = {f} {klein}, dus deel door {f}: {d['n'] * f} : {f} = {d['n']} {mv}."]
        if s == "gemengd_naar":
            return [f"{d['u']} u = {d['u']} × 60 = {d['u'] * 60} min.", f"{d['u'] * 60} + {d['m']} = {v.antwoord} min."]
        if s == "naar_gemengd":
            u, m = divmod(int(v.antwoord), 60)
            return [f"Hoeveel keer past 60 min erin? {u} × 60 = {u * 60}.",
                    f"Er blijft {m} min over: {duur_tekst(v.antwoord)}."]
        b, du = d["begin"], d["duur"]
        tot_uur = (60 - b % 60) % 60
        if s == "duur":
            if 0 < tot_uur < du:
                return [f"Tel in stapjes: van {klok_tekst(b)} tot {klok_tekst(b + tot_uur)} is {tot_uur} min,",
                        f"dan nog tot {klok_tekst(b + du)}: samen {du} min ({duur_tekst(du)})."]
            return [f"Van {klok_tekst(b)} tot {klok_tekst(b + du)} is {du} min ({duur_tekst(du)})."]
        return [f"{klok_tekst(b)} + {duur_tekst(du)}: tel eerst de uren, dan de minuten.",
                f"Je komt aan om {klok_tekst(b + du)}. Na 59 minuten komt er een uur bij."]

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s == "omrekenen":
            f, n = OMREKENEN[d["i"]][3], d["n"]
            return oplossing_van(f"{n} × {f} = {n * f}" if d["richting"] == "naar_klein" else f"{n * f} : {f} = {n}")
        if s == "gemengd_naar":
            return oplossing_van(f"{d['u']} × 60 = {d['u'] * 60}", f"{d['u'] * 60} + {d['m']} = {d['u'] * 60 + d['m']}")
        if s == "naar_gemengd":
            u, m = divmod(int(v.antwoord), 60)
            return oplossing_van(f"{int(v.antwoord)} : 60 = {u} rest {m}", f"{u} × 60 + {m} = {int(v.antwoord)}")
        b, du = d["begin"], d["duur"]
        tot = (60 - b % 60) % 60  # tel in stapjes tot het volle uur
        if s == "duur":
            if 0 < tot < du:
                return oplossing_van(f"{klok_tekst(b)} + {tot} min = {klok_tekst(b + tot)}",
                                     f"{klok_tekst(b + tot)} + {du - tot} min = {klok_tekst(b + du)}",
                                     f"{tot} + {du - tot} = {du}")
            return oplossing_van(f"{klok_tekst(b + du)} − {klok_tekst(b)} = {du} min")
        if 0 < tot < du:
            return oplossing_van(f"{klok_tekst(b)} + {tot} min = {klok_tekst(b + tot)}",
                                 f"{klok_tekst(b + tot)} + {du - tot} min = {klok_tekst(b + du)}")
        return oplossing_van(f"{klok_tekst(b)} + {du} min = {klok_tekst(b + du)}")

    def tip(self, v):
        if v.data["soort"] == "omrekenen":
            groot, _, klein, f = OMREKENEN[v.data["i"]]
            return f"1 {groot} = {f} {klein}. Naar een kleinere eenheid: maal. Naar een grotere: gedeeld door."
        return "Een uur heeft 60 minuten, geen 100! Tel in stapjes tot het volle uur."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        s = d["soort"]
        if s == "omrekenen":
            f, n = OMREKENEN[d["i"]][3], D(d["n"])
            klein = d["richting"] == "naar_klein"
            if getal == (n / f if klein else n * f * f):
                return "tijd_verkeerde_kant", "Andersom: naar een kleinere eenheid doe je maal, naar een grotere gedeeld door."
            if f == 60 and getal == (n * 100 if klein else n * f / 100):
                return "tijd_met_100", "Je rekende met 100. Een uur heeft 60 minuten, een minuut 60 seconden."
            return None
        if s == "gemengd_naar":
            if getal == d["u"] * 100 + d["m"]:
                return "tijd_met_100", f"Je rekende met 100 minuten per uur. {d['u']} u = {d['u'] * 60} min."
            return None
        if s == "naar_gemengd":
            u100, m100 = divmod(int(v.antwoord), 100)
            if m100 < 60 and getal == u100 * 60 + m100:
                return "tijd_met_100", "Je deelde door 100. Een uur heeft 60 minuten: kijk hoeveel keer 60 erin past."
            return None
        b, du = d["begin"], d["duur"]
        if s == "duur":
            kl = lambda x: (x // 60) * 100 + x % 60  # 9.45 u → 945
            if getal == kl(b + du) - kl(b):
                return "tijd_met_100", "Je trok de tijden af alsof een uur 100 minuten heeft. Tel in stapjes tot het volle uur."
        if s == "eindtijd" and b % 60 + du % 60 >= 60 and getal == b + du - 60:
            return "tijd_uur_vergeten", (f"{b % 60} + {du % 60} = {b % 60 + du % 60} min: dat is meer dan een uur, "
                                         f"dus er komt een uur bij.")
        return None


# ---- geld ------------------------------------------------------------------------------------------------

DINGEN = [("een boek", 8, 25), ("een spel", 12, 40), ("een pizza", 6, 15), ("een bal", 5, 20), ("een strip", 4, 12),
          ("een T-shirt", 9, 30), ("een rugzak", 15, 45), ("een puzzel", 7, 25)]
FRUIT = [("appel", "appels", 25, 70), ("peer", "peren", 30, 80), ("banaan", "bananen", 20, 60),
         ("kiwi", "kiwi's", 30, 90), ("sinaasappel", "sinaasappels", 40, 95)]


class Geld(_Grootheid):
    id = "wiskunde.eenheden.geld"
    naam = "Geld"
    omschrijving = "euro en cent, betalen en wisselgeld"
    denkfouten = {"geld_komma": "de komma verkeerd: 1 euro = 100 cent",
                  "wisselgeld_opgeteld": "opgeteld in plaats van afgetrokken"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        d = {"soort": soort, "onderwerp": soort}
        if soort in ("euro_naar_cent", "cent_naar_euro"):
            cent = rng.randint(101, p["max_cent"])
            d["cent"] = cent
            euro = D(cent) / 100
            if soort == "euro_naar_cent":
                return Vraag(self.id, f"{self.id}:euro_naar_cent:{cent}", f"€ {geld(euro)} = ? cent", D(cent),
                             eenheid="cent", data=d)
            return Vraag(self.id, f"{self.id}:cent_naar_euro:{cent}", f"{cent} cent = ? euro", euro, eenheid="euro",
                         data=d, verwacht_tekst=f"{geld(euro)} euro")
        if soort == "wisselgeld":
            ding, laag, hoog = rng.choice(DINGEN)
            prijs = D(rng.randint(laag * 20, hoog * 20) * 5) / 100
            briefje = next(b for b in (5, 10, 20, 50, 100) if b > prijs)
            terug = briefje - prijs
            d.update(ding=ding, prijs=str(prijs), briefje=briefje)
            return Vraag(self.id, f"{self.id}:wisselgeld:{prijs}:{briefje}",
                         f"Je koopt {ding} van € {geld(prijs)} en betaalt met € {briefje}. Hoeveel krijg je terug?",
                         terug, eenheid="euro", data=d, verwacht_tekst=f"{geld(terug)} euro")
        (a, amv, la, ha), (b, bmv, lb, hb) = rng.sample(FRUIT, 2)
        pa, pb = D(rng.randint(la // 5, ha // 5) * 5) / 100, D(rng.randint(lb // 5, hb // 5) * 5) / 100
        na, nb = rng.randint(2, 6), rng.randint(2, 5)
        totaal = na * pa + nb * pb
        d.update(a=a, b=b, pa=str(pa), pb=str(pb), na=na, nb=nb)
        return Vraag(self.id, f"{self.id}:samen:{na}{a}{pa}:{nb}{b}{pb}",
                     f"Een {a} kost € {geld(pa)}, een {b} € {geld(pb)}. Wat betaal je voor {na} {amv} en "
                     f"{nb} {bmv}?", totaal, eenheid="euro", data=d, verwacht_tekst=f"{geld(totaal)} euro")

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "euro_naar_cent":
            return [f"1 euro = 100 cent, dus × 100: € {geld(D(d['cent']) / 100)} = {d['cent']} cent."]
        if s == "cent_naar_euro":
            return [f"100 cent = 1 euro, dus : 100: {d['cent']} cent = € {geld(D(d['cent']) / 100)}."]
        if s == "wisselgeld":
            prijs = D(d["prijs"])
            return [f"Trek af: € {d['briefje']} − € {geld(prijs)} = € {geld(v.antwoord)}.",
                    f"Of tel aan van € {geld(prijs)} tot € {d['briefje']}, zoals aan de kassa."]
        pa, pb = D(d["pa"]), D(d["pb"])
        return [f"{d['na']} × € {geld(pa)} = € {geld(d['na'] * pa)} en {d['nb']} × € {geld(pb)} = € {geld(d['nb'] * pb)}.",
                f"Samen: € {geld(v.antwoord)}."]

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s == "euro_naar_cent":
            return oplossing_van(f"{fmt(D(d['cent']) / 100)} × 100 = {d['cent']}")
        if s == "cent_naar_euro":
            return oplossing_van(f"{d['cent']} : 100 = {fmt(D(d['cent']) / 100)}")
        if s == "wisselgeld":
            return oplossing_van(f"{d['briefje']} − {fmt(D(d['prijs']))} = {fmt(v.antwoord)}")
        pa, pb = D(d["pa"]), D(d["pb"])
        return oplossing_van(f"{d['na']} × {fmt(pa)} = {fmt(d['na'] * pa)}", f"{d['nb']} × {fmt(pb)} = {fmt(d['nb'] * pb)}",
                             f"{fmt(d['na'] * pa)} + {fmt(d['nb'] * pb)} = {fmt(v.antwoord)}")

    def tip(self, v):
        if v.data["soort"] == "wisselgeld":
            return "Wisselgeld = wat je betaalt − de prijs. Of tel aan tot het briefje."
        return "1 euro = 100 cent. De komma schuift 2 plaatsen."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        s = d["soort"]
        if s in ("euro_naar_cent", "cent_naar_euro") and getal in (v.antwoord * 10, v.antwoord / 10,
                                                                    v.antwoord * 100, v.antwoord / 100):
            return "geld_komma", "Let op de komma: 1 euro = 100 cent, dus de komma schuift 2 plaatsen."
        if s == "wisselgeld" and getal == d["briefje"] + D(d["prijs"]):
            return "wisselgeld_opgeteld", "Wisselgeld: je trekt de prijs af van wat je betaalt."
        return None


# ---- snelheid --------------------------------------------------------------------------------------------

REIZIGERS = [("Een fietser", "fietst", 12, 24, 4), ("Een auto", "rijdt", 60, 120, 10),
             ("Een trein", "rijdt", 80, 160, 10), ("Een wandelaar", "wandelt", 4, 6, 1)]


class Snelheid(_Grootheid):
    id = "wiskunde.eenheden.snelheid"
    naam = "Snelheid"
    omschrijving = "afstand, tijd en snelheid (km/u, m/s)"
    denkfouten = {"snelheid_bewerking": "vermenigvuldigd in plaats van gedeeld (of omgekeerd)",
                  "snelheid_minuten": "minuten niet omgezet in uren",
                  "snelheid_3_6": "bij km/u en m/s de verkeerde kant op met 3,6"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        d = {"soort": soort, "onderwerp": soort}
        if soort == "omzetten":  # km/u ↔ m/s
            ms = rng.choice([5, 10, 15, 20, 25, 30])
            kmu = D(ms) * D("3.6")
            d.update(richting=rng.choice(["naar_ms", "naar_kmu"]), kmu=str(kmu), ms=ms)
            if d["richting"] == "naar_ms":
                return Vraag(self.id, f"{self.id}:omzetten:{fmt(kmu)}kmu", f"{fmt(kmu)} km/u = ? m/s", D(ms),
                             eenheid="m/s", data=d)
            return Vraag(self.id, f"{self.id}:omzetten:{ms}ms", f"{ms} m/s = ? km/u", kmu, eenheid="km/u", data=d)
        wie, werkw, laag, hoog, stap = rng.choice(REIZIGERS)
        snel = rng.randrange(laag, hoog + 1, stap)
        minuten = rng.choice(p["tijden"])
        afstand = D(snel) * minuten / 60
        d.update(wie=wie, v=snel, min=minuten, km=str(afstand))
        if soort == "afstand":
            return Vraag(self.id, f"{self.id}:afstand:{snel}:{minuten}",
                         f"{wie} {werkw} {snel} km/u. Hoe ver is dat in {duur_tekst(minuten)}?", afstand,
                         eenheid="km", data=d)
        if soort == "tijd":
            return Vraag(self.id, f"{self.id}:tijd:{snel}:{minuten}",
                         f"{wie} {werkw} {snel} km/u. Hoeveel minuten duurt {fmt(afstand)} km?", D(minuten),
                         eenheid="min", data=d)
        return Vraag(self.id, f"{self.id}:snelheid:{snel}:{minuten}",
                     f"{wie} legt {fmt(afstand)} km af in {duur_tekst(minuten)}. Hoe snel is dat gemiddeld?", D(snel),
                     eenheid="km/u", data=d)

    def uitleg(self, v):
        d = v.data
        s = d["soort"]
        if s == "omzetten":
            if d["richting"] == "naar_ms":
                return [f"1 m/s = 3,6 km/u, dus deel door 3,6: {fmt(D(d['kmu']))} : 3,6 = {d['ms']} m/s."]
            return [f"1 m/s = 3600 m per uur = 3,6 km/u, dus × 3,6: {d['ms']} × 3,6 = {fmt(D(d['kmu']))} km/u."]
        uren = fmt(D(d["min"]) / 60)
        km = fmt(D(d["km"]))
        omzetten = f"{duur_tekst(d['min'])} = {uren} u, dus " if d["min"] % 60 else ""
        if s == "afstand":
            return ["afstand = snelheid × tijd", f"{omzetten}{d['v']} × {uren} = {km} km."]
        if s == "tijd":
            return ["tijd = afstand : snelheid", f"{km} : {d['v']} = {uren} u = {d['min']} min."]
        return ["snelheid = afstand : tijd", f"{omzetten}{km} : {uren} = {d['v']} km/u."]

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s == "omzetten":
            kmu = fmt(D(d["kmu"]))
            return oplossing_van(f"{kmu} : 3,6 = {d['ms']}" if d["richting"] == "naar_ms" else f"{d['ms']} × 3,6 = {kmu}")
        uren, km = fmt(D(d["min"]) / 60), fmt(D(d["km"]))
        omzetten = f"{d['min']} : 60 = {uren}" if d["min"] % 60 else ""
        if s == "afstand":
            return oplossing_van(omzetten, f"{d['v']} × {uren} = {km}")
        if s == "tijd":
            return oplossing_van(f"{km} : {d['v']} = {uren}", f"{uren} × 60 = {d['min']}")
        return oplossing_van(omzetten, f"{km} : {uren} = {d['v']}")

    def tip(self, v):
        if v.data["soort"] == "omzetten":
            return "1 m/s = 3,6 km/u. Naar km/u: × 3,6. Naar m/s: : 3,6."
        return "km/u = zoveel km in 1 uur. Zet minuten eerst om in uren (30 min = 0,5 u)."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        s = d["soort"]
        if s == "omzetten":
            kmu, ms = D(d["kmu"]), D(d["ms"])
            if getal == (kmu * D("3.6") if d["richting"] == "naar_ms" else ms / D("3.6")):
                return "snelheid_3_6", "Andersom met 3,6: van km/u naar m/s deel je, van m/s naar km/u doe je maal."
            return None
        km, snel, minuten = D(d["km"]), D(d["v"]), D(d["min"])
        if s == "afstand" and getal == snel * minuten:
            return "snelheid_minuten", "Je rekende met minuten. km/u gaat per uur: zet de minuten eerst om in uren."
        if s == "afstand" and getal == snel * 60 / minuten:
            return "snelheid_bewerking", "Afstand = snelheid × tijd (niet gedeeld)."
        if s == "tijd" and getal == km * snel:
            return "snelheid_bewerking", "Tijd = afstand : snelheid (niet maal)."
        if s == "snelheid" and getal == km / minuten:
            return "snelheid_minuten", "Je deelde door de minuten. Snelheid in km/u: deel door het aantal uren."
        return None


SPIEKBRIEF = [
    ("TIJD", "accent"),
    ("  1 u = 60 min     1 min = 60 s     1 dag = 24 u", ""),
    ("  1 week = 7 dagen     1 jaar = 12 maanden", ""),
    ("  Een uur heeft 60 minuten, geen 100!", ""),
    ("  135 min = 2 u 15 min  (2 × 60 = 120, en nog 15)", ""),
    ("  Tijdsduur: tel in stapjes tot het volle uur.", ""),
    ("  8.45 u → 9.00 u = 15 min, 9.00 u → 10.20 u = 1 u 20 min, samen 1 u 35 min", ""),
    ("", ""),
    ("GELD", "accent"),
    ("  1 euro = 100 cent      € 3,45 = 345 cent      275 cent = € 2,75", ""),
    ("  Wisselgeld = wat je betaalt − de prijs.  € 20 − € 12,35 = € 7,65", ""),
    ("", ""),
    ("SNELHEID  (6de leerjaar)", "accent"),
    ("  afstand = snelheid × tijd      tijd = afstand : snelheid", ""),
    ("  snelheid = afstand : tijd", ""),
    ("  60 km/u = 60 km in 1 uur.  30 min = 0,5 u   15 min = 0,25 u", ""),
    ("  1 m/s = 3,6 km/u   (van km/u naar m/s: : 3,6)", ""),
]

TIJD = Tijd()
GELD = Geld()
SNELHEID = Snelheid()
ALLE = [TIJD, GELD, SNELHEID]
