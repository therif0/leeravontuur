"""Cijferen: optellen, aftrekken en vermenigvuldigen onder elkaar in een rooster (met onthouden-rij),
en de staartdeling stap voor stap (deel, vermenigvuldig, trek af, haal neer).
"""

import re
from decimal import Decimal

from ..getal import fmt, lees_getal
from ..modellen import Rooster, Staartdeling, Stap
from ..onderwerp import Onderwerp, Vraag
from .getallen import AFK, NAAM, _getal

D = Decimal


def _cijfers(x):
    """{macht: cijfer} van |x|, bv. 12,5 → {1: 1, 0: 2, -1: 5}."""
    tekst = format(abs(D(x)).normalize(), "f")
    geheel, _, na = tekst.partition(".")
    uit = {len(geheel) - 1 - i: int(c) for i, c in enumerate(geheel)}
    uit.update({-1 - i: int(c) for i, c in enumerate(na)})
    if geheel == "0" and na:
        uit.pop(0, None)
        uit[0] = 0
    return uit


def _decimalen(x):
    return max(0, -D(x).normalize().as_tuple().exponent)


def _geheel_lengte(x):
    return len(format(abs(D(x)).normalize(), "f").partition(".")[0])


def _uit_cijfers(cijfers):
    return sum((D(c).scaleb(k) for k, c in cijfers.items()), D(0))


def _kol(k):
    return AFK.get(k, f"10^{k}")


def _som_tekst(cijfers, onth):
    """'7 + 5 + 1 (onthouden)'."""
    delen = [str(c) for c in cijfers] + ([f"{onth} (onthouden)"] if onth else [])
    return " + ".join(delen)


SPIEKBRIEF = [
    ("CIJFEREN ONDER ELKAAR", "accent"),
    ("  Zet eenheden onder eenheden, komma onder komma.", ""),
    ("  Begin rechts, bij de kleinste plaats, en werk naar links.", ""),
    ("", ""),
    ("OPTELLEN", "accent"),
    ("  Is een kolom samen 10 of meer? Schrijf de eenheden, onthoud de tientallen.", ""),
    ("  7 + 5 = 12: schrijf 2, onthoud 1 (bovenaan in de kolom links).", ""),
    ("", ""),
    ("AFTREKKEN", "accent"),
    ("  Is het bovenste cijfer te klein? Leen 1 bij de kolom links (die wordt 1 kleiner).", ""),
    ("  Nooit 'de kleinste van de grootste': 2 − 7 kan niet, dus 12 − 7 = 5.", ""),
    ("", ""),
    ("VERMENIGVULDIGEN", "accent"),
    ("  Elk cijfer van het onderste getal geeft een rij. Rij 2 begint met een 0.", ""),
    ("  Tel de rijen op. Komma? Tel alle cijfers na de komma samen.", ""),
    ("", ""),
    ("STAARTDELING", "accent"),
    ("  Deel → vermenigvuldig → trek af → haal neer. En opnieuw.", ""),
    ("  De rest moet altijd kleiner zijn dan de deler.", ""),
    ("  Controle: quotiënt × deler + rest = deeltal.", ""),
]


class _Cijferen(Onderwerp):
    def spiekbrief(self):
        return SPIEKBRIEF

    def tip(self, v):
        return "Begin rechts. Druk ? terwijl je in een vakje staat voor hulp bij die kolom."


# ---- optellen ----------------------------------------------------------------------------------------

def optel_kolommen(getallen):
    """Per kolom (van rechts naar links): (macht, cijfers, onthouden_in, som, schrijf, onthouden_uit)."""
    cs = [_cijfers(g) for g in getallen]
    laagste = min(min(c) for c in cs)
    hoogste = max(max(c) for c in cs)
    uit, onth, k = [], 0, laagste
    while k <= hoogste or onth:
        cijfers = [c[k] for c in cs if k in c]
        som = sum(cijfers) + onth
        uit.append((k, cijfers, onth, som, som % 10, som // 10))
        onth = som // 10
        k += 1
    return uit


class Optellen(_Cijferen):
    id = "wiskunde.cijferen.optellen"
    naam = "Cijferend optellen"
    spiek_kop = "OPTELLEN"
    omschrijving = "onder elkaar, met onthouden"
    denkfouten = {"onthouden_vergeten": "onthouden vergeten bij het optellen"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else \
            ("komma" if p["decimalen"] and rng.random() < 0.5 else "natuurlijk")
        dec = max(1, p["decimalen"]) if soort == "komma" else 0
        termen = rng.randint(2, p["termen"])
        for _ in range(60):
            getallen = [_getal(rng, rng.randint(max(1, p["cijfers"] - 2), p["cijfers"]), rng.randint(0, dec),
                               verschillend=False).normalize() for _ in range(termen)]
            if dec and not any(_decimalen(g) for g in getallen):
                continue
            if sum(o[5] for o in optel_kolommen(getallen)) >= 1:
                break
        getallen.sort(reverse=True)
        som = sum(getallen)
        rechts = max(_decimalen(g) for g in getallen)
        breedte = max(_geheel_lengte(g) for g in getallen) + 1 + rechts
        teksten = [fmt(g) for g in getallen]
        model = Rooster("+", teksten, breedte, rechts, verwacht=[fmt(som)])
        d = {"op": "+", "termen": [str(g) for g in getallen], "soort": soort,
             "onderwerp": "kommagetallen" if soort == "komma" else "natuurlijke getallen"}
        return Vraag(self.id, f"{self.id}:{'+'.join(teksten)}", " + ".join(teksten) + " =", som, data=d,
                     invoer="rooster", model=model)

    def getallen(self, v):
        return [D(t) for t in v.data["termen"]]

    def uitleg(self, v):
        regels = ["Begin rechts en tel elke kolom op:"]
        for k, cijfers, onth, som, schrijf, uit in optel_kolommen(self.getallen(v)):
            deel = _som_tekst(cijfers, onth)
            regels.append(f"  {_kol(k)}: {deel} = {som}" + (f" → schrijf {schrijf}, onthoud {uit}" if uit else ""))
        if len(regels) > 6:  # niet te lang op het scherm: de kolommen met onthouden zijn het belangrijkst
            regels = regels[:1] + [r for r in regels[1:] if "onthoud" in r][:4]
        regels.append(f"Samen: {v.verwacht}.")
        return regels

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        kols = optel_kolommen(self.getallen(v))
        zonder = sum(D(sum(cijfers) % 10).scaleb(k) for k, cijfers, *_ in kols)
        if getal == zonder:
            return "onthouden_vergeten", "Je vergat wat je moest onthouden. Schrijf het bovenaan in de kolom links."
        gegeven, verwacht = _cijfers(getal), _cijfers(v.antwoord)
        verschil = [k for k in set(gegeven) | set(verwacht) if gegeven.get(k, 0) != verwacht.get(k, 0)]
        onth_in = {k: o for k, _, o, *_ in kols}
        if verschil and all(onth_in.get(k) and gegeven.get(k, 0) == (verwacht.get(k, 0) - 1) % 10 for k in verschil):
            return "onthouden_vergeten", "In een kolom vergat je het getal dat je moest onthouden (+1)."
        return None

    def kolom_hulp(self, v, rij, kolom):
        k = v.model.macht(kolom)
        for kk, cijfers, onth, som, schrijf, uit in optel_kolommen(self.getallen(v)):
            if kk == k:
                deel = _som_tekst(cijfers, onth)
                if len(cijfers) + bool(onth) == 1:
                    return f"Kolom {_kol(k)}: hier staat alleen {deel}, dus schrijf {schrijf}."
                return (f"Kolom {_kol(k)}: {deel} = {som}: schrijf {schrijf}" +
                        (f" en onthoud {uit} (zet die {uit} bovenaan in de kolom links)." if uit else "."))
        return "In deze kolom komt niets: daar staan geen cijfers en je hoeft niets meer te onthouden."

    def onderwerp_van_sleutel(self, sleutel):
        if not sleutel.startswith(self.id + ":"):
            return None
        return "kommagetallen" if "," in sleutel else "natuurlijke getallen"


# ---- aftrekken ---------------------------------------------------------------------------------------

def aftrek_kolommen(a, b):
    """Per kolom (van rechts naar links): (macht, boven, onder, geleend_in, leent, schrijf)."""
    ca, cb = _cijfers(a), _cijfers(b)
    laagste = min(min(ca), min(cb))
    uit, leen = [], 0
    for k in range(laagste, max(ca) + 1):
        boven, onder = ca.get(k, 0), cb.get(k, 0)
        nu = boven - leen
        leent = 1 if nu < onder else 0
        uit.append((k, boven, onder, leen, leent, nu + 10 * leent - onder))
        leen = leent
    return uit


class Aftrekken(_Cijferen):
    id = "wiskunde.cijferen.aftrekken"
    naam = "Cijferend aftrekken"
    spiek_kop = "AFTREKKEN"
    omschrijving = "onder elkaar, met lenen"
    denkfouten = {"kleinste_van_grootste": "per kolom de kleinste van de grootste afgetrokken",
                  "lenen_vergeten": "geleend, maar de kolom links niet 1 kleiner gemaakt"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else \
            ("komma" if p["decimalen"] and rng.random() < 0.5 else "natuurlijk")
        dec = max(1, p["decimalen"]) if soort == "komma" else 0
        for _ in range(60):
            a = _getal(rng, rng.randint(max(2, p["cijfers"] - 1), p["cijfers"]), rng.randint(0, dec),
                       verschillend=False).normalize()
            b = _getal(rng, rng.randint(max(1, _geheel_lengte(a) - 2), _geheel_lengte(a)), rng.randint(0, dec),
                       verschillend=False).normalize()
            if b >= a or (dec and not (_decimalen(a) or _decimalen(b))):
                continue
            if sum(o[4] for o in aftrek_kolommen(a, b)) >= 1:
                break
        rechts = max(_decimalen(a), _decimalen(b))
        breedte = _geheel_lengte(a) + rechts
        teksten = [fmt(a), fmt(b)]
        model = Rooster("−", teksten, breedte, rechts, verwacht=[fmt(a - b)])
        d = {"op": "−", "a": str(a), "b": str(b), "soort": soort,
             "onderwerp": "kommagetallen" if soort == "komma" else "natuurlijke getallen"}
        return Vraag(self.id, f"{self.id}:{teksten[0]}-{teksten[1]}", f"{teksten[0]} − {teksten[1]} =", a - b, data=d,
                     invoer="rooster", model=model)

    def ab(self, v):
        return D(v.data["a"]), D(v.data["b"])

    def uitleg(self, v):
        regels = ["Begin rechts. Is het bovenste cijfer te klein, leen dan 1 bij de kolom links:"]
        for k, boven, onder, leen, leent, schrijf in aftrek_kolommen(*self.ab(v)):
            if leent:
                regels.append(f"  {_kol(k)}: {boven - leen} − {onder} kan niet → leen: "
                              f"{boven - leen + 10} − {onder} = {schrijf}")
        regels.append(f"Uitkomst: {v.verwacht}. Controle: {v.verwacht} + {fmt(self.ab(v)[1])} = {fmt(self.ab(v)[0])}.")
        return regels[:6]

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        kols = aftrek_kolommen(*self.ab(v))
        if getal == sum(D(abs(boven - onder)).scaleb(k) for k, boven, onder, *_ in kols):
            return ("kleinste_van_grootste", "Je trok telkens de kleinste van de grootste af. Is het bovenste cijfer "
                    "kleiner, dan moet je lenen bij de kolom links.")
        if getal == sum(D((boven - onder) % 10).scaleb(k) for k, boven, onder, *_ in kols):
            return "lenen_vergeten", "Je leende wel, maar vergat de kolom links daarna 1 kleiner te maken."
        return None

    def kolom_hulp(self, v, rij, kolom):
        k = v.model.macht(kolom)
        for kk, boven, onder, leen, leent, schrijf in aftrek_kolommen(*self.ab(v)):
            if kk == k:
                begin = f"Kolom {_kol(k)}: " + (f"de {boven} werd {boven - 1} (je leende er 1). " if leen else "")
                nu = boven - leen
                if leent:
                    return begin + f"{nu} − {onder} kan niet: leen 1 bij de kolom links. {nu + 10} − {onder} = {schrijf}."
                return begin + f"{nu} − {onder} = {schrijf}."
        return "In deze kolom komt niets."

    def onderwerp_van_sleutel(self, sleutel):
        if not sleutel.startswith(self.id + ":"):
            return None
        return "kommagetallen" if "," in sleutel else "natuurlijke getallen"


# ---- vermenigvuldigen --------------------------------------------------------------------------------

def maal_rij(A, cijfer, r):
    """Per kolom van rechts naar links voor A × cijfer, r plaatsen opgeschoven:
    (macht, cijfer van A of None, onthouden_in, product, schrijf, onthouden_uit)."""
    uit = [(k, None, 0, 0, 0, 0) for k in range(r)]
    onth = 0
    for i, c in enumerate(reversed(str(A))):
        prod = int(c) * cijfer + onth
        uit.append((i + r, int(c), onth, prod, prod % 10, prod // 10))
        onth = prod // 10
    if onth:
        uit.append((len(str(A)) + r, None, onth, onth, onth, 0))
    return uit


class Vermenigvuldigen(_Cijferen):
    id = "wiskunde.cijferen.vermenigvuldigen"
    naam = "Cijferend vermenigvuldigen"
    spiek_kop = "VERMENIGVULDIGEN"
    omschrijving = "onder elkaar, ook met 2 cijfers en kommagetallen"
    denkfouten = {"niet_opgeschoven": "de tweede rij niet opgeschoven (de 0 vergeten)",
                  "komma_product": "de komma op de verkeerde plaats in het product"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soort = data["soort"] if data and "soort" in data else \
            ("komma" if p["decimalen"] and rng.random() < 0.4 else "natuurlijk")
        cb = rng.randint(1, p["cijfers_b"])
        ca = rng.randint(max(2, p["cijfers_a"] - 1), p["cijfers_a"])
        A = int(_getal(rng, ca, 0, verschillend=False))
        B = int("".join(str(rng.randint(2, 9)) for _ in range(cb)))
        da = db = 0
        if soort == "komma":
            totaal = rng.randint(1, max(1, p["decimalen"]))
            da = rng.randint(0, min(totaal, ca - 1)) if ca > 1 else 0
            db = min(totaal - da, cb - 1 if cb > 1 else 0) if totaal - da else 0
            if da + db == 0:
                da = 1
        a, b = D(A).scaleb(-da), D(B).scaleb(-db)
        ta, tb = fmt(a), fmt(b)
        if A % 10 == 0 and da:  # een kommagetal mag niet op een 0 eindigen
            A += 1
            a = D(A).scaleb(-da)
            ta = fmt(a)
        rijen = [str(A * int(c) * 10 ** r) for r, c in enumerate(reversed(str(B)))]
        invul = ([f"rij {i + 1}" for i in range(len(rijen))] if len(rijen) > 1 else []) + ["uitkomst"]
        verwacht = (rijen if len(rijen) > 1 else []) + [fmt(a * b)]
        model = Rooster("×", [ta, tb], len(str(A)) + len(str(B)), 0, invul, verwacht, komma_zelf=True)
        d = {"op": "×", "a": str(a), "b": str(b), "soort": soort,
             "onderwerp": "kommagetallen" if soort == "komma" else f"× {cb} cijfer{'s' if cb > 1 else ''}"}
        return Vraag(self.id, f"{self.id}:{ta}x{tb}", f"{ta} × {tb} =", a * b, data=d, invoer="rooster", model=model)

    def ABr(self, v):
        a, b = D(v.data["a"]), D(v.data["b"])
        A, B = int(a.scaleb(_decimalen(a))), int(b.scaleb(_decimalen(b)))
        return A, B, _decimalen(a) + _decimalen(b)

    def uitleg(self, v):
        A, B, dec = self.ABr(v)
        regels = []
        if B >= 10:
            for r, c in enumerate(reversed(str(B))):
                regels.append(f"Rij {r + 1}: {A} × {c}" + (f" {NAAM[r]}" if r else "") +
                              f" = {A * int(c) * 10 ** r}" + (f" (begin met {'een 0' if r == 1 else str(r) + ' nullen'})"
                                                              if r else ""))
            regels.append(f"Tel de rijen op: {A * B}.")
        else:
            regels.append(f"{A} × {B} = {A * B} (begin rechts, onthoud wat boven de 10 komt).")
        if dec:
            regels.append(f"Cijfers na de komma: {_decimalen(D(v.data['a']))} + {_decimalen(D(v.data['b']))} = {dec}, "
                          f"dus {v.verwacht}.")
        return regels

    def diagnose(self, v, getal):
        if getal is None or getal == v.antwoord:
            return None
        A, B, dec = self.ABr(v)
        for j in range(-5, 6):
            if j and getal.scaleb(j) == v.antwoord:
                return ("komma_product", f"De cijfers zijn juist, maar de komma niet. Tel de cijfers na de komma "
                        f"in beide getallen samen: {dec}.")
        if B >= 10 and getal == D(sum(A * int(c) for c in str(B))).scaleb(-dec):
            return "niet_opgeschoven", "Je vergat de tweede rij op te schuiven: begin die rij met een 0."
        return None

    def kolom_hulp(self, v, rij, kolom):
        A, B, dec = self.ABr(v)
        k = v.model.breedte - 1 - kolom
        rijen = list(reversed(str(B)))
        laatste = len(v.model.invul) - 1
        if rij == laatste and len(rijen) > 1:
            delen = [A * int(c) * 10 ** r for r, c in enumerate(rijen)]
            kols = optel_kolommen(delen)
            for kk, cijfers, onth, som, schrijf, uit in kols:
                if kk == k:
                    deel = _som_tekst(cijfers, onth)
                    tekst = f"Tel de rijen op. Deze kolom: {deel} = {som}: schrijf {schrijf}" + \
                            (f", onthoud {uit}." if uit else ".")
                    break
            else:
                tekst = "Tel de rijen op. In deze kolom komt niets."
            if dec:
                tekst += f" Daarna de komma: {dec} cijfer{'s' if dec > 1 else ''} na de komma (toets ,)."
            return tekst
        r = 0 if rij == -1 or rij == laatste else rij
        c = int(rijen[r])
        for kk, cijfer, onth, prod, schrijf, uit in maal_rij(A, c, r):
            if kk == k:
                if cijfer is None and not onth:
                    return f"Schrijf hier een 0: je rekent nu × {c} {NAAM[r]}, dus alles schuift {r} plaats op."
                if cijfer is None:
                    return f"Schrijf hier de {onth} die je nog onthouden had."
                tekst = f"{cijfer} × {c}" + (f" + {onth} (onthouden)" if onth else "") + f" = {prod}: schrijf {schrijf}"
                tekst += f", onthoud {uit}." if uit else "."
                if rij == laatste and dec:
                    tekst += f" Op het einde de komma: {dec} cijfer{'s' if dec > 1 else ''} na de komma (toets ,)."
                return tekst
        return "In deze kolom komt niets."

    def onderwerp_van_sleutel(self, sleutel):
        if not sleutel.startswith(self.id + ":"):
            return None
        if "," in sleutel:
            return "kommagetallen"
        b = sleutel.rsplit("x", 1)[-1]
        return f"× {len(b)} cijfer{'s' if len(b) > 1 else ''}"


# ---- staartdeling ------------------------------------------------------------------------------------

def staart_stappen(deeltal, deler, decimalen):
    """Bouwt de stappen van deeltal : deler (deeltal als Decimal; het quotiënt krijgt hoogstens `decimalen`
    decimalen, of meer als het deeltal er zelf meer heeft). Geeft (getoond deeltal, stappen, quotiënt, rest)."""
    eigen = _decimalen(deeltal)
    na = max(eigen, decimalen)
    geheel, _, deci = format(deeltal.quantize(D(1).scaleb(-na)), "f").partition(".")
    cijfers = geheel + deci
    k = len(geheel)
    stappen = []
    p, cur = 0, int(cijfers[0])
    while cur < deler and p + 1 < k:  # eerste stuk: zo weinig cijfers als nodig
        p += 1
        cur = cur * 10 + int(cijfers[p])
    while True:
        q = cur // deler
        if deler < 10:
            tip = f"Zoek in de tafel van {deler}: welk veelvoud past net in {cur}?"
        else:
            rond = (deler + 5) // 10 * 10
            tip = (f"Schat: {deler} is ongeveer {rond}. Hoeveel keer gaat {rond} in {cur}? "
                   f"Controleer daarna met {deler}.")
        stappen.append(Stap("deel", f"Hoeveel keer gaat {deler} in {cur}?", q, tip, p, p == k))
        rest = cur
        if q:
            stappen.append(Stap("maal", f"{q} × {deler} =", q * deler, f"Reken {q} × {deler}.", p))
            rest = cur - q * deler
            stappen.append(Stap("min", f"{cur} − {q * deler} =", rest, f"Trek af: {cur} − {q * deler}.", p))
        if p + 1 >= len(cijfers) or (rest == 0 and p + 1 >= k + eigen):
            break
        p += 1
        cur = rest * 10 + int(cijfers[p])
        extra = " (na de komma: ook een komma in de uitkomst)" if p == k else ""
        stappen.append(Stap("neer", f"Haal de {cijfers[p]} neer{extra}. Welk getal krijg je?", cur,
                            f"Zet de {cijfers[p]} achter de {rest}: dat geeft {cur}.", p))
    na_komma = max(0, p + 1 - k)
    getoond = geheel + ("," + deci[:na_komma] if na_komma else "")
    quotient = D(int(cijfers[:p + 1]) // deler).scaleb(-na_komma)
    return getoond, stappen, quotient, rest


def staart_fout(stap, gegeven, deler):
    """(code, uitleg) voor een fout antwoord op een stap."""
    if stap.soort == "deel":
        cur = int(stap.vraag.split(" in ")[1].rstrip("?"))
        if gegeven * deler > cur:
            return "staart_te_veel", f"{gegeven} × {deler} = {gegeven * deler}, dat is meer dan {cur}: te veel."
        return ("staart_te_weinig", f"Met {gegeven} hou je {cur - gegeven * deler} over, en dat is {deler} of meer: "
                "de deler past er nog eens in.")
    if stap.soort == "maal":
        return "staart_maal", f"Kijk de vermenigvuldiging na: {stap.vraag} {stap.antwoord}."
    if stap.soort == "min":
        return "staart_min", f"Kijk de aftrekking na: {stap.vraag} {stap.antwoord}."
    return "staart_neer", stap.tip


class Delen(_Cijferen):
    id = "wiskunde.cijferen.delen"
    naam = "Staartdeling"
    spiek_kop = "STAARTDELING"
    omschrijving = "stap voor stap: deel, maal, min, neer"
    denkfouten = {"staart_te_veel": "bij de staartdeling te veel keer geschat",
                  "staart_te_weinig": "bij de staartdeling te weinig keer geschat (rest te groot)",
                  "staart_maal": "een maalfout in de staartdeling", "staart_min": "een aftrekfout in de staartdeling",
                  "staart_neer": "verkeerd neergehaald in de staartdeling"}
    vast = ("soort",)

    def maak_met(self, p, rng, data=None):
        soorten = ["rest" if p["rest"] else "opgaand"] + (["komma"] if p["decimalen"] else [])
        soort = data["soort"] if data and "soort" in data else rng.choice(soorten)
        lo = 10 ** (p["deler_cijfers"] - 1)
        deler = rng.randint(max(2, lo), 10 * lo - 1)
        while deler % 10 == 0 or deler in (10, 11):
            deler = rng.randint(max(2, lo), 10 * lo - 1)
        if soort == "komma":
            dec = rng.randint(1, max(1, p["decimalen"]))
            for _ in range(50):
                q = D(rng.randint(10 ** (p["cijfers"] - 1) // deler + 1, 10 ** p["cijfers"] // deler)) + D(rng.randint(1, 10 ** dec - 1)).scaleb(-dec)
                deeltal = (q * deler).normalize()
                if _decimalen(q) == dec:
                    break
        else:
            lo_d = max(deler * 2, 10 ** (p["cijfers"] - 1))
            deeltal = D(rng.randint(lo_d, 10 ** p["cijfers"] - 1))
            if soort == "opgaand" or not p["rest"]:
                deeltal = D(int(deeltal) - int(deeltal) % deler)
            dec = 0
        getoond, stappen, quotient, rest = staart_stappen(deeltal, deler, dec)
        model = Staartdeling(getoond, deler, stappen, rest)
        toon = fmt(quotient) + (f" rest {rest}" if rest and not dec else "")
        d = {"deeltal": str(deeltal), "deler": deler, "dec": dec, "rest": rest if not dec else 0, "soort": soort,
             "onderwerp": {"rest": "met rest", "opgaand": "zonder rest", "komma": "kommagetal"}[soort]}
        return Vraag(self.id, f"{self.id}:{fmt(deeltal)}:{deler}", f"{fmt(deeltal)} : {deler} =", quotient, data=d,
                     invoer="staart", model=model, verwacht_tekst=toon)

    def stap_fout(self, v, stap, gegeven):
        return staart_fout(stap, gegeven, v.model.deler)

    def lees(self, tekst):
        m = re.match(r"\s*([-−]?[\d.,]+)", tekst or "")
        return lees_getal(m.group(1)) if m else None

    def uitleg(self, v):
        d = v.data
        q = v.antwoord
        regels = [f"{fmt(D(d['deeltal']))} : {d['deler']} = {v.verwacht}"]
        controle = f"{fmt(q)} × {d['deler']}" + (f" + {d['rest']}" if d["rest"] else "")
        regels.append(f"Controle: {controle} = {fmt(q * d['deler'] + d['rest'])}.")
        return regels

    def tip(self, v):
        return "Deel → vermenigvuldig → trek af → haal neer. De rest moet kleiner zijn dan de deler."

    def onderwerp_van_sleutel(self, sleutel):
        if not sleutel.startswith(self.id + ":"):
            return None
        return "kommagetal" if "," in sleutel else "staartdeling"


OPTELLEN = Optellen()
AFTREKKEN = Aftrekken()
VERMENIGVULDIGEN = Vermenigvuldigen()
DELEN = Delen()
ALLE = [OPTELLEN, AFTREKKEN, VERMENIGVULDIGEN, DELEN]
