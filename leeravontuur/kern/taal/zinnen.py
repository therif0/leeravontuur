"""Een zin met zijn ontleding: de woorden (met hun woordsoort) en de zinsdelen (alleen data, geen curses).

Elke zin is **volledig ontleed**: elk woord hoort bij een zinsdeel (behalve de leestekens). Het leerjaar beslist welke
zinsdelen gevraagd worden; de rest blijft in de oefening grijs. De pv hoort ook bij het gezegde (wwg of nwg), zoals
op school; verder overlappen zinsdelen niet.

Een zin schrijven (de nagekeken lijst en de eigen zinnen van de ouder) gaat met haakjes:

    [o De juf] [pv geeft] [mv de kinderen] [lv een boek].
    [o Oma] [pv,wwg heeft] [lv een fiets] [wwg gekocht].
    [bwb Morgen] [pv geeft] [o oma] [mv haar/vnw kleinzoon] [lv een fiets].

Een woord kan zijn woordsoort meekrijgen met een schuine streep (`haar/vnw`). Het gezegde (wwg, nwg) mag in stukken
staan: alle stukken samen zijn één zinsdeel. Bij de andere labels is elk paar haakjes één zinsdeel.
"""

import re
from dataclasses import dataclass, field

# de zinsdelen, in de volgorde van de stappen (de vader, 7/11: pv → o → lv → mv; op Moeilijk komt de rest erbij)
ZINSDELEN = {
    "pv": "persoonsvorm",
    "o": "onderwerp",
    "wwg": "werkwoordelijk gezegde",
    "nwg": "naamwoordelijk gezegde",
    "lv": "lijdend voorwerp",
    "mv": "meewerkend voorwerp",
    "bwb": "bijwoordelijke bepaling",
}
GEZEGDE = ("wwg", "nwg")  # de pv hoort erbij; mag in stukken staan
WOORDSOORTEN = {
    "zn": "zelfstandig naamwoord",
    "lidw": "lidwoord",
    "bn": "bijvoeglijk naamwoord",
    "ww": "werkwoord",
    "telw": "telwoord",
    "vz": "voorzetsel",
    "bijw": "bijwoord",
    "vw": "voegwoord",
    "vnw": "voornaamwoord",
}
LEESTEKENS = ".?!,"
LT = "lt"  # de woordsoort van een leesteken (niet aan te duiden)


class ZinFout(ValueError):
    """Een zin met haakjes die niet klopt (de melding zegt wat er mis is, in gewone taal)."""


@dataclass(frozen=True)
class Woord:
    tekst: str
    soort: str | None = None  # woordsoort (zie WOORDSOORTEN), LT voor een leesteken, None = nog niet bekend

    @property
    def leesteken(self):
        return self.soort == LT


@dataclass(frozen=True)
class Deel:
    label: str            # zie ZINSDELEN
    posities: tuple       # de posities van de woorden in de zin (oplopend; een gezegde mag in stukken)

    def tekst(self, zin):
        return " ".join(zin.woorden[i].tekst for i in self.posities)


@dataclass
class Zin:
    woorden: list
    delen: list
    data: dict = field(default_factory=dict)  # hoe de zin gemaakt is (de machine: werkwoord, tijd, getal …)

    @property
    def tekst(self):
        """De zin zoals hij er staat: woorden met een spatie, leestekens tegen het woord ervoor."""
        uit = ""
        for w in self.woorden:
            uit += w.tekst if w.leesteken else (" " if uit else "") + w.tekst
        return uit

    def deel(self, label):
        """Het (eerste) zinsdeel met dit label, of None."""
        return next((d for d in self.delen if d.label == label), None)

    def alle(self, label):
        return [d for d in self.delen if d.label == label]

    def labels(self):
        return {d.label for d in self.delen}

    def label_van(self, i):
        """Het zinsdeel van woord i (de pv gaat voor het gezegde), of None."""
        labels = [d.label for d in self.delen if i in d.posities]
        return "pv" if "pv" in labels else (labels[0] if labels else None)

    def haakjes(self):
        """De zin terug in haakjes (voor de ouder en de tests). Woorden van hetzelfde zinsdeel na elkaar = één paar."""
        stukken, i = [], 0
        while i < len(self.woorden):
            w = self.woorden[i]
            if w.leesteken:
                stukken.append(w.tekst)
                i += 1
                continue
            labels = tuple(sorted({d.label for d in self.delen if i in d.posities}, key=list(ZINSDELEN).index))
            j = i + 1
            while j < len(self.woorden) and not self.woorden[j].leesteken and \
                    tuple(sorted({d.label for d in self.delen if j in d.posities}, key=list(ZINSDELEN).index)) == labels \
                    and _zelfde_deel(self, i, j):
                j += 1
            tekst = " ".join(self.woorden[k].tekst for k in range(i, j))
            stukken.append(f"[{','.join(labels)} {tekst}]" if labels else tekst)
            i = j
        uit = ""
        for s in stukken:
            uit += s if s in LEESTEKENS else (" " if uit else "") + s
        return uit


BREEDTE = 71  # zoveel tekens mag een zin hebben met 2 spaties tussen de woorden (80 kolommen min de marges)


def breedte(zin):
    """Hoe breed de zin op het scherm staat: de woorden met 2 spaties ertussen (ook voor het leesteken)."""
    return sum(len(w.tekst) for w in zin.woorden) + 2 * (len(zin.woorden) - 1)


def _zelfde_deel(zin, i, j):
    """Horen woord i en j bij precies dezelfde zinsdelen (niet twee bwb's na elkaar)?"""
    return [d for d in zin.delen if i in d.posities] == [d for d in zin.delen if j in d.posities]


_WOORD = re.compile(r"[^\s\[\]]+")


def _splits(tekst):
    """'boek.' → ['boek', '.']; leestekens aan het einde van een woord worden een eigen woord."""
    uit = []
    for stuk in tekst.split():
        einde = []
        while stuk and stuk[-1] in LEESTEKENS:
            einde.insert(0, stuk[-1])
            stuk = stuk[:-1]
        if stuk:
            uit.append(stuk)
        uit += einde
    return uit


def _woord(stuk, soorten):
    if stuk in LEESTEKENS:
        return Woord(stuk, LT)
    tekst, _, soort = stuk.partition("/")
    if soort and soort not in WOORDSOORTEN:
        raise ZinFout(f"'{soort}' is geen woordsoort (kies uit {', '.join(WOORDSOORTEN)}).")
    if not tekst:
        raise ZinFout("Er staat een schuine streep zonder woord.")
    return Woord(tekst, soort or (soorten(tekst) if soorten else None))


def lees_haakjes(tekst, soorten=None):
    """Een zin met haakjes → Zin. soorten(woord) mag de woordsoort geven van een woord zonder /soort.
    Geeft ZinFout met een uitleg in gewone taal als er iets niet klopt."""
    woorden, delen, gezegde = [], [], {}
    i = 0
    tekst = tekst.strip()
    while i < len(tekst):
        c = tekst[i]
        if c.isspace():
            i += 1
        elif c == "[":
            eind = tekst.find("]", i)
            if eind < 0:
                raise ZinFout("Er ontbreekt een ] (elk zinsdeel staat tussen [ en ]).")
            binnen = tekst[i + 1:eind]
            if "[" in binnen:
                raise ZinFout("Een zinsdeel staat in een ander zinsdeel: sluit eerst met ].")
            labels, _, rest = binnen.strip().partition(" ")
            labels = labels.split(",")
            for label in labels:
                if label not in ZINSDELEN:
                    raise ZinFout(f"'{label}' is geen zinsdeel (kies uit {', '.join(ZINSDELEN)}).")
            stukken = _splits(rest)
            if not stukken or all(s in LEESTEKENS for s in stukken):
                raise ZinFout(f"Het zinsdeel {','.join(labels)} heeft geen woorden.")
            posities = []
            for s in stukken:
                if s not in LEESTEKENS:
                    posities.append(len(woorden))
                woorden.append(_woord(s, soorten))
            for label in labels:
                if label in GEZEGDE:
                    gezegde.setdefault(label, []).extend(posities)
                else:
                    delen.append(Deel(label, tuple(posities)))
            i = eind + 1
        elif c == "]":
            raise ZinFout("Er staat een ] zonder [.")
        else:
            m = _WOORD.match(tekst, i)
            for s in _splits(m.group()):
                woorden.append(_woord(s, soorten))
            i = m.end()
    for label, posities in gezegde.items():
        delen.append(Deel(label, tuple(sorted(posities))))
    pv = [d for d in delen if d.label == "pv"]
    if not gezegde and len(pv) == 1:  # geen gezegde geschreven: het werkwoordelijk gezegde is de pv alleen
        delen.append(Deel("wwg", pv[0].posities))
    zin = Zin(woorden, sorted(delen, key=lambda d: (list(ZINSDELEN).index(d.label), d.posities)))
    fouten = controleer(zin)
    if fouten:
        raise ZinFout(fouten[0])
    return zin


def controleer(zin, volledig=True):
    """De fouten in een ontleding (leeg = in orde), in gewone taal. volledig: elk woord hoort bij een zinsdeel."""
    fouten = []
    if not zin.woorden or all(w.leesteken for w in zin.woorden):
        return ["De zin is leeg."]
    pv = zin.alle("pv")
    if len(pv) != 1:
        fouten.append("Een zin heeft precies één persoonsvorm (pv)." if pv else "Er is geen persoonsvorm (pv).")
    elif len(pv[0].posities) != 1:
        fouten.append("De persoonsvorm is één woord.")
    if len(zin.alle("o")) > 1:
        fouten.append("Een zin heeft hoogstens één onderwerp (o).")
    if zin.deel("wwg") and zin.deel("nwg"):
        fouten.append("Een zin heeft een werkwoordelijk of een naamwoordelijk gezegde, niet allebei.")
    gezegde = [d for d in zin.delen if d.label in GEZEGDE]
    if pv and gezegde and pv[0].posities[0] not in gezegde[0].posities:
        fouten.append("De persoonsvorm hoort bij het gezegde.")
    gezien = {}
    for d in zin.delen:
        if d.label == "pv":
            continue
        for p in d.posities:
            if zin.woorden[p].leesteken:
                fouten.append("Een leesteken hoort bij geen zinsdeel.")
            elif p in gezien and not (d.label in GEZEGDE or gezien[p] in GEZEGDE):
                fouten.append(f"'{zin.woorden[p].tekst}' staat in twee zinsdelen ({gezien[p]} en {d.label}).")
            gezien.setdefault(p, d.label)
    if volledig:
        in_deel = {p for d in zin.delen for p in d.posities}
        los = [w.tekst for i, w in enumerate(zin.woorden) if not w.leesteken and i not in in_deel]
        if los:
            fouten.append(f"'{los[0]}' hoort bij geen enkel zinsdeel.")
    return list(dict.fromkeys(fouten))
