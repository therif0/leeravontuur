"""De werkwoordmachine: een zin met een gat, het denkschema in stappen (Taal › Werkwoordspelling, docs/taal.md). Een
invoer-object voor terminal/oefenaar.py, zoals de zinsontleder (eigen_tekst, eigen_tip, extra, uitleg_na).

De vader (10/11):
- stap voor stap zoals bij Zinsdelen: wie doet het, de stam, de regel ('t kofschip), dan de vorm typen;
- **Tab** = meteen de vorm typen (en terug); op Moeilijk typ je altijd meteen;
- een fout geeft een uitleg die bij de fout past en een tweede kans; daarna het juiste antwoord.
De stappen zijn data uit de kern (kern/taal/werkwoorden.stappen): een keuze (cijfer, ↑↓ + Enter, of een klik) of een
woord typen. Het antwoord van de vraag is de getypte vorm; een fout in een stap ervoor telt als "met een tweede kans"
(dan komt de vraag in de herhaalbak, zoals bij de zinsontleder).
"""

import curses
import textwrap

from ..kern.taal import werkwoorden as W
from .scherm import BACKSPACE, ENTER, ESC, HULP, teken_van

TAB = 9
X, RIJ = 7, 6          # waar de zin staat (RIJ rijen onder de opdracht: onder het maatje)
OPDRACHT_BREED = 56    # tot rij 9 staat rechts het maatje
MAX_WOORD = 16         # zoveel letters kan je typen


class WerkwoordInvoer:
    eigen_tekst = True
    eigen_tip = True

    def __init__(self, v, o):
        self.v, self.o, self.zin = v, o, v.model
        self.alle = W.stappen(self.zin, True)              # het hele denkschema
        self.kan_wisselen = v.data.get("stap_voor_stap", True) and len(self.alle) > 1
        self.direct = not self.kan_wisselen                  # alleen de vorm typen (Tab, of Moeilijk)
        self.stappen = self.alle if not self.direct else W.stappen(self.zin, False)
        self.stap, self.keuze, self.buf = 0, 0, ""
        self.gedaan = {}            # naam van de stap -> kort wat het juiste antwoord was
        self.pogingen, self.mislukt = {}, []
        self.tips, self.tip_nr, self.tiptekst = 0, 0, ""
        self.eerste_fout, self.diagnose, self.fouten = None, None, 0
        self.melding, self.melding_rol = "", "fout"
        self.cursor_pos, self.extra, self.uitleg_na = None, None, []
        self.hint = ""
        self.getypt = ""            # de vorm die het kind typte (voor het beeld na het nakijken)
        self.tweede_kans = True     # de Oefenaar zet het volgens de Hulp (een examen later: uit)
        self.spiekbrief_aan = True  # idem: na de laatste tip opent F1 de spiekbrief (bij het kopje van de stap)
        self.aantal_tips = 2

    # ---- wat er nu gevraagd wordt -------------------------------------------------------------------
    @property
    def nu(self):
        return self.stappen[min(self.stap, len(self.stappen) - 1)]

    # ---- vorm ---------------------------------------------------------------------------------------
    def hoogte(self, nagekeken=False):
        return RIJ + 2 if nagekeken else RIJ + 9

    def knoppen(self):
        if self.nu.soort == "keuze":
            k = [("↑↓", "kies", None), ("Enter", "ok", 10)]
        else:
            k = [("Enter", "controleren", 10)]
        k.append(("F1", "tip", HULP))
        if self.kan_wisselen:
            k.append(("Tab", "stappen" if self.direct else "meteen typen", TAB))
        return k + [("Esc", "stoppen", ESC)]

    # ---- tekenen ------------------------------------------------------------------------------------
    def teken(self, s, y, uitslag=None, hulp=False):
        self.cursor_pos = None
        if uitslag is not None:  # nagekeken: de zin met de juiste vorm
            s.put(y + RIJ - 2, 4, "De zin met de juiste vorm:", "bold")
            self.teken_zin(s, y + RIJ, self.zin.antwoord, "goed")
            return
        stap = self.nu
        kop = stap.vraag if len(self.stappen) == 1 else f"Stap {self.stap + 1} van {len(self.stappen)}: {stap.vraag}"
        s.put(y, 4, kop, "bold")
        if stap.sub:
            s.put(y + 1, 4, stap.sub, "dim")
        self.teken_zin(s, y + RIJ, self.buf if stap.naam == "vorm" else None, "veld")
        rij = y + RIJ + 2
        if stap.soort == "keuze":
            for i, tekst in enumerate(stap.opties):
                regel = f" {i + 1}  {tekst} "
                s.put(rij + i, X, regel, "cursor" if i == self.keuze else "")
                s.zones.voeg(rij + i, X, 1, len(regel), ("optie", i))
        elif stap.naam != "vorm":  # een woord typen (de stam)
            s.put(rij, X, stap.voor, "bold")
            x = X + len(stap.voor) + 1
            s.tekstvak(rij, x, self.buf, MAX_WOORD, "veld")
            self.cursor_pos = (rij, x + 1 + len(self.buf))
        if any(st.kofschip for st in self.alle) and not self.direct:
            self.teken_kofschip(s, y + RIJ + 5)
        self.teken_gevonden(s, y + RIJ + 6)
        for i, regel in enumerate(textwrap.wrap(self.tiptekst, 72)[:2]):
            s.put(y + RIJ + 7 + i, 4, regel, "accent")
        self.hint = ("↑↓ of het cijfer, Enter = kies" if stap.soort == "keuze" else "Typ het woord, Enter = klaar")

    def teken_zin(self, s, y, vak, rol):
        """De zin (rij y): vak = None (het gat ___), of de tekst in het vak (bij het typen en na het nakijken)."""
        zin, x = self.zin, X
        if zin.voor:
            s.put(y, x, zin.voor)
            x += len(zin.voor) + 1
        if vak is None:
            s.put(y, x, W.GAT, "bold")
            x += len(W.GAT)
        elif rol == "veld":
            breed = max(len(zin.antwoord), len(vak), 8) + 2
            s.tekstvak(y, x, vak, breed, "veld")
            self.cursor_pos = (y, x + 1 + len(vak))
            x += breed + 2
        else:  # nagekeken: de juiste vorm, met een hoofdletter als de zin ermee begint
            vorm = vak if zin.voor else vak[:1].upper() + vak[1:]
            s.put(y, x, vorm, rol)
            x += len(vorm)
        na = zin.na if zin.na[:1] in ".?!," else " " + zin.na
        s.put(y, x, na)
        s.put(y, x + len(na) + 2, f"({zin.inf})", "dim")

    def teken_kofschip(self, s, y):
        """'t kofschip, letter per letter; de letter van dit werkwoord licht op zodra die stap klaar is."""
        licht = next((st.kofschip for st in self.alle if st.kofschip and st.naam in self.gedaan), "")
        x = X
        for stuk in ("'t", "k", "o", "f", "s", "c", "h", "i", "p"):
            aan = bool(licht) and stuk.strip("'") in licht and stuk not in ("o", "i")
            s.put(y, x, stuk, "cursor" if aan else "dim")
            x += len(stuk) + 1 + (stuk == "'t")

    def teken_gevonden(self, s, y):
        stukken = [self.gedaan[st.naam] for st in self.alle if st.naam in self.gedaan and self.gedaan[st.naam]]
        if stukken and not self.direct:
            s.put(y, 4, ("✔ " + " · ".join(stukken))[:74], "goed")

    # ---- toetsen ------------------------------------------------------------------------------------
    def toets(self, k):
        stap = self.nu
        if isinstance(k, tuple) and k[0] != "teken":
            if k[0] == "optie" and stap.soort == "keuze" and k[1] < len(stap.opties):
                self.keuze = k[1]
                return self.kies(k[1])
            return None
        if k == HULP:
            self.volgende_tip()
            return None
        if k == TAB:
            if self.kan_wisselen:
                self.wissel()
            return None
        if stap.soort == "keuze":
            n = len(stap.opties)
            if k in (curses.KEY_UP, curses.KEY_LEFT):
                self.keuze = (self.keuze - 1) % n
            elif k in (curses.KEY_DOWN, curses.KEY_RIGHT):
                self.keuze = (self.keuze + 1) % n
            elif k in ENTER:
                return self.kies(self.keuze)
            else:
                ch = (teken_van(k) or "").lower()
                if ch.isdigit() and 1 <= int(ch) <= n:
                    self.keuze = int(ch) - 1
                    return self.kies(self.keuze)
                if ch in ("j", "n") and stap.naam == "kofschip":
                    self.keuze = 0 if ch == "j" else 1
                    return self.kies(self.keuze)
                return None
            self.melding = ""
            return None
        # een woord typen
        if k in ENTER:
            if not self.buf.strip():
                self.melding, self.melding_rol = "Typ eerst het woord.", "accent"
                return None
            return self.kies(self.buf.strip())
        if k in BACKSPACE or k == curses.KEY_DC:
            self.buf = self.buf[:-1]
        else:
            ch = teken_van(k)
            if ch is None or not (ch.isalpha() or ch in "'-") or len(self.buf) >= MAX_WOORD:
                return None
            self.buf += ch
        self.melding = ""
        return None

    def wissel(self):
        """Tab: van de stappen naar meteen typen en terug. Wat al gevonden was, blijft staan."""
        self.direct = not self.direct
        if self.direct:
            self.stappen, self.stap = W.stappen(self.zin, False), 0
        else:
            self.stappen = self.alle
            self.stap = next((i for i, st in enumerate(self.alle) if st.naam not in self.gedaan), len(self.alle) - 1)
        if self.nu.naam != "vorm":
            self.buf = ""
        self.keuze, self.melding = 0, ""
        self.tip_nr, self.tiptekst = 0, ""

    # ---- een stap nakijken --------------------------------------------------------------------------
    def kies(self, antwoord):
        stap = self.nu
        if W.nakijken_stap(stap, antwoord) or (stap.naam == "vorm" and W.nakijken(self.zin, antwoord)):
            if stap.naam == "vorm":
                return self.klaar(antwoord)
            self.gedaan[stap.naam] = W.kort(self.zin, stap)
            self.melding, self.melding_rol = "✔ " + stap.uitleg, "goed"
            return self.volgende()
        d = W.diagnose_stap(self.zin, stap, antwoord)
        self.pogingen[stap.naam] = self.pogingen.get(stap.naam, 0) + 1
        if self.eerste_fout is None:
            self.eerste_fout = stap.naam
        if self.diagnose is None and d:
            self.diagnose = d
        if self.pogingen[stap.naam] == 1 and self.tweede_kans:
            self.melding = "✘ " + (d[1] if d else "Nog niet juist. Probeer nog eens (F1 = tip).")
            self.melding_rol = "fout"
            return None
        if stap.naam == "vorm":
            return self.klaar(antwoord)
        self.mislukt.append(stap.naam)
        self.gedaan[stap.naam] = W.kort(self.zin, stap)
        self.melding, self.melding_rol = "✘ " + stap.uitleg, "fout"
        return self.volgende()

    def volgende(self):
        self.stap += 1
        self.keuze, self.buf = 0, ""
        self.tip_nr, self.tiptekst = 0, ""
        return None

    # ---- tips ---------------------------------------------------------------------------------------
    def volgende_tip(self):
        tips = self.nu.tips
        self.aantal_tips = len(tips)
        self.v.data["spiek_kop"] = self.nu.kop  # daar opent de spiekbrief
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
    def klaar(self, getypt):
        self.getypt = getypt.strip().lower()
        juist = W.nakijken(self.zin, self.getypt)
        namen = ", ".join(dict.fromkeys(NAAM.get(n, n) for n in self.pogingen))
        self.extra = {"werkwoord": 1, "tips": self.tips, "eerste_fout": self.eerste_fout,
                      "mislukt": list(self.mislukt), "direct": self.direct}
        if juist and self.eerste_fout is None:
            kop = "Meteen juist!"
        elif juist:
            kop = f"Juist, met een tweede kans bij: {namen}."
        else:
            kop = "Zo vind je de vorm:"
        self.uitleg_na = [kop, *W.uitleg(self.zin)]
        return self.getypt, self.getypt


# hoe een stap heet in "Juist, met een tweede kans bij: …"
NAAM = {"wie": "wie het doet", "getal": "één of meer", "stam": "de stam", "regel": "de regel",
        "kofschip": W.KOFSCHIP, "vorm": "de vorm"}
