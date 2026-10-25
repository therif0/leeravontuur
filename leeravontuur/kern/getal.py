"""Getallen lezen en tonen zoals in Vlaanderen: met een komma."""

import re
from decimal import Decimal


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
