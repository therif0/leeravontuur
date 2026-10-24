"""De winkel: items voor de avatar kopen met punten, met een kleine rekenvraag bij elke aankoop.

Juist → het item meteen. Fout → "Ben je zeker?" en nog één kans. Nog eens fout → een mini-lesje en het item
toch (de punten zijn betaald), maar met een ludieke straf die de ouder kiest: standaard komt het pakje pas
na 10 juiste antwoorden ("de koerier is verdwaald").
"""

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import avatar as A
from .leerjaren import LEERJAREN

BESTAND = Path(__file__).resolve().parent.parent / "inhoud" / "avatar" / "winkel.json"
LAGEN = {"vorm": "Vormen", "kleur": "Kleuren", "ogen": "Ogen", "oren": "Oren", "haar": "Haar",
         "hoed": "Hoeden", "accessoire": "Accessoires"}
PAKJE_JUIST = 10
PAKJE_MINUTEN = 15
VERZENDKOSTEN = 5


@dataclass(frozen=True)
class Item:
    laag: str
    sleutel: str
    naam: str
    prijs: int


@lru_cache(maxsize=1)
def _data():
    return json.loads(BESTAND.read_text(encoding="utf-8"))


def catalogus(laag=None):
    d = _data()
    uit = []
    for l in LAGEN:
        if laag and l != laag:
            continue
        namen = A.opties(l)
        for s in d["gratis"].get(l, []):
            uit.append(Item(l, s, namen[s], 0))
        for s, prijs in d["prijzen"].get(l, {}).items():
            uit.append(Item(l, s, namen[s], prijs))
    return uit


def zoek(laag, sleutel):
    return next((i for i in catalogus(laag) if i.sleutel == sleutel), None)


def in_kast(opslag, kind_id):
    """{(laag, sleutel)} van alles wat het kind mag dragen (gratis + gekocht en geleverd)."""
    uit = {(i.laag, i.sleutel) for i in catalogus() if i.prijs == 0}
    uit |= {(b["laag"], b["sleutel"]) for b in opslag.bezit(kind_id) if b["geleverd"]}
    return uit


def gekocht(opslag, kind_id):
    return {(b["laag"], b["sleutel"]): b for b in opslag.bezit(kind_id)}


# ---- de rekenvraag bij een aankoop ------------------------------------------------

@dataclass
class Challenge:
    vraag: str
    antwoord: int
    betalen: int          # wat het item echt kost (eventueel met korting)
    lesje: list           # uitleg als het fout blijft


def _lesje_aftrekken(a, b):
    tientallen = (b // 10) * 10
    stappen = [f"{a} − {b} = ?"]
    if b >= 10 and b % 10:
        tussen = a - tientallen
        stappen += [f"Splits {b} in {tientallen} en {b - tientallen}.",
                    f"{a} − {tientallen} = {tussen}", f"{tussen} − {b - tientallen} = {tussen - (b - tientallen)}"]
    else:
        stappen.append(f"Tel {b} terug vanaf {a}: je komt uit op {a - b}.")
    stappen.append(f"Dus {a} − {b} = {a - b}.")
    return stappen


def challenge(saldo, prijs, leerjaar, rng=random):
    """De rekenvraag als het kind genoeg punten heeft. Hoger leerjaar → soms met korting (procent)."""
    i = LEERJAREN.index(leerjaar) if leerjaar in LEERJAREN else 2
    kortingen = []
    if i >= 2:          # vanaf het 5de: eenvoudige procenten
        kortingen = [10, 20, 25, 50]
    if i >= 3:          # vanaf het 6de: ook moeilijkere procenten
        kortingen += [15, 30, 40]
    kortingen = [k for k in kortingen if prijs * k % 100 == 0]
    if kortingen and rng.random() < 0.5:
        k = rng.choice(kortingen)
        betalen = prijs - prijs * k // 100
        return Challenge(
            f"Vandaag {k} % korting! Het kost normaal {prijs} punten. Je hebt {saldo} punten. "
            f"Hoeveel punten heb je over na de aankoop?",
            saldo - betalen, betalen,
            [f"{k} % van {prijs} = {prijs} × {k} : 100 = {prijs * k // 100} punten korting.",
             f"Je betaalt dus {prijs} − {prijs * k // 100} = {betalen} punten.",
             *_lesje_aftrekken(saldo, betalen)])
    return Challenge(f"Je hebt {saldo} punten. Dit kost {prijs} punten. Hoeveel punten heb je over?",
                     saldo - prijs, prijs, _lesje_aftrekken(saldo, prijs))


def spaar_vraag(saldo, prijs):
    """Als het kind te weinig punten heeft: hoeveel moet je nog sparen?"""
    return Challenge(f"Je hebt {saldo} punten. Dit kost {prijs} punten. Hoeveel punten moet je nog sparen?",
                     prijs - saldo, 0, [f"{prijs} − {saldo} = {prijs - saldo}",
                                        f"Nog {prijs - saldo} punten, dat is ongeveer "
                                        f"{-(-(prijs - saldo) // 10)} juiste antwoorden."])


# ---- kopen en leveren -------------------------------------------------------------

def koop(opslag, kind_id, item, betalen, challenge_juist, straf="pakje"):
    """Betaalt en zet het item in de kast (of onderweg). Geeft de levering (None = meteen)."""
    opslag.punten_bij(kind_id, -betalen, f"gekocht: {item.naam}")
    levering = None
    if not challenge_juist:
        if straf == "pakje":
            levering = {"soort": "pakje", "nodig": PAKJE_JUIST}
        elif straf == "tijd":
            levering = {"soort": "tijd", "minuten": PAKJE_MINUTEN}
        elif straf == "kosten":
            opslag.punten_bij(kind_id, -VERZENDKOSTEN, "verzendkosten (foute som in de winkel)")
    opslag.zet_bezit(kind_id, item.laag, item.sleutel, betalen, levering is None, levering, challenge_juist)
    return levering


def voortgang(opslag, kind_id, bezit):
    """(gedaan, nodig, eenheid) voor een pakje dat onderweg is."""
    juist, ms = opslag.sinds(kind_id, bezit["gekocht"])
    lev = bezit["levering"] or {}
    if lev.get("soort") == "tijd":
        return min(round(ms / 60000), lev["minuten"]), lev["minuten"], "minuten oefenen"
    return min(juist, lev.get("nodig", PAKJE_JUIST)), lev.get("nodig", PAKJE_JUIST), "juiste antwoorden"


def onderweg(opslag, kind_id):
    return [b for b in opslag.bezit(kind_id) if not b["geleverd"]]


def lever_pakjes(opslag, kind_id):
    """Levert pakjes waarvoor genoeg geoefend werd. Geeft de items die nu aankomen."""
    aangekomen = []
    for b in onderweg(opslag, kind_id):
        gedaan, nodig, _ = voortgang(opslag, kind_id, b)
        if gedaan >= nodig:
            opslag.lever(kind_id, b["laag"], b["sleutel"])
            item = zoek(b["laag"], b["sleutel"])
            if item:
                aangekomen.append(item)
    return aangekomen


def draag(opslag, kind_id, laag, sleutel):
    """Trekt een item aan (alleen als het in de kast zit). None = uittrekken (haar, hoed, accessoire)."""
    config = A.geldig(opslag.avatar(kind_id))
    if sleutel is None and A.STANDAARD[laag] is None:
        config[laag] = None
    elif (laag, sleutel) in in_kast(opslag, kind_id):
        config[laag] = sleutel
    else:
        return False
    opslag.bewaar_avatar(kind_id, config)
    return True

