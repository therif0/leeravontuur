"""De klok: een wijzerklok lezen en zetten, tijden in Vlaamse woorden, de 24-uursnotatie, later en vroeger.

Een tijdstip is overal een aantal minuten na middernacht (0 … 1439), zoals in kern/wiskunde/grootheden.py.
Een wijzerklok toont maar 12 uur: daar telt 3.15 even goed als 15.15.
"""

import re
from decimal import Decimal

from ..klad import oplossing_van
from ..modellen import Wijzerklok
from ..onderwerp import Onderwerp, Vraag
from .grootheden import duur_tekst, klok_tekst, lees_klok

D = Decimal
GETALLEN = ["twaalf", "een", "twee", "drie", "vier", "vijf", "zes", "zeven", "acht", "negen", "tien", "elf", "twaalf"]
WOORD = {w: i for i, w in enumerate(GETALLEN) if i} | {"één": 1, "twintig": 20, "kwart": 15}
DAGDELEN = [(0, 6, "'s nachts"), (6, 12, "'s morgens"), (12, 18, "'s middags"), (18, 24, "'s avonds")]


def uur12(uur):
    """0..23 → 1..12."""
    return (uur - 1) % 12 + 1


def woorden(minuten):
    """Een tijdstip in Vlaamse woorden, zoals je het op een wijzerklok leest: 205 → 'vijf voor half vier'.
    Alleen voor veelvouden van 5 minuten; anders bv. 'drie uur zeventien' (met cijfers: '3 uur 17')."""
    u, m = divmod(int(minuten) % 720, 60)
    nu, straks = GETALLEN[uur12(u)], GETALLEN[uur12(u + 1)]
    if m % 5:
        return f"{uur12(u)} uur {m}"
    return {0: f"{nu} uur", 5: f"vijf over {nu}", 10: f"tien over {nu}", 15: f"kwart over {nu}",
            20: f"tien voor half {straks}", 25: f"vijf voor half {straks}", 30: f"half {straks}",
            35: f"vijf over half {straks}", 40: f"tien over half {straks}", 45: f"kwart voor {straks}",
            50: f"tien voor {straks}", 55: f"vijf voor {straks}"}[m]


def _getal(w):
    if w.isdigit():
        return int(w)
    return WOORD.get(w)


def lees_woorden(tekst):
    """'vijf voor half vier', '5 voor half 4', 'kwart over drie', 'drie uur', 'twintig over drie' → minuten
    (0 … 719), of None. Ook een tijd in cijfers ('3.25') mag."""
    t = re.sub(r"[^\wé ]", " ", (tekst or "").lower()).split()
    t = [w for w in t if w not in ("het", "is", "om", "u")]
    if not t:
        return None
    if all(c.isdigit() or c in ".:" for c in "".join((tekst or "").split()).rstrip("u")):
        k = lees_klok(tekst)
        return None if k is None else k % 720
    try:
        if t[-1] == "uur" and len(t) == 2:                       # drie uur
            return uur12(_getal(t[0])) % 12 * 60
        if len(t) == 3 and t[1] == "uur":                       # 3 uur 17
            return (uur12(_getal(t[0])) % 12) * 60 + int(t[2])
        if len(t) == 2 and t[0] == "half":                      # half vier
            return (uur12(_getal(t[1])) - 1) % 12 * 60 + 30
        if len(t) == 3 and t[1] in ("over", "voor"):            # kwart over drie, tien voor vier
            m, u = _getal(t[0]), uur12(_getal(t[2]))
            if m is None or not 0 < m < 30:
                return None
            return (u % 12 * 60 + (m if t[1] == "over" else -m)) % 720
        if len(t) == 4 and t[1] in ("over", "voor") and t[2] == "half":  # vijf voor half vier
            m, u = _getal(t[0]), uur12(_getal(t[3]))
            if m is None or not 0 < m < 30:
                return None
            return ((u - 1) % 12 * 60 + 30 + (m if t[1] == "over" else -m)) % 720
    except (TypeError, ValueError):
        return None
    return None


def dagdeel(minuten):
    u = int(minuten) // 60 % 24
    return next(naam for van, tot, naam in DAGDELEN if van <= u < tot)


SPIEKBRIEF = [
    ("DE WIJZERKLOK", "accent"),
    ("  De korte wijzer = het uur.  De lange wijzer = de minuten.", ""),
    ("  Staat de korte wijzer tussen 3 en 4? Dan is het nog 3 uur (en iets).", ""),
    ("  De lange wijzer op 1 = 5 minuten, op 2 = 10, op 3 = 15 … (tel per 5).", ""),
    ("", ""),
    ("IN WOORDEN", "accent"),
    ("  3.00 drie uur          3.30 half vier  (half vóór vier!)", ""),
    ("  3.05 vijf over drie    3.35 vijf over half vier", ""),
    ("  3.15 kwart over drie   3.40 tien over half vier", ""),
    ("  3.20 tien voor half vier   3.45 kwart voor vier", ""),
    ("  3.25 vijf voor half vier   3.55 vijf voor vier", ""),
    ("", ""),
    ("24 UUR", "accent"),
    ("  Na de middag tel je 12 bij het uur: 3.15 's middags = 15.15 u.", ""),
    ("  00.00 u = middernacht   12.00 u = de middag", ""),
    ("", ""),
    ("LATER EN VROEGER", "accent"),
    ("  Een uur heeft 60 minuten! Tel in stapjes tot het volle uur.", ""),
    ("  8.50 + 20 min: tot 9.00 is 10 min, nog 10 → 9.10.", ""),
    ("  9.10 − 25 min: terug tot 9.00 is 10 min, nog 15 terug → 8.45.", ""),
]


def klok12(t):
    """Een tijd op de wijzerklok: 12 uur in plaats van 0 uur (0.55 → 12.55 u)."""
    u, m = divmod(int(t) % 720, 60)
    return f"{uur12(u)}.{m:02d} u"


def lange_wijzer(m):
    """Hoe je de minuten afleest: per 5 tellen, en dan de streepjes erbij."""
    cijfer, rest = m // 5 or 12, m % 5
    if m == 0:
        return "De lange wijzer staat op de 12: een vol uur."
    if rest == 0:
        return f"De lange wijzer staat op de {cijfer}: {cijfer} × 5 = {m} minuten."
    streepjes = f"{rest} streepje{'s' if rest > 1 else ''}"
    if m < 5:
        return f"De lange wijzer staat {streepjes} na de 12: {m} minuten."
    return f"De lange wijzer staat {streepjes} na de {cijfer}: {cijfer} × 5 = {m - rest}, en nog {rest} = {m} minuten."


class Klok(Onderwerp):
    id = "wiskunde.eenheden.klok"
    naam = "De klok"
    omschrijving = "de wijzerklok lezen en zetten, tijden in woorden, 24 uur, later en vroeger"
    denkfouten = {"klok_wijzers": "uurwijzer en minutenwijzer verwisseld",
                  "klok_half": "'half vier' gelezen als 4.30 (half vier = 3.30)",
                  "klok_uur_te_ver": "het volgende uur genomen (de uurwijzer staat er nog maar bijna)",
                  "klok_24": "24-urennotatie: 12 niet (of te veel) bij het uur opgeteld",
                  "klok_uur_vergeten": "60 minuten niet omgezet in een uur",
                  "klok_richting": "later en vroeger verwisseld",
                  "klok_met_100": "gerekend alsof een uur 100 minuten heeft"}
    vast = ("soort",)

    def onderwerp_van_sleutel(self, sleutel):
        delen = sleutel.split(":")
        return delen[1] if len(delen) >= 3 and delen[0] == self.id else None

    def kies_onderwerp(self, gewichten, p, rng):
        w = [gewichten.get(s, 1.0) for s in p["soorten"]]
        return {"soort": rng.choices(p["soorten"], weights=w, k=1)[0]}

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and data.get("soort") in p["soorten"] else rng.choice(p["soorten"])
        stap = p["stap"]
        d = {"soort": soort, "onderwerp": soort}
        uur = rng.randint(1, 12)
        minuut = rng.randrange(0, 60, stap)
        t = uur % 12 * 60 + minuut
        if soort == "lezen":
            d["t"] = t
            return Vraag(self.id, f"{self.id}:lezen:{t}", "Hoe laat is het op de klok?", D(t), data=d,
                         invoer="klok", model=Wijzerklok(t), verwacht_tekst=klok12(t))
        vijf = uur % 12 * 60 + rng.randrange(0, 60, max(5, stap))
        if soort == "woorden_naar":
            d["t"] = vijf
            return Vraag(self.id, f"{self.id}:woorden_naar:{vijf}", f"Hoe schrijf je '{woorden(vijf)}' in cijfers?",
                         D(vijf), data=d, invoer="klok", verwacht_tekst=klok12(vijf))
        if soort == "naar_woorden":
            d["t"] = vijf
            return Vraag(self.id, f"{self.id}:naar_woorden:{vijf}", f"Hoe zeg je {klok12(vijf)} in woorden?",
                         D(vijf), data=d, invoer="klokwoord", model=Wijzerklok(vijf), verwacht_tekst=woorden(vijf))
        if soort == "zetten":
            doel = vijf if rng.random() < 0.6 else t
            d["t"] = doel
            vraag = (f"Zet de klok op {woorden(doel)}." if doel % 5 == 0 and rng.random() < 0.6
                     else f"Zet de klok op {klok12(doel)}.")
            start = rng.randrange(0, 720, 5)
            return Vraag(self.id, f"{self.id}:zetten:{doel}", vraag, D(doel), data={**d, "start": start},
                         invoer="wijzers", model=Wijzerklok(start), verwacht_tekst=klok12(doel))
        if soort == "24uur":
            t24 = rng.randrange(13 * 60, 24 * 60, stap)
            d["t"] = t24
            deel = dagdeel(t24)
            return Vraag(self.id, f"{self.id}:24uur:{t24}",
                         f"Het is {deel}. Schrijf dat zoals op een digitale klok (24-urennotatie).", D(t24),
                         data=d, invoer="klok",
                         model=Wijzerklok(t24), verwacht_tekst=klok_tekst(t24))
        # later of vroeger
        begin = rng.randrange(7 * 60, 21 * 60, stap)
        duur = rng.randrange(max(5, stap * 3), p["max_duur"] + 1, max(5, stap))
        if p.get("middernacht") and rng.random() < 0.25:
            begin = rng.randrange(22 * 60, 24 * 60, 5)
        d.update(begin=begin, duur=duur)
        eind = (begin + duur if soort == "later" else begin - duur) % 1440
        woord = "later" if soort == "later" else "vroeger"
        return Vraag(self.id, f"{self.id}:{soort}:{begin}{'+' if soort == 'later' else '-'}{duur}",
                     f"Het is {klok_tekst(begin)}. Hoe laat is het {duur_tekst(duur)} {woord}?", D(eind), data=d,
                     invoer="klok", model=Wijzerklok(begin), verwacht_tekst=klok_tekst(eind))

    # ---- lezen en nakijken ---------------------------------------------------------------------------
    klad = "ja"  # maar alleen bij later, vroeger en 24 uur (klad_voor)

    def klad_voor(self, v):
        """Rekenen met de klok krijgt een klad; de klok lezen, zetten of in woorden niet."""
        return "ja" if v.data.get("soort") in ("later", "vroeger", "24uur") else None

    def oplossing(self, v):
        d, s = v.data, v.data["soort"]
        if s == "24uur":
            return oplossing_van(f"{klok12(d['t'] - 720)} + 12 u = {klok_tekst(d['t'])}")
        b, du, eind = d["begin"], d["duur"], int(v.antwoord)
        if s == "later":
            tot = (60 - b % 60) % 60  # eerst tot het volle uur
            if 0 < tot < du:
                return oplossing_van(f"{klok_tekst(b)} + {tot} min = {klok_tekst((b + tot) % 1440)}",
                                     f"{klok_tekst((b + tot) % 1440)} + {du - tot} min = {klok_tekst(eind)}")
            return oplossing_van(f"{klok_tekst(b)} + {du} min = {klok_tekst(eind)}")
        terug = b % 60  # eerst terug tot het volle uur
        if 0 < terug < du:
            return oplossing_van(f"{klok_tekst(b)} − {terug} min = {klok_tekst(b - terug)}",
                                 f"{klok_tekst(b - terug)} − {du - terug} min = {klok_tekst(eind)}")
        return oplossing_van(f"{klok_tekst(b)} − {du} min = {klok_tekst(eind)}")

    def lees_vraag(self, v, tekst):
        if v.invoer == "klokwoord":
            return lees_woorden(tekst)
        if v.invoer == "wijzers":
            return lees_klok(tekst) if isinstance(tekst, str) else tekst
        return lees_klok(tekst)

    def nakijken(self, v, getal):
        if getal is None:
            return False
        s = v.data["soort"]
        if s == "24uur":
            return getal == v.antwoord
        if s in ("later", "vroeger"):  # na 13 uur in 24 uur schrijven: 19.25, niet 7.25
            return getal == v.antwoord or (v.antwoord < 780 and D(getal) % 720 == v.antwoord % 720)
        return D(getal) % 720 == v.antwoord % 720  # een wijzerklok toont 12 uur

    def diagnose(self, v, getal):
        if getal is None or self.nakijken(v, getal):
            return None
        s, d = v.data["soort"], v.data
        t, g = int(v.antwoord) % 720, int(getal) % 720
        u, m = divmod(t, 60)
        if s in ("lezen", "zetten", "naar_woorden", "woorden_naar"):
            omgewisseld = (m // 5) % 12 * 60 + (u % 12) * 5  # de lange wijzer als uur, de korte als minuten
            if m % 5 == 0 and g == omgewisseld != t:
                return "klok_wijzers", "De korte wijzer is het uur, de lange wijzer de minuten. Je wisselde ze om."
            volgend = GETALLEN[uur12(u + 1)]
            if s == "woorden_naar" and 20 <= m <= 40 and g == (t + 60) % 720:  # "vijf voor half vier" → 4.25
                if m == 30:
                    return "klok_half", f"Half {volgend} is een half uur vóór {volgend}: {klok12(t)}."
                return "klok_half", f"'... half {volgend}' gaat over het halfuur vóór {volgend} uur, dus nog " \
                                    f"{uur12(u)} uur en iets."
            if s == "naar_woorden" and 20 <= m <= 40 and g == (t - 60) % 720:  # 3.25 → "vijf voor half drie"
                return "klok_half", f"Vanaf {uur12(u)}.20 tel je vanaf half {volgend} (een half uur vóór {volgend}): " \
                                    f"{klok12(t)} = {woorden(t)}."
            if m >= 30 and g == (t + 60) % 720:
                if s in ("naar_woorden", "woorden_naar"):
                    return "klok_half", f"'... half {volgend}' gaat over het halfuur vóór {volgend} uur, dus nog " \
                                        f"{uur12(u)} uur en iets."
                return "klok_uur_te_ver", (f"De korte wijzer staat bijna op {uur12(u + 1)}, maar nog niet: het is nog "
                                           f"{uur12(u)} uur en {m} minuten.")
            return None
        if s == "24uur":
            if getal == v.antwoord - 720:
                return "klok_24", f"Is het {dagdeel(v.antwoord)}? Dan tel je 12 bij het uur: {uur12(u)} + 12 = {u + 12}."
            return None
        b, du = d["begin"], d["duur"]
        ander = (b - du if s == "later" else b + du) % 1440
        if getal % 720 == ander % 720:
            return "klok_richting", "Later = erbij tellen, vroeger = terugtellen." if s == "later" else \
                "Vroeger = terugtellen, niet erbij."
        kl = lambda x: (x // 60) * 100 + x % 60  # 8.50 → 850
        honderd = kl(b) + (du // 60) * 100 + du % 60 if s == "later" else kl(b) - (du // 60) * 100 - du % 60
        if getal % 720 == (v.antwoord - 60) % 720 or (getal % 720 == (v.antwoord + 60) % 720 and s == "vroeger"):
            return "klok_uur_vergeten", "Over het volle uur heen: na 59 minuten komt er een uur bij (of eraf)."
        if honderd % 100 >= 60 and getal == honderd:
            return "klok_met_100", "Een uur heeft 60 minuten, geen 100. Tel in stapjes tot het volle uur."
        return None

    def uitleg(self, v):
        s, d = v.data["soort"], v.data
        t = int(v.antwoord)
        if s in ("lezen", "zetten"):
            u, m = divmod(t % 720, 60)
            return [f"De korte wijzer staat bij {uur12(u)} (of net erna): {uur12(u)} uur.", lange_wijzer(m),
                    f"Het is {klok12(t)}" + (f" ({woorden(t)})." if t % 5 == 0 else ".")]
        if s in ("naar_woorden", "woorden_naar"):
            return [f"{klok12(t)} = {woorden(t)}.", "Let op: half vier = een half uur vóór vier = 3.30."]
        if s == "24uur":
            return [f"Is het {dagdeel(t)}? Dan tel je 12 bij het uur: {uur12(t // 60)} + 12 = {t // 60}.",
                    f"Het is {klok_tekst(t)}."]
        b, du = d["begin"], d["duur"]
        if s == "later":
            tot_uur = (60 - b % 60) % 60
            if 0 < tot_uur <= du:
                return [f"Van {klok_tekst(b)} tot {klok_tekst(b + tot_uur)} is {tot_uur} min.",
                        f"Nog {duur_tekst(du - tot_uur)} erbij: {klok_tekst(b + du)}."]
            return [f"{klok_tekst(b)} + {duur_tekst(du)} = {klok_tekst(b + du)}."]
        terug = b % 60
        if 0 < terug <= du:
            return [f"Van {klok_tekst(b)} terug tot {klok_tekst(b - terug)} is {terug} min.",
                    f"Nog {duur_tekst(du - terug)} terug: {klok_tekst(b - du)}."]
        return [f"{klok_tekst(b)} − {duur_tekst(du)} = {klok_tekst(b - du)}."]

    def tip(self, v):
        s = v.data["soort"]
        if s in ("lezen", "zetten"):
            return "Eerst de korte wijzer (het uur), dan de lange (tel per 5 minuten)."
        if s in ("naar_woorden", "woorden_naar"):
            return "Half vier = een half uur vóór vier. Na half: 'vijf over half', voor half: 'vijf voor half'."
        if s == "24uur":
            return "Na de middag tel je 12 bij het uur."
        return "Tel in stapjes tot het volle uur. Een uur heeft 60 minuten, geen 100!"

    def spiekbrief(self):
        return SPIEKBRIEF


KLOK = Klok()
