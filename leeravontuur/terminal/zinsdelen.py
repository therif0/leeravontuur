"""De zinsontleder: een zin als woordblokjes, de zinsdelen aanduiden (Taal, docs/taal.md). Een invoer-object voor
terminal/oefenaar.py, zoals het vraagstuk (eigen_tekst, eigen_tip, extra, uitleg_na).

De vader (7/11):
- stap voor stap zoals op school (pv → o → lv → mv; op Makkelijk eerst in zinsdelen verdelen);
- **Tab** wisselt naar vrij kleuren (Makkelijk, Normaal); op Moeilijk is vrij kleuren meteen aan;
- een fout geeft een tip en een tweede kans; daarna het juiste antwoord met de uitleg.
Een zin is juist als elk zinsdeel juist is (ook na de tweede kans; dan komt hij wel in de herhaalbak, zoals bij een
vraagstuk). Al het nakijken gebeurt in de kern (kern/taal/zinsontleding.py).
"""

import curses
import textwrap

from ..kern.taal import zinsontleding as Z
from .scherm import BACKSPACE, ENTER, ESC, HULP, teken_van

TAB = 9
X, RIJ = 7, 6          # waar de zin begint (rij onder het verhaal: RIJ na de opdracht), 2 spaties tussen de woorden
OPDRACHT_BREED = 56    # tot rij 9 staat rechts het maatje
VERDELEN = "verdelen"
LETTERS = {"p": "pv", "o": "o", "g": "wwg", "n": "nwg", "l": "lv", "m": "mv", "b": "bwb"}
VRAAG = {"pv": "Zoek de persoonsvorm (pv).", "o": "Zoek het onderwerp (o).",
         "wwg": "Zoek het werkwoordelijk gezegde (wwg).", "nwg": "Zoek het naamwoordelijk gezegde (nwg).",
         "lv": "Is er een lijdend voorwerp (lv)?", "mv": "Is er een meewerkend voorwerp (mv)?",
         "bwb": "Is er een bijwoordelijke bepaling (bwb)?", VERDELEN: "Verdeel de zin in zinsdelen."}
KAN_GEEN = {"lv", "mv", "bwb"}  # die zitten niet in elke zin: N = er is er geen


def rol(label):
    return f"z_{label}"


class ZinsdelenInvoer:
    eigen_tekst = True
    eigen_tip = True

    def __init__(self, v, o):
        self.v, self.o, self.zin = v, o, v.model
        self.gevraagd = list(v.data.get("delen", ("pv", "o")))
        self.stappen = ([VERDELEN] if v.data.get("verdelen") else []) + Z.stappen(self.zin, self.gevraagd)
        self.stap_voor_stap = v.data.get("stap_voor_stap", True)
        self.vrij = not self.stap_voor_stap
        self.woorden = [i for i, w in enumerate(self.zin.woorden) if not w.leesteken]
        self.stap, self.cur, self.anker = 0, 0, 0
        self.gevonden = {}          # label -> posities (of None: er is er geen), wat al nagekeken is
        self.markering = {}         # vrij kleuren: positie -> label
        self.grenzen = set()        # in zinsdelen verdelen: index k = een grens vóór self.woorden[k]
        self.verdeeld = False       # de stap "verdelen" is gedaan
        self.gat = 1                # in zinsdelen verdelen: de cursor staat op een gat tussen twee woorden
        self.pogingen, self.mislukt = {}, []
        self.vrij_poging = 0
        self.tips, self.tip_nr, self.tiptekst = 0, 0, ""
        self.eerste_fout, self.diagnose, self.fouten = None, None, 0
        self.melding, self.melding_rol = "", "fout"
        self.cursor_pos, self.extra, self.uitleg_na = None, None, []
        self.hint = ""
        self.tweede_kans = True     # de Oefenaar zet het volgens de Hulp (een examen later: uit)
        self.spiekbrief_aan = True  # idem: na de laatste tip opent F1 de spiekbrief (bij het kopje van de stap)
        self.aantal_tips = 2
        if self.vrij and VERDELEN in self.stappen:
            self.stappen.remove(VERDELEN)

    # ---- wat er nu gevraagd wordt -------------------------------------------------------------------
    @property
    def label(self):
        return self.stappen[self.stap] if self.stap < len(self.stappen) else None

    def groep(self):
        a, b = sorted((self.anker, self.cur))
        return tuple(self.woorden[a:b + 1])

    # ---- vorm ---------------------------------------------------------------------------------------
    def hoogte(self, nagekeken=False):
        return RIJ + 4 if nagekeken else RIJ + 9

    def knoppen(self):
        if self.label == VERDELEN:
            k = [("←→", "gat", None), ("Spatie", "grens", ord(" ")), ("Enter", "klaar", 10)]
        elif self.vrij:
            letters = " ".join(l.upper() for l, lab in LETTERS.items() if lab in self.gevraagd)
            k = [(letters, "kleur", None), ("Enter", "nakijken", 10)]
        else:
            k = [("Spatie", "woord erbij", ord(" ")), ("Enter", "kies", 10)]
            if self.label in KAN_GEEN:
                k.append(("N", "geen", ord("n")))
        k.append(("F1", "tip", HULP))
        if self.stap_voor_stap and self.label != VERDELEN:
            k.append(("Tab", "stappen" if self.vrij else "vrij", TAB))
        return k + [("Esc", "stoppen", ESC)]

    # ---- tekenen ------------------------------------------------------------------------------------
    def teken(self, s, y, uitslag=None, hulp=False):
        self.cursor_pos = None
        if uitslag is None:
            self.teken_opdracht(s, y)
            self.teken_zin(s, y + RIJ, self.kleuren_nu(), bezig=True)
            self.teken_voortgang(s, y + RIJ + 4)
            for i, regel in enumerate(textwrap.wrap(self.tiptekst, 72)[:2]):
                s.put(y + RIJ + 6 + i, 4, regel, "accent")
            self.hint = self.hint_tekst()
        else:  # nagekeken: de juiste ontleding, in kleur
            s.put(y + RIJ - 2, 4, "Zo ontleed je deze zin:", "bold")  # onder het maatje (dat staat tot rij 9)
            juist = {}
            for label in self.stappen:
                if label != VERDELEN:
                    for p in Z.verwacht(self.zin, label) or ():
                        juist.setdefault(p, label)
            self.teken_zin(s, y + RIJ, juist, bezig=False)

    def teken_opdracht(self, s, y):
        if self.vrij:
            namen = " · ".join(f"{l.upper()} {LETTERS[l]}" for l in LETTERS if LETTERS[l] in self.gevraagd)
            s.put(y, 4, "Kleur de zinsdelen.", "bold")
            for i, regel in enumerate(textwrap.wrap(namen, OPDRACHT_BREED)[:2]):
                s.put(y + 1 + i, 4, regel, "dim")
        else:
            s.put(y, 4, f"Stap {self.stap + 1} van {len(self.stappen)}: {VRAAG[self.label]}", "bold")
            if self.label in KAN_GEEN:
                s.put(y + 1, 4, "Duid het aan, of druk N (er is er geen).", "dim")

    def kleuren_nu(self):
        """positie -> label van wat er nu gekleurd staat (nagekeken stappen, of wat het kind vrij kleurde)."""
        uit = {}
        for label, posities in self.gevonden.items():
            for p in posities or ():
                if label == "pv" or p not in uit:
                    uit[p] = label
        if self.vrij:
            uit.update(self.markering)
        return uit

    def teken_zin(self, s, y, kleuren, bezig):
        """De woorden (rij y), gemarkeerd als met een markeerstift in de kleur van het zinsdeel, met de afkorting
        eronder (y+2). Waar het kind staat (de groep die het kiest), staat een streep onder de woorden (y+1): zo lijkt
        de cursor niet op de gele pv."""
        x, plekken = X, []
        groep = set(self.groep()) if bezig and self.label != VERDELEN else set()
        for i, w in enumerate(self.zin.woorden):
            plekken.append(x)
            s.put(y, x, w.tekst, rol(kleuren[i]) if i in kleuren else "bold" if i in groep else "")
            if i in groep:
                s.put(y + 1, x, "▀" * len(w.tekst), "accent")
                if i + 1 in groep:
                    s.put(y + 1, x + len(w.tekst), "▀▀", "accent")
            if bezig and not w.leesteken:
                s.zones.voeg(y, x, 1, len(w.tekst), ("woord", self.woorden.index(i)))
            x += len(w.tekst) + 2
        # de markeerstift loopt door tussen de woorden van één zinsdeel, en de afkorting staat eronder
        i = 0
        while i < len(self.zin.woorden):
            label = kleuren.get(i)
            if not label:
                i += 1
                continue
            j = i
            while j + 1 < len(self.zin.woorden) and kleuren.get(j + 1) == label and not \
                    (label == "pv" or kleuren.get(j) == "pv"):
                j += 1
            begin, eind = plekken[i], plekken[j] + len(self.zin.woorden[j].tekst)
            for k in range(i, j):
                s.put(y, plekken[k] + len(self.zin.woorden[k].tekst), "  ", rol(label))
            s.put(y + 2, begin + max(0, (eind - begin - len(label)) // 2), label, rol(label))
            i = j + 1
        if bezig and self.label == VERDELEN:  # de grenzen tussen de woorden en de cursor op een gat
            for k in range(1, len(self.woorden)):
                gx = plekken[self.woorden[k]] - 1
                teken = "|" if k in self.grenzen else " "
                s.put(y, gx, teken, "cursor" if k == self.gat else "accent")
                s.zones.voeg(y, gx - 1, 1, 2, ("gat", k))

    def teken_voortgang(self, s, y):
        if self.vrij or self.label == VERDELEN:
            return
        x = 4
        for label in self.stappen:
            if label == VERDELEN:
                continue
            if label in self.gevonden:
                posities = self.gevonden[label]
                tekst = Z._woorden(self.zin, posities) if posities else "(geen)"
                stuk, r = f"{label} {tekst}", rol(label)
            else:
                stuk, r = f"{label} …", "dim"
            if x + len(stuk) > 78:
                break
            s.put(y, x, stuk, r)
            x += len(stuk) + 4

    def hint_tekst(self):
        if self.label == VERDELEN:
            return "←→ naar een plek tussen twee woorden · Spatie: een grens |"
        if self.vrij:
            return "←→ woord · Spatie: woord erbij · letter: kleur · Backspace: wis"
        return f"←→ woord, Spatie = het volgende woord erbij, Enter = dit is {Z.LIDWOORD[self.label]} {self.label}."

    # ---- toetsen ------------------------------------------------------------------------------------
    def toets(self, k):
        if isinstance(k, tuple):
            return self.klik(k)
        if k == HULP:
            self.volgende_tip()
            return None
        if k == TAB:
            if self.stap_voor_stap and self.label != VERDELEN:
                self.wissel()
            return None
        if self.label == VERDELEN:
            return self.toets_verdelen(k)
        n = len(self.woorden)
        sleft, sright = getattr(curses, "KEY_SLEFT", -1), getattr(curses, "KEY_SRIGHT", -1)
        if k == curses.KEY_LEFT:
            self.cur = self.anker = max(0, self.cur - 1)
        elif k == curses.KEY_RIGHT:
            self.cur = self.anker = min(n - 1, self.cur + 1)
        elif k == sright or k == ord(" "):
            self.cur = min(n - 1, self.cur + 1)
        elif k == sleft:
            self.cur = max(0, self.cur - 1)
        elif k in BACKSPACE or k == curses.KEY_DC:
            if self.vrij:
                for p in self.groep():
                    self.markering.pop(p, None)
            elif self.cur != self.anker:
                self.cur += 1 if self.cur < self.anker else -1
        elif k in ENTER:
            return self.nakijken_vrij() if self.vrij else self.kies(self.groep())
        else:
            ch = (teken_van(k) or "").lower()
            if not self.vrij and ch == "n" and self.label in KAN_GEEN:
                return self.kies(None)
            if self.vrij and ch in LETTERS:
                self.kleur(LETTERS[ch])
            return None
        self.melding = ""
        return None

    def klik(self, k):
        if k[0] == "gat" and self.label == VERDELEN:
            self.gat = k[1]
            self.grenzen ^= {k[1]}
        elif k[0] == "woord" and self.label != VERDELEN:
            a, b = sorted((self.anker, self.cur))
            if k[1] == b + 1 or k[1] == a - 1:  # een woord ernaast: de groep groter (slepen kan niet)
                self.cur = k[1]
                self.anker = a if k[1] > b else b
            else:
                self.cur = self.anker = k[1]
        return None

    def wissel(self):
        """Tab: van stap voor stap naar vrij kleuren en terug. Wat al juist gevonden was, blijft staan."""
        if not self.vrij:
            self.markering = {p: l for p, l in self.kleuren_nu().items()}
        else:
            self.markering = {}
            klaar = set(self.gevonden) | ({VERDELEN} if self.verdeeld else set())
            self.stap = next((i for i, l in enumerate(self.stappen) if l not in klaar), len(self.stappen))
        self.vrij = not self.vrij
        self.melding = ""

    # ---- stap voor stap -----------------------------------------------------------------------------
    def kies(self, keuze):
        label = self.label
        if Z.nakijken(self.zin, label, keuze):
            self.gevonden[label] = Z.verwacht(self.zin, label)
            tekst = Z._woorden(self.zin, keuze) if keuze else "er is er geen"
            self.melding, self.melding_rol = f"✔ {label}: {tekst}.", "goed"
            return self.volgende()
        d = Z.diagnose(self.zin, label, keuze)
        self.fout(label, d)
        if self.pogingen.get(label, 0) == 1 and self.tweede_kans:
            self.melding = "✘ " + (d[1] if d else "Nog niet juist. Probeer nog eens (F1 = tip).")
            self.melding_rol = "fout"
            return None
        self.mislukt.append(label)
        self.gevonden[label] = Z.verwacht(self.zin, label)
        self.melding, self.melding_rol = "✘ " + Z.uitleg(self.zin, label), "fout"
        return self.volgende()

    def fout(self, label, d):
        self.pogingen[label] = self.pogingen.get(label, 0) + 1
        if self.eerste_fout is None:
            self.eerste_fout = label
        if self.diagnose is None and d:
            self.diagnose = d

    def volgende(self):
        self.stap += 1
        self.tip_nr, self.tiptekst = 0, ""
        self.cur = self.anker = 0
        if self.stap < len(self.stappen):
            return None
        return self.klaar()

    # ---- in zinsdelen verdelen ------------------------------------------------------------------------
    def toets_verdelen(self, k):
        n = len(self.woorden)
        if k == curses.KEY_LEFT:
            self.gat = max(1, self.gat - 1)
        elif k == curses.KEY_RIGHT:
            self.gat = min(n - 1, self.gat + 1)
        elif k == ord(" "):
            self.grenzen ^= {self.gat}
        elif k in ENTER:
            grenzen = [0, *sorted(self.grenzen), n]
            stukken = [tuple(self.woorden[a:b]) for a, b in zip(grenzen, grenzen[1:])]
            juist, fout = Z.nakijken_verdeling(self.zin, stukken)
            if juist:
                self.verdeeld = True
                self.melding, self.melding_rol = "✔ Zo is de zin goed verdeeld.", "goed"
                return self.volgende()
            self.fout(VERDELEN, None)
            if self.pogingen[VERDELEN] == 1 and self.tweede_kans:
                stuk = " ".join(self.zin.woorden[p].tekst for p in fout[0]) if fout else ""
                self.melding = (f"✘ Kijk nog eens naar ‘{stuk}’: is dat één zinsdeel?" if stuk else
                                "✘ Nog niet juist: er ontbreekt een grens.")
                return None
            self.mislukt.append(VERDELEN)
            self.verdeeld = True
            juist_stukken = Z.verdeling(self.zin)
            self.melding = "✘ Zo is het juist: " + " | ".join(" ".join(self.zin.woorden[p].tekst for p in st)
                                                            for st in juist_stukken)
            return self.volgende()
        return None

    # ---- vrij kleuren ---------------------------------------------------------------------------------
    def kleur(self, label):
        if label not in self.gevraagd:
            self.melding = "Dat zinsdeel vraagt deze oefening niet."
            return
        groep = self.groep()
        if label == "pv" and len(groep) > 1:
            self.melding = "De persoonsvorm is één woord."
            return
        for p in groep:
            self.markering[p] = label
        self.melding = ""

    def nakijken_vrij(self):
        uit = Z.nakijken_vrij(self.zin, self.gevraagd, self.markering)
        fout = [l for l, (juist, _) in uit.items() if not juist]
        if not fout:
            self.gevonden.update({l: Z.verwacht(self.zin, l) for l in uit})
            return self.klaar()
        self.vrij_poging += 1
        for l in fout:
            self.fout(l, uit[l][1])
        if self.vrij_poging == 1 and self.tweede_kans:
            self.melding = f"✘ Nog niet alles juist: kijk nog eens naar {', '.join(fout)} (F1 = tip)."
            self.melding_rol = "fout"
            return None
        self.mislukt += [l for l in fout if l not in self.mislukt]
        self.gevonden.update({l: Z.verwacht(self.zin, l) for l in uit})
        return self.klaar()

    # ---- tips ---------------------------------------------------------------------------------------
    def volgende_tip(self):
        label = self.label
        if self.vrij:  # de tip bij het eerste zinsdeel dat nog niet juist gekleurd is
            uit = Z.nakijken_vrij(self.zin, self.gevraagd, self.markering)
            label = next((l for l, (juist, _) in uit.items() if not juist), None)
            if label is None:
                self.tiptekst = "Alles ziet er juist uit. Druk Enter om na te kijken."
                return
        tips = Z.TIP_VERDELEN if label == VERDELEN else Z.tips(self.zin, label)
        self.aantal_tips = len(tips)
        self.v.data["spiek_kop"] = Z.SPIEK_KOP.get(label, Z.SPIEK_KOP["pv"])  # daar opent de spiekbrief
        if self.tip_nr >= len(tips):
            self.tiptekst = "Meer tips zijn er niet. Probeer het, en lees daarna de uitleg."
            return
        self.tips += 1
        self.tiptekst = f"Tip {self.tip_nr + 1}: {tips[self.tip_nr]}"
        self.tip_nr += 1
        if self.tip_nr >= len(tips) and self.spiekbrief_aan:
            self.tiptekst += " Nog eens F1: je spiekbrief."

    @property
    def tips_op(self):
        """Alle tips van deze stap gegeven: de Oefenaar opent dan bij F1 de spiekbrief (de vaste werkwijze, #20)."""
        return self.tip_nr >= self.aantal_tips

    def spiekbrief_bekeken(self):
        """Na de spiekbrief begint het weer bij tip 1 (de vaste werkwijze)."""
        self.tips += 1
        self.tip_nr, self.tiptekst = 0, ""

    def hulp(self, o):
        return self.tiptekst

    def rijen(self):
        return []

    # ---- klaar --------------------------------------------------------------------------------------
    def klaar(self):
        juist = not self.mislukt
        self.extra = {"zinsdelen": 1, "tips": self.tips, "eerste_fout": self.eerste_fout,
                      "mislukt": list(self.mislukt), "vrij": self.vrij}
        if juist and self.eerste_fout is None:
            kop = ["Elk zinsdeel juist, meteen!"]
        elif juist:
            kop = [f"Juist, met een tweede kans bij: {', '.join(dict.fromkeys(self.pogingen))}."]
        else:
            kop = [f"Niet gevonden: {', '.join(self.mislukt)}. Lees de uitleg."]
        stappen = [l for l in self.stappen if l != VERDELEN]
        self.uitleg_na = kop + [("✘ " if l in self.mislukt else "✔ ") + Z.uitleg(self.zin, l) for l in stappen]
        antwoord = "juist" if juist else "fout"
        return antwoord, antwoord
