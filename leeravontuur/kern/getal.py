"""Getallen lezen en tonen zoals in Vlaanderen: met een komma."""

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction


def decimalen(d):
    return max(0, -d.normalize().as_tuple().exponent)


def fmt(d):
    """Decimal -> tekst met komma, zonder wetenschappelijke notatie (negatief met het minteken −)."""
    d = Decimal(d)
    tekst = format(abs(d).normalize(), "f").replace(".", ",")
    return ("−" + tekst) if d < 0 else tekst


def lees_getal(tekst):
    """Leest wat het kind typte. '3,5' en '0.25' zijn kommagetallen, '3.500' is 3500.

    Een eenheid achteraan ('0,25 g') mag. Geeft None als het geen getal is.
    """
    t = re.sub(r"[a-z]+$", "", tekst.strip().lower()).replace(" ", "").replace("−", "-")
    negatief = t.startswith("-")
    if negatief:
        t = t[1:]
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"[1-9]\d{0,2}(\.\d{3})+", t):
        t = t.replace(".", "")
    if not re.fullmatch(r"\d+(\.\d+)?|\.\d+", t):
        return None
    return -Decimal(t) if negatief else Decimal(t)


def fmt_groot(d):
    """Zoals fmt, maar met spaties tussen de duizendtallen: 47352 -> '47 352'."""
    tekst = fmt(d)
    teken = "−" if tekst.startswith("−") else ""
    tekst = tekst.lstrip("−")
    geheel, _, komma = tekst.partition(",")
    groepen = []
    while len(geheel) > 3:
        groepen.insert(0, geheel[-3:])
        geheel = geheel[:-3]
    groepen.insert(0, geheel)
    return teken + " ".join(groepen) + ("," + komma if komma else "")


@dataclass(frozen=True)
class GetypteBreuk:
    """Een breuk zoals het kind ze typte: de vorm blijft bewaard (4/6 is niet 2/3 voor 'vereenvoudig')."""
    geheel: int
    teller: int
    noemer: int
    negatief: bool = False

    @property
    def waarde(self):
        w = self.geheel + Fraction(self.teller, self.noemer)
        return -w if self.negatief else w

    @property
    def eenvoudigst(self):
        """Is dit de eenvoudigste vorm (teller en noemer hebben geen gemeenschappelijke deler)?"""
        return self.teller == 0 or math.gcd(self.teller, self.noemer) == 1

    def __str__(self):
        teken = "−" if self.negatief else ""
        if not self.teller:
            return teken + str(self.geheel)
        return teken + (f"{self.geheel} " if self.geheel else "") + f"{self.teller}/{self.noemer}"


def lees_breuk(tekst):
    """'3/4', '7', '1 3/4' (gemengd), '-2/5' → GetypteBreuk, anders None."""
    t = (tekst or "").strip().replace("−", "-").replace(":", "/")
    negatief = t.startswith("-")
    t = t.lstrip("-").strip()
    m = re.fullmatch(r"(?:(\d+)\s+)?(\d+)\s*/\s*(\d+)|(\d+)", t)
    if not m:
        return None
    if m.group(4) is not None:
        return GetypteBreuk(int(m.group(4)), 0, 1, negatief)
    noemer = int(m.group(3))
    if noemer == 0:
        return None
    return GetypteBreuk(int(m.group(1) or 0), int(m.group(2)), noemer, negatief)


def fmt_breuk(f, gemengd=False):
    """Fraction → '3/4', '5' of (gemengd) '1 3/4'. Negatief met −."""
    f = Fraction(f)
    teken = "−" if f < 0 else ""
    f = abs(f)
    if f.denominator == 1:
        return teken + str(f.numerator)
    if gemengd and f > 1:
        geheel, rest = divmod(f.numerator, f.denominator)
        return f"{teken}{geheel} {rest}/{f.denominator}"
    return f"{teken}{f.numerator}/{f.denominator}"
