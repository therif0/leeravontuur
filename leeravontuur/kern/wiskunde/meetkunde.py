"""Meetkunde: oppervlakte en omtrek op het cm²-rooster, formules (ook cirkel en volume), hoeken, coördinaten
(de schatkaart en het assenstelsel) en schaal.
"""

import hashlib
import re
from decimal import Decimal

from ..getal import fmt, lees_getal
from ..klad import oplossing_van
from ..modellen import KOLOMLETTERS, Figuur, Hoek, Kaart, fmt_geheel
from ..onderwerp import Onderwerp, Vraag

D = Decimal
PI = D("3.14")


class _Meetkunde(Onderwerp):
    vast = ("soort",)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def soort(self, p, rng, data):
        return data["soort"] if data and "soort" in data else rng.choice(p["soorten"])

    def spiekbrief(self):
        return SPIEKBRIEF_MEETKUNDE


# ---- oppervlakte en omtrek op het rooster ------------------------------------------------------------------

def maak_figuur(vorm, p, rng):
    """Een figuur op een rooster van p['rijen'] × p['kolommen'] vakjes."""
    rijen, kolommen = p["rijen"], p["kolommen"]
    if vorm == "driehoek":  # rechthoekige driehoek met twee gelijke zijden, schuine kant door halve vakjes
        n = rng.randint(3, min(rijen, kolommen))
        r0, k0 = rng.randint(0, rijen - n), rng.randint(0, kolommen - n)
        vakjes = {(r0 + i, k0 + j) for i in range(n) for j in range(i)}
        return Figuur(rijen, kolommen, vakjes, {(r0 + i, k0 + i) for i in range(n)})
    b, h = rng.randint(2, kolommen), rng.randint(2, rijen)
    if vorm != "rechthoek":
        b, h = max(b, 3), max(h, 3)
    r0, k0 = rng.randint(0, rijen - h), rng.randint(0, kolommen - b)
    vakjes = {(r0 + i, k0 + j) for i in range(h) for j in range(b)}
    if vorm == "L":  # een hoek eruit
        hb, hh = rng.randint(1, b - 1), rng.randint(1, h - 1)
        boven, links = rng.random() < 0.5, rng.random() < 0.5
        rs = range(r0, r0 + hh) if boven else range(r0 + h - hh, r0 + h)
        ks = range(k0, k0 + hb) if links else range(k0 + b - hb, k0 + b)
        vakjes -= {(r, k) for r in rs for k in ks}
    elif vorm == "trap":  # elke rij (van onder naar boven) een stukje korter
        vakjes = set()
        breedte = b
        for i in range(h):
            vakjes |= {(r0 + h - 1 - i, k0 + j) for j in range(breedte)}
            breedte = max(1, breedte - rng.randint(1, 2))
    return Figuur(rijen, kolommen, vakjes)


class Rooster(_Meetkunde):
    id = "wiskunde.meetkunde.rooster"
    naam = "Oppervlakte en omtrek"
    omschrijving = "tel de vakjes en de randjes op het rooster"
    vast = ("soort", "vorm")
    denkfouten = {"omtrek_oppervlakte": "omtrek en oppervlakte verwisseld",
                  "binnenranden": "ook de randjes binnenin de figuur geteld",
                  "halve_als_hele": "halve vakjes als hele geteld",
                  "halve_vergeten": "de halve vakjes vergeten"}

    def spiekbrief(self):
        return SPIEKBRIEF_OPPERVLAKTE

    def maak_met(self, p, rng, data=None):
        vorm = data["vorm"] if data and "vorm" in data else rng.choice(p["vormen"])
        soort = "oppervlakte" if vorm == "driehoek" else self.soort(p, rng, data)
        fig = maak_figuur(vorm, p, rng)
        while vorm != "driehoek" and fig.omtrek() == fig.oppervlakte():  # anders zie je niet wat er verwisseld is
            fig = maak_figuur(vorm, p, rng)
        d = {"soort": soort, "vorm": vorm, "onderwerp": soort, "vol": len(fig.vakjes), "half": len(fig.halve)}
        vorm_id = hashlib.sha1(repr((sorted(fig.vakjes), sorted(fig.halve))).encode()).hexdigest()[:10]
        sleutel = f"{self.id}:{soort}:{vorm}:{vorm_id}"
        if soort == "oppervlakte":
            return Vraag(self.id, sleutel, "Hoe groot is de oppervlakte van de figuur?", fig.oppervlakte(),
                         eenheid="cm²", data=d, model=fig)
        d.update(omtrek=fig.omtrek(), binnen=fig.binnenranden())
        return Vraag(self.id, sleutel, "Hoe groot is de omtrek van de figuur?", D(fig.omtrek()), eenheid="cm",
                     data=d, model=fig, model_na=Figuur(fig.rijen, fig.kolommen, fig.vakjes, rand=True))

    def uitleg(self, v):
        d = v.data
        if d["soort"] == "omtrek":
            return ["De omtrek is de rand rondom: tel elk randje van 1 cm (ze zijn aangeduid).",
                    f"Rondom zijn er {d['omtrek']} randjes: de omtrek is {d['omtrek']} cm."]
        if d["half"]:
            return [f"{d['vol']} hele vakjes en {d['half']} halve vakjes. 2 halve = 1 heel vakje.",
                    f"{d['vol']} + ({d['half']} : 2) = {d['vol']} + {fmt(D(d['half']) / 2)} = {fmt(v.antwoord)} cm²."]
        return [f"Tel de gekleurde vakjes: {d['vol']} vakjes van 1 cm², dus {d['vol']} cm².",
                "Tip: tel per rij en tel de rijen samen."]

    def tip(self, v):
        if v.data["soort"] == "omtrek":
            return "Omtrek = de randjes rondom (in cm). Begin in een hoek en ga de rand rond."
        if v.data["half"]:
            return "Twee halve vakjes samen zijn één heel vakje."
        return "Oppervlakte = hoeveel vakjes van 1 cm² er gekleurd zijn."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        if d["soort"] == "omtrek":
            if getal == d["vol"]:
                return "omtrek_oppervlakte", "Je telde de vakjes: dat is de oppervlakte. De omtrek zijn de randjes rondom."
            if d["binnen"] and getal == d["omtrek"] + d["binnen"]:
                return "binnenranden", "Je telde ook de randjes binnenin. De omtrek is alleen de rand rondom."
            return None
        if d["half"]:
            if getal == d["vol"] + d["half"]:
                return "halve_als_hele", "Je telde de halve vakjes als hele. Twee halve = één heel vakje."
            if getal == d["vol"]:
                return "halve_vergeten", "Je vergat de halve vakjes. Twee halve = één heel vakje."
            return None
        fig = v.model
        if getal == fig.omtrek():
            return "omtrek_oppervlakte", "Je telde de randjes: dat is de omtrek. De oppervlakte zijn de vakjes."
        return None


# ---- formules ----------------------------------------------------------------------------------------------

FIGUREN = {  # figuur: (naam, wat, eenheid)
    "rechthoek_opp": ("rechthoek", "oppervlakte", "cm²"), "rechthoek_omtrek": ("rechthoek", "omtrek", "cm"),
    "vierkant_opp": ("vierkant", "oppervlakte", "cm²"), "vierkant_omtrek": ("vierkant", "omtrek", "cm"),
    "driehoek_opp": ("driehoek", "oppervlakte", "cm²"), "parallellogram_opp": ("parallellogram", "oppervlakte", "cm²"),
    "trapezium_opp": ("trapezium", "oppervlakte", "cm²"), "cirkel_omtrek": ("cirkel", "omtrek", "cm"),
    "cirkel_opp": ("cirkel", "oppervlakte", "cm²"), "balk_volume": ("balk", "volume", "cm³"),
    "kubus_volume": ("kubus", "volume", "cm³")}


class Formules(_Meetkunde):
    id = "wiskunde.meetkunde.formules"
    naam = "Formules"
    omschrijving = "oppervlakte, omtrek en volume uitrekenen"
    vast = ("soort",)
    denkfouten = {"deel_door_2_vergeten": "vergeten te delen door 2",
                  "omtrek_ipv_opp": "de omtrek berekend in plaats van de oppervlakte",
                  "opp_ipv_omtrek": "de oppervlakte berekend in plaats van de omtrek",
                  "maar_2_zijden": "maar 2 zijden opgeteld voor de omtrek",
                  "straal_diameter": "straal en diameter verwisseld"}

    def spiekbrief(self):
        return SPIEKBRIEF_OPPERVLAKTE

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        fig, wat, eenheid = FIGUREN[soort]
        d = {"soort": soort, "onderwerp": soort}

        def maat(laag=2, hoog=None):
            hoog = hoog or p["max"]
            if p["komma"] and rng.random() < 0.3:
                return D(rng.randint(laag * 2, hoog * 2)) / 2
            return D(rng.randint(laag, hoog))

        if fig == "rechthoek":
            l = maat(3)
            b = maat(2, max(2, int(l) - 1))
            d.update(l=str(l), b=str(b))
            tekst = f"Een rechthoek is {fmt(l)} cm lang en {fmt(b)} cm breed."
        elif fig in ("vierkant", "kubus"):
            z = maat(2, min(p["max"], 10 if fig == "kubus" else p["max"]))
            d.update(z=str(z))
            tekst = f"Een {fig} heeft zijden van {fmt(z)} cm."
        elif fig in ("driehoek", "parallellogram"):
            b, h = maat(2), maat(2)
            d.update(b=str(b), h=str(h))
            tekst = f"Een {fig} heeft een basis van {fmt(b)} cm en een hoogte van {fmt(h)} cm."
        elif fig == "trapezium":
            B = maat(4)
            b = maat(2, max(2, int(B) - 1))
            h = maat(2)
            d.update(B=str(B), b=str(b), h=str(h))
            tekst = f"Een trapezium: grote basis {fmt(B)} cm, kleine basis {fmt(b)} cm, hoogte {fmt(h)} cm."
        elif fig == "cirkel":
            r = D(rng.randint(1, 10))
            diameter = rng.random() < 0.5
            d.update(r=str(r), diameter=diameter)
            tekst = (f"Een cirkel heeft een diameter van {fmt(2 * r)} cm." if diameter else
                     f"Een cirkel heeft een straal van {fmt(r)} cm.") + " Neem π = 3,14."
        else:  # balk
            l, b, h = maat(2, 12), maat(2, 10), maat(2, 10)
            d.update(l=str(l), b=str(b), h=str(h))
            tekst = f"Een balk is {fmt(l)} cm lang, {fmt(b)} cm breed en {fmt(h)} cm hoog."
        antwoord = self.bereken(soort, d)
        maten = "x".join(f"{k}{d[k]}" for k in ("l", "b", "h", "z", "B", "r") if k in d)
        return Vraag(self.id, f"{self.id}:{soort}:{maten}{'d' if d.get('diameter') else ''}", f"{tekst} Wat is de {wat}?",
                     antwoord, eenheid=eenheid, data=d)

    @staticmethod
    def bereken(soort, d):
        g = {k: D(w) for k, w in d.items() if k in ("l", "b", "h", "z", "B", "r")}
        return {
            "rechthoek_opp": lambda: g["l"] * g["b"], "rechthoek_omtrek": lambda: 2 * (g["l"] + g["b"]),
            "vierkant_opp": lambda: g["z"] * g["z"], "vierkant_omtrek": lambda: 4 * g["z"],
            "driehoek_opp": lambda: g["b"] * g["h"] / 2, "parallellogram_opp": lambda: g["b"] * g["h"],
            "trapezium_opp": lambda: (g["B"] + g["b"]) * g["h"] / 2, "cirkel_omtrek": lambda: 2 * PI * g["r"],
            "cirkel_opp": lambda: PI * g["r"] * g["r"], "balk_volume": lambda: g["l"] * g["b"] * g["h"],
            "kubus_volume": lambda: g["z"] ** 3,
        }[soort]()

    klad = "ja"

    def oplossing(self, v):
        d, s, a = v.data, v.data["soort"], fmt(v.antwoord)
        f = {k: fmt(D(w)) for k, w in d.items() if k in ("l", "b", "h", "z", "B", "r")}
        regel = {
            "rechthoek_opp": f"{f.get('l')} × {f.get('b')} = {a}",
            "rechthoek_omtrek": f"2 × ({f.get('l')} + {f.get('b')}) = {a}",
            "vierkant_opp": f"{f.get('z')} × {f.get('z')} = {a}",
            "vierkant_omtrek": f"4 × {f.get('z')} = {a}",
            "driehoek_opp": f"{f.get('b')} × {f.get('h')} : 2 = {a}",
            "parallellogram_opp": f"{f.get('b')} × {f.get('h')} = {a}",
            "trapezium_opp": f"({f.get('B')} + {f.get('b')}) × {f.get('h')} : 2 = {a}",
            "cirkel_omtrek": f"2 × 3,14 × {f.get('r')} = {a}",
            "cirkel_opp": f"3,14 × {f.get('r')} × {f.get('r')} = {a}",
            "balk_volume": f"{f.get('l')} × {f.get('b')} × {f.get('h')} = {a}",
            "kubus_volume": f"{f.get('z')} × {f.get('z')} × {f.get('z')} = {a}",
        }[s]
        straal = f"{fmt(2 * D(d['r']))} : 2 = {f['r']}" if s.startswith("cirkel") and d.get("diameter") else ""
        return oplossing_van(straal, regel)

    def lees(self, tekst):
        return lees_getal(tekst)

    def uitleg(self, v):
        d, s, a = v.data, v.data["soort"], fmt(v.antwoord)
        f = {k: fmt(D(w)) for k, w in d.items() if k in ("l", "b", "h", "z", "B", "r")}
        eenheid = v.eenheid
        regels = {
            "rechthoek_opp": f"Oppervlakte = lengte × breedte = {f.get('l')} × {f.get('b')} = {a} {eenheid}",
            "rechthoek_omtrek": f"Omtrek = 2 × (lengte + breedte) = 2 × ({f.get('l')} + {f.get('b')}) = {a} {eenheid}",
            "vierkant_opp": f"Oppervlakte = zijde × zijde = {f.get('z')} × {f.get('z')} = {a} {eenheid}",
            "vierkant_omtrek": f"Omtrek = 4 × zijde = 4 × {f.get('z')} = {a} {eenheid}",
            "driehoek_opp": f"Oppervlakte = basis × hoogte : 2 = {f.get('b')} × {f.get('h')} : 2 = {a} {eenheid}",
            "parallellogram_opp": f"Oppervlakte = basis × hoogte = {f.get('b')} × {f.get('h')} = {a} {eenheid}",
            "trapezium_opp": f"Oppervlakte = (B + b) × h : 2 = ({f.get('B')} + {f.get('b')}) × {f.get('h')} : 2 = {a} {eenheid}",
            "cirkel_omtrek": f"Omtrek = 2 × π × straal = 2 × 3,14 × {f.get('r')} = {a} {eenheid}",
            "cirkel_opp": f"Oppervlakte = π × straal × straal = 3,14 × {f.get('r')} × {f.get('r')} = {a} {eenheid}",
            "balk_volume": f"Volume = l × b × h = {f.get('l')} × {f.get('b')} × {f.get('h')} = {a} {eenheid}",
            "kubus_volume": f"Volume = z × z × z = {f.get('z')} × {f.get('z')} × {f.get('z')} = {a} {eenheid}",
        }
        uit = [regels[s]]
        if s.startswith("cirkel") and d["diameter"]:
            uit.insert(0, f"Eerst de straal: de helft van de diameter, {fmt(2 * D(d['r']))} : 2 = {f['r']} cm.")
        elif s == "driehoek_opp":
            uit.append("Een driehoek is de helft van een parallellogram met dezelfde basis en hoogte: daarom : 2.")
        elif s == "trapezium_opp":
            uit.append("Twee dezelfde trapeziums vormen samen een parallellogram: daarom : 2.")
        return uit

    def tip(self, v):
        s = v.data["soort"]
        if s.startswith("cirkel"):
            return "Straal = de helft van de diameter. Omtrek = 2 × π × r, oppervlakte = π × r × r."
        return {"driehoek_opp": "Driehoek: basis × hoogte, en dan : 2.",
                "trapezium_opp": "Trapezium: (grote basis + kleine basis) × hoogte : 2.",
                "rechthoek_omtrek": "Omtrek = alle 4 zijden samen.",
                "vierkant_omtrek": "Omtrek = alle 4 zijden samen."}.get(
            s, "Oppervlakte = hoeveel vakjes van 1 cm² erin passen. Kijk op de spiekbrief voor de formule.")

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d, s = v.data, v.data["soort"]
        if s in ("driehoek_opp", "trapezium_opp") and getal == 2 * v.antwoord:
            return "deel_door_2_vergeten", "Je vergat te delen door 2."
        if s.startswith(("rechthoek", "vierkant")):
            ander = s.replace("_opp", "_X").replace("_omtrek", "_opp").replace("_X", "_omtrek")
            if getal == self.bereken(ander, d):
                if s.endswith("_opp"):
                    return "omtrek_ipv_opp", "Dat is de omtrek (de rand). De oppervlakte is lengte × breedte."
                return "opp_ipv_omtrek", "Dat is de oppervlakte. De omtrek is de rand: alle zijden samen."
            if s == "rechthoek_omtrek" and getal == v.antwoord / 2:
                return "maar_2_zijden", "Een rechthoek heeft 4 zijden: 2 lengtes en 2 breedtes."
        if s.startswith("cirkel"):
            if d["diameter"] and getal == v.antwoord * (2 if s == "cirkel_omtrek" else 4):
                return "straal_diameter", "Je rekende met de diameter. De straal is de helft van de diameter."
            if not d["diameter"] and getal == v.antwoord / (2 if s == "cirkel_omtrek" else 4):
                return "straal_diameter", "Je nam de helft van de straal. De straal gebruik je zoals hij is."
        return None


# ---- hoeken ------------------------------------------------------------------------------------------------

SOORTEN_HOEK = ["scherp", "recht", "stomp", "gestrekt", "vol"]
BIJVOEGLIJK = {"scherp": "scherpe", "recht": "rechte", "stomp": "stompe", "gestrekt": "gestrekte", "vol": "volle"}


def hoek_soort(graden):
    if graden < 90:
        return "scherp"
    if graden == 90:
        return "recht"
    if graden < 180:
        return "stomp"
    return "gestrekt" if graden == 180 else "vol"


class Hoeken(_Meetkunde):
    id = "wiskunde.meetkunde.hoeken"
    naam = "Hoeken"
    omschrijving = "scherp, recht, stomp; de hoeken van een driehoek"
    denkfouten = {"stomp_scherp": "scherp en stomp verwisseld",
                  "hoekensom": "de som van de hoeken in een driehoek is 180°",
                  "nevenhoek": "nevenhoeken zijn samen 180°"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        d = {"soort": soort, "onderwerp": soort}
        if soort in ("tekening", "graden"):
            soorten = p["hoeken"]
            welke = rng.choice(soorten if soort == "graden" else [h for h in soorten if h != "vol"])
            graden = {"scherp": rng.choice([20, 30, 40, 45, 50, 60] if soort == "tekening" else range(5, 90, 5)),
                      "recht": 90,
                      "stomp": rng.choice([120, 130, 135, 145, 150] if soort == "tekening" else range(95, 180, 5)),
                      "gestrekt": 180, "vol": 360}[welke]
            d["graden"] = graden
            if soort == "tekening":
                return Vraag(self.id, f"{self.id}:tekening:{graden}", "Wat voor hoek is dit?", welke, data=d,
                             invoer="woord", model=Hoek(graden))
            return Vraag(self.id, f"{self.id}:graden:{graden}", f"Een hoek van {graden}°: wat voor hoek is dat?",
                         welke, data=d, invoer="woord")
        if soort == "driehoek":
            a = rng.randrange(20, 120, 5)
            b = rng.randrange(20, 160 - a, 5)
            d.update(a=a, b=b)
            return Vraag(self.id, f"{self.id}:driehoek:{a}:{b}",
                         f"In een driehoek zijn twee hoeken {a}° en {b}°. Hoe groot is de derde hoek?",
                         D(180 - a - b), eenheid="°", data=d)
        a = rng.randrange(15, 170, 5)
        d.update(a=a)
        return Vraag(self.id, f"{self.id}:nevenhoek:{a}",
                     f"Twee nevenhoeken (samen een gestrekte hoek): de ene is {a}°. Hoe groot is de andere?",
                     D(180 - a), eenheid="°", data=d)

    def lees_vraag(self, v, tekst):
        if v.invoer == "woord":
            t = re.sub(r"\s*hoek$", "", (tekst or "").strip().lower())
            t = {b: h for h, b in BIJVOEGLIJK.items()}.get(t, t)  # 'scherpe' → 'scherp'
            return t if t in SOORTEN_HOEK else None
        return lees_getal((tekst or "").replace("°", ""))

    def uitleg(self, v):
        d, s = v.data, v.data["soort"]
        if s in ("tekening", "graden"):
            g = d["graden"]
            waarom = {"scherp": "kleiner dan 90° (kleiner dan een rechte hoek)", "recht": "precies 90° (zoals de hoek van een blad)",
                      "stomp": "tussen 90° en 180° (groter dan een rechte hoek)",
                      "gestrekt": "precies 180° (een rechte lijn)", "vol": "360°: helemaal rond"}[v.antwoord]
            return [f"Deze hoek is {g}°: {waarom}.", f"Dat is een {BIJVOEGLIJK[v.antwoord]} hoek."]
        if s == "driehoek":
            return ["De 3 hoeken van een driehoek zijn samen 180°.",
                    f"180° − {d['a']}° − {d['b']}° = {fmt(v.antwoord)}°."]
        return ["Nevenhoeken vormen samen een gestrekte hoek: 180°.", f"180° − {d['a']}° = {fmt(v.antwoord)}°."]

    def tip(self, v):
        s = v.data["soort"]
        if s in ("tekening", "graden"):
            return "Vergelijk met een rechte hoek (90°, de hoek van een blad): kleiner = scherp, groter = stomp."
        if s == "driehoek":
            return "De hoeken van een driehoek zijn samen 180°."
        return "Twee nevenhoeken zijn samen 180°."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d, s = v.data, v.data["soort"]
        if s in ("tekening", "graden") and {getal, v.antwoord} == {"scherp", "stomp"}:
            return "stomp_scherp", "Scherp en stomp verwisseld: scherp is kleiner dan 90°, stomp groter."
        if s == "driehoek" and getal in (D(360 - d["a"] - d["b"]), D(d["a"] + d["b"])):
            return "hoekensom", "De 3 hoeken van een driehoek zijn samen 180°: trek de twee hoeken af van 180°."
        if s == "nevenhoek" and getal in (D(360 - d["a"]), D(90 - d["a"])):
            return "nevenhoek", "Nevenhoeken zijn samen 180° (een gestrekte hoek)."
        return None


# ---- coördinaten: de schatkaart ------------------------------------------------------------------------------

def lees_coord(kaart, tekst):
    """'C4', 'c 4', '(C, 4)' op de schatkaart, '(3, -2)' of '3 -2' in een assenstelsel → (x, y) of None."""
    t = (tekst or "").strip().upper().replace("−", "-")
    if kaart.assen:
        m = re.fullmatch(r"\(?\s*(-?\d+)\s*[,; ]\s*(-?\d+)\s*\)?", t)
        if not m:
            return None
        x, y = int(m.group(1)), int(m.group(2))
    else:
        m = re.fullmatch(r"\(?\s*([A-Z])\s*[,; ]?\s*(\d+)\s*\)?", t)
        if not m:
            return None
        x, y = KOLOMLETTERS.find(m.group(1)) + 1, int(m.group(2))
    return (x, y) if x in kaart.xs() and y in kaart.ys() else None


class Coordinaten(_Meetkunde):
    id = "wiskunde.meetkunde.coordinaten"
    naam = "Schatkaart"
    omschrijving = "coördinaten: waar ligt de schat?"
    denkfouten = {"coord_omgewisseld": "kolom en rij (x en y) omgewisseld",
                  "rij_van_boven": "de rijen van boven geteld in plaats van van onder"}

    def maak_kaart(self, soort, p):
        if soort.startswith("assen"):
            return Kaart(assen=p["assen"])
        return Kaart(p["kolommen"], p["rijen"])

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        kaart = self.maak_kaart(soort, p)
        x, y = rng.choice(kaart.xs()), rng.choice(kaart.ys())
        naam = kaart.naam(x, y)
        d = {"soort": soort, "onderwerp": soort, "x": x, "y": y}
        if soort.endswith("aflezen"):
            kaart.punten = {(x, y): "✦"}
            vraag = ("Welke coördinaat heeft de schat ✦? Typ bv. (2, −3)" if kaart.assen else
                     "Waar ligt de schat ✦? Typ bv. C4")
            return Vraag(self.id, f"{self.id}:{soort}:{naam}", vraag, naam, data=d, model=kaart, invoer="plek")
        vraag = f"Zet een kruisje op {naam}." if not kaart.assen else f"Zet een kruisje op het punt {naam}."
        return Vraag(self.id, f"{self.id}:{soort}:{naam}", vraag, naam, data=d, model=kaart, invoer="coord")

    def lees_vraag(self, v, tekst):
        punt = lees_coord(v.model, tekst)
        return v.model.naam(*punt) if punt else None

    def uitleg(self, v):
        d, kaart = v.data, v.model
        if kaart.assen:
            return [f"Eerst x (naar rechts of links): {fmt_geheel(d['x'])}, dan y (naar boven of onder): "
                    f"{fmt_geheel(d['y'])}.", f"Het punt is {v.antwoord}. Eerst door de gang, dan de trap op!"]
        return [f"Eerst de kolom (de letter onderaan): {v.antwoord[0]}, dan de rij (het getal links): {d['y']}.",
                f"De schat ligt op {v.antwoord}. Rij 1 staat onderaan."]

    def tip(self, v):
        if v.model.assen:
            return "Eerst x (horizontaal, naar rechts +), dan y (verticaal, naar boven +)."
        return "Eerst de letter (kolom, onderaan), dan het getal (rij, links). Rij 1 staat onderaan."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        kaart, d = v.model, v.data
        punt = lees_coord(kaart, getal)
        if punt is None:
            return None
        if punt == (d["y"], d["x"]):
            return "coord_omgewisseld", ("Je wisselde x en y om. Eerst x (horizontaal), dan y (verticaal)."
                                         if kaart.assen else "Je wisselde kolom en rij om. Eerst de letter, dan het getal.")
        if not kaart.assen and punt == (d["x"], kaart.rijen + 1 - d["y"]):
            return "rij_van_boven", "Je telde de rijen van boven. Rij 1 staat onderaan."
        return None


# ---- schaal ------------------------------------------------------------------------------------------------

def schaal_tekst(n):
    return f"1 : {fmt(D(n))}"


class Schaal(_Meetkunde):
    id = "wiskunde.meetkunde.schaal"
    naam = "Schaal"
    omschrijving = "kaart en werkelijkheid: 1 : 1000"
    denkfouten = {"schaal_niet_omgezet": "cm niet omgezet naar m of km (of omgekeerd)",
                  "schaal_omgekeerd": "gedeeld in plaats van vermenigvuldigd (of omgekeerd)"}

    def maak_met(self, p, rng, data=None):
        soort = self.soort(p, rng, data)
        schaal = rng.choice(p["schalen"])
        eenheid, per = ("km", 100000) if schaal >= 50000 else ("m", 100)
        cm = rng.randint(2, 12)
        echt = D(cm * schaal) / per  # in m of km
        d = {"soort": soort, "onderwerp": soort, "schaal": schaal, "cm": cm, "eenheid": eenheid, "per": per}
        if soort == "naar_echt":
            return Vraag(self.id, f"{self.id}:naar_echt:{schaal}:{cm}",
                         f"Een kaart heeft schaal {schaal_tekst(schaal)}. Een weg is er {cm} cm lang. "
                         f"Hoe lang is de weg in het echt (in {eenheid})?", echt, eenheid=eenheid, data=d)
        if soort == "naar_kaart":
            return Vraag(self.id, f"{self.id}:naar_kaart:{schaal}:{cm}",
                         f"Een weg is in het echt {fmt(echt)} {eenheid} lang. Hoeveel cm is dat op een kaart met "
                         f"schaal {schaal_tekst(schaal)}?", D(cm), eenheid="cm", data=d)
        return Vraag(self.id, f"{self.id}:schaal_zoeken:{schaal}:{cm}",
                     f"Op een kaart is {cm} cm in het echt {fmt(echt)} {eenheid}. Wat is de schaal? (typ bv. 1:500)",
                     D(schaal), data=d, verwacht_tekst=schaal_tekst(schaal))

    klad = "ja"

    def oplossing(self, v):
        d = v.data
        n, cm, e = d["schaal"], d["cm"], d["eenheid"]
        echt_cm = cm * n
        echt = fmt(D(echt_cm) / d["per"])
        if d["soort"] == "naar_echt":
            return oplossing_van(f"{cm} × {n} = {echt_cm}", f"{echt_cm} cm = {echt} {e}")
        if d["soort"] == "naar_kaart":
            return oplossing_van(f"{echt} {e} = {echt_cm} cm", f"{echt_cm} : {n} = {cm}")
        return oplossing_van(f"{echt} {e} = {echt_cm} cm", f"{echt_cm} : {cm} = {n}")

    def lees(self, tekst):
        t = (tekst or "").replace(" ", "")
        t = t[2:] if t.startswith("1:") else t
        return lees_getal(t)

    def uitleg(self, v):
        d = v.data
        n, cm, e = d["schaal"], d["cm"], d["eenheid"]
        echt_cm = cm * n
        omzet = f"{fmt(D(echt_cm))} cm = {fmt(D(echt_cm) / d['per'])} {e}"
        if d["soort"] == "naar_echt":
            return [f"{schaal_tekst(n)}: 1 cm op de kaart is {fmt(D(n))} cm in het echt.",
                    f"{cm} × {fmt(D(n))} = {omzet}."]
        if d["soort"] == "naar_kaart":
            return [f"Zet eerst om naar cm: {fmt(D(echt_cm) / d['per'])} {e} = {fmt(D(echt_cm))} cm.",
                    f"Deel door {fmt(D(n))}: {fmt(D(echt_cm))} : {fmt(D(n))} = {cm} cm op de kaart."]
        return [f"Zet om naar cm: {fmt(D(echt_cm) / d['per'])} {e} = {fmt(D(echt_cm))} cm.",
                f"{fmt(D(echt_cm))} : {cm} = {fmt(D(n))}, dus 1 cm op de kaart = {fmt(D(n))} cm: {schaal_tekst(n)}."]

    def tip(self, v):
        return f"{schaal_tekst(v.data['schaal'])} betekent: 1 cm op de kaart = {fmt(D(v.data['schaal']))} cm in het echt."

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        d = v.data
        n, cm, per = D(d["schaal"]), D(d["cm"]), d["per"]
        if d["soort"] == "naar_echt":
            if getal == cm * n:
                return "schaal_niet_omgezet", f"Dat zijn cm. Zet nog om naar {d['eenheid']}."
            if getal in (cm / n, cm / n / per):
                return "schaal_omgekeerd", "Je deelde. In het echt is alles groter: vermenigvuldig met de schaal."
        elif d["soort"] == "naar_kaart":
            if getal == cm / per or getal == cm * per:
                return "schaal_niet_omgezet", f"Zet eerst de {d['eenheid']} om naar cm."
            if getal == cm * n * n:
                return "schaal_omgekeerd", "Op de kaart is alles kleiner: deel door de schaal."
        elif getal in (n / per, n * per):
            return "schaal_niet_omgezet", "Zet eerst alles om naar cm."
        return None


# twee spiekbrieven: oppervlakte en formules (in het menu bij Meten), en hoeken, coördinaten en schaal (Meetkunde)
SPIEKBRIEF_OPPERVLAKTE = [
    ("OPPERVLAKTE EN OMTREK", "accent"),
    ("  Oppervlakte = hoeveel vakjes van 1 cm² erin passen (cm²).", ""),
    ("  Omtrek = de lengte van de rand rondom (cm).", ""),
    ("", ""),
    ("FORMULES", "accent"),
    ("  rechthoek    opp = l × b             omtrek = 2 × (l + b)", ""),
    ("  vierkant     opp = z × z             omtrek = 4 × z", ""),
    ("  driehoek     opp = b × h : 2", ""),
    ("  parallellogram  opp = b × h          trapezium  opp = (B + b) × h : 2", ""),
    ("  cirkel       omtrek = 2 × π × r      opp = π × r × r", ""),
    ("               (π ≈ 3,14; straal r = de helft van de diameter d)", ""),
    ("  balk         volume = l × b × h      kubus  volume = z × z × z", ""),
]

SPIEKBRIEF_MEETKUNDE = [
    ("HOEKEN", "accent"),
    ("  scherp: kleiner dan 90°    recht = 90°    stomp: tussen 90° en 180°", ""),
    ("  gestrekt = 180° (een rechte lijn)    vol = 360° (helemaal rond)", ""),
    ("  De 3 hoeken van een driehoek zijn samen 180°. Nevenhoeken samen: 180°.", ""),
    ("", ""),
    ("COÖRDINATEN", "accent"),
    ("  Schatkaart: eerst de letter (kolom), dan het getal (rij): C4.", ""),
    ("  Rij 1 staat onderaan.", ""),
    ("  Assenstelsel: eerst x (horizontaal), dan y (verticaal): (3, −2).", ""),
    ("", ""),
    ("SCHAAL", "accent"),
    ("  1 : 1000 = 1 cm op de kaart is 1000 cm (10 m) in het echt.", ""),
    ("  Kaart → echt: × de schaal.   Echt → kaart: : de schaal.", ""),
    ("  Let op de eenheden: 100 cm = 1 m, 100 000 cm = 1 km.", ""),
]

ROOSTER = Rooster()
FORMULES = Formules()
HOEKEN = Hoeken()
COORDINATEN = Coordinaten()
SCHAAL = Schaal()
ALLE = [ROOSTER, FORMULES, HOEKEN, COORDINATEN, SCHAAL]
