"""Een vraagstuk oplossen in 4 stappen: Lees (gegeven en gevraagd), Plan, Reken (klad) en Controle (antwoord).

Een invoer-object voor terminal/oefenaar.py (zie terminal/rooster.py), met een paar extra's:
  eigen_tekst  het object tekent zelf het verhaal (de Oefenaar zet de vraag niet bovenaan)
  eigen_tip    '?' gaat naar het object: elke keer een volgende tip (die tekent het object zelf)
  extra        wat er bij het antwoord bewaard wordt (tips, klad, eerste poging …), ook voor de punten
  uitleg_na    de uitleg na het nakijken (in de plaats van Onderwerp.uitleg)
Meteen antwoorden mag. Is dat fout, dan krijgt het kind één keer een hulpje en de vraag om klad te maken.
"""

import curses
import textwrap

from ..kern import verhaal as V
from ..kern.klad import lees_regel
from ..kern.wiskunde import vraagstukken as VS
from .scherm import BACKSPACE, ENTER, ESC, teken_van

TAB = 9
X = 2                       # linkerrand
KOP = 15                    # waar de inhoud van een stap begint
LEES, PLAN, REKEN, CONTROLE = range(4)
OPWOORD = {"+": "optellen", "−": "aftrekken", "×": "vermenigvuldigen", ":": "delen", "omzet": "omzetten",
           "pct": "het procent berekenen", "heel": "delen", "rest": "delen (de rest)", "boven": "delen"}
PLAN_TOETS = {"+": "+", "-": "−", "−": "−", "x": "×", "X": "×", "*": "×", ":": ":", "/": ":", "o": "omzetten"}
KLAD_TEKENS = set("0123456789,.+-−*xX×:/()=%€ ") | set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ²³")
ANTW_TEKENS = set("0123456789,.€ -")
MAX_KLAD = 8


class VraagstukInvoer:
    eigen_tekst = True
    eigen_tip = True

    def __init__(self, v, o):
        self.v, self.o, self.m = v, o, v.model
        self.lijnen = V.regels(self.m.zinnen, VS.BREEDTE)
        self.ids = []
        for regel in self.lijnen:
            for woord in regel:
                for _, gid, _ in woord:
                    if gid and gid not in self.ids:
                        self.ids.append(gid)
        self.fase, self.onder = LEES, False   # onder = in stap 1 op de rij 'Gevraagd'
        self.cur, self.aangeduid = 0, []
        self.optie, self.gevraagd, self.gevraagd_eerst = 0, None, None
        self.plan, self.klad, self.buf, self.antw = [], [], "", ""
        self.tips, self.tiptekst = 0, ""
        self.eerste = None                    # het eerste (foute) directe antwoord
        self.melding, self.melding_rol = "", "fout"
        self.fouten, self.diagnose, self.cursor_pos = 0, None, None
        self.uitleg_na = []
        self.hint = ""

    # ---- vorm ----------------------------------------------------------------------------------------
    def verhaal_h(self):
        return len(self.lijnen) + 2

    def klad_h(self):
        return max(2, min(MAX_KLAD, 16 - self.verhaal_h() - 6))

    def hoogte(self, nagekeken=False):
        if nagekeken:
            return self.verhaal_h() + 4 + len(self.m.stappen) + len(self.controle_regels())
        return self.verhaal_h() + 4 + self.klad_h() + 2

    def knoppen(self):
        k = [("Tab", "volgende stap", TAB)]
        if self.fase == LEES:
            k.append(("Spatie", "aanduiden" if not self.onder else "kiezen", ord(" ")))
        k.append(("?", f"tip ({max(0, 4 - self.tips)} over)", ord("?")))
        k.append(("Enter", "controleren" if self.fase == CONTROLE else "ok", 10))
        return k + [("Esc", "stoppen", ESC)]

    # ---- tekenen -------------------------------------------------------------------------------------
    def teken(self, s, y, uitslag=None, hulp=False):
        bezig = uitslag is None
        self.cursor_pos = None
        self.teken_verhaal(s, y, bezig)
        r = y + self.verhaal_h()
        if bezig:
            self.teken_stappen(s, r)
            self.hint = self.hint_tekst()
        else:
            self.teken_uitwerking(s, r, uitslag)

    def teken_verhaal(self, s, y, bezig):
        breed = VS.BREEDTE + 4
        s.put(y, X, "┌ Het verhaal " + "─" * (breed - 15) + "┐", "dim")
        nodig = {k for k, g in self.m.gegevens.items() if g.nodig}
        for i, regel in enumerate(self.lijnen):
            yy = y + 1 + i
            s.put(yy, X, "│", "dim")
            s.put(yy, X + breed - 1, "│", "dim")
            x = X + 2
            for woord in regel:
                for tekst, gid, sleutel in woord:
                    rol = ""
                    if gid:
                        if bezig and self.fase == LEES and not self.onder and self.ids[self.cur] == gid:
                            rol = "cursor"
                        elif gid in self.aangeduid:
                            rol = "goedvak" if gid in nodig else "foutvak"
                        elif self.tips >= 1 or not bezig:
                            rol = "accent2" if gid in nodig else "dim"
                        else:
                            rol = "bold"
                        if bezig:
                            s.zones.voeg(yy, x, 1, len(tekst), ("gegeven", gid))
                    elif sleutel and (self.tips >= 1 or not bezig):
                        rol = "accent"
                    s.put(yy, x, tekst, rol)
                    x += len(tekst)
                x += 1
        s.put(y + len(self.lijnen) + 1, X, "└" + "─" * (breed - 2) + "┘", "dim")

    def kop(self, s, y, fase):
        plan = VS.STAPPENPLAN[fase]
        actief = fase == self.fase
        tekst = f"{'▸' if actief else ' '}{plan['nr']} {plan['naam']}"
        s.put(y, X, tekst, "accent" if actief else "bold")
        s.zones.voeg(y, X, 1, KOP - X - 1, ("fase", fase))

    def teken_stappen(self, s, r):
        m = self.m
        # 1 Lees: gegeven en gevraagd
        self.kop(s, r, LEES)
        s.put(r, KOP, "Gegeven:", "dim")
        x = KOP + 9
        if not self.aangeduid:
            s.put(r, x, "duid aan wat je nodig hebt (←→ en spatie, of klik)", "dim")
        for gid in self.aangeduid:
            g = m.gegevens[gid]
            stuk = f"{g.tekst} {'✔' if g.nodig else '(niet nodig)'}"
            if x + len(stuk) > 78:
                s.put(r, x, "…", "dim")
                break
            s.put(r, x, stuk, "goed" if g.nodig else "dim")
            s.zones.voeg(r, x, 1, len(stuk), ("gegeven", gid))
            x += len(stuk) + 3
        s.put(r + 1, KOP, "Gevraagd:", "dim")
        if self.gevraagd is None:
            kies = self.fase == LEES and self.onder
            tekst = m.opties[self.optie]
            s.put(r + 1, KOP + 10, "◂", "accent" if kies else "dim")
            s.put(r + 1, KOP + 12, tekst, "cursor" if kies else "")
            s.put(r + 1, KOP + 13 + len(tekst), f"▸ ({self.optie + 1}/{len(m.opties)})", "accent" if kies else "dim")
            s.zones.voeg(r + 1, KOP + 10, 1, 1, ("optie", -1))
            s.zones.voeg(r + 1, KOP + 12, 1, len(tekst), ("kies",))
            s.zones.voeg(r + 1, KOP + 13 + len(tekst), 1, 1, ("optie", 1))
        else:
            ok = m.opties[self.gevraagd] == m.gevraagd
            s.put(r + 1, KOP + 10, m.opties[self.gevraagd], "goed" if ok else "fout")
            s.put(r + 1, KOP + 11 + len(m.opties[self.gevraagd]),
                  "✔" if ok else "✘ lees de vraag nog eens (←→ = opnieuw kiezen)", "goed" if ok else "fout")
        # 2 Plan
        self.kop(s, r + 2, PLAN)
        if self.plan:
            tekst = "  ".join(("eerst " if i == 0 else "dan ") + op for i, op in enumerate(self.plan))
            s.put(r + 2, KOP, tekst[:30] if self.fase == PLAN else tekst, "bold")
        elif self.fase == PLAN:
            s.put(r + 2, KOP, "welke bewerking eerst?", "dim")
        else:
            s.put(r + 2, KOP, "(mag je overslaan)", "dim")
        x = 46
        if self.fase == PLAN:
            for op in ("+", "−", "×", ":", "omzetten", "⌫"):
                s.put(r + 2, x, f"[{op}]", "knop")
                s.zones.voeg(r + 2, x, 1, len(op) + 2, ("plan", op))
                x += len(op) + 3
        # 3 Reken: het klad
        self.kop(s, r + 3, REKEN)
        kh = self.klad_h()
        zicht = self.klad[-(kh - 1):] if len(self.klad) >= kh else self.klad
        eerste_nr = len(self.klad) - len(zicht)
        for i, (tekst, regel) in enumerate(zicht):
            yy = r + 3 + i
            s.put(yy, KOP, (regel.netjes or tekst)[:50], "")
            teken, rol = {True: ("✔", "goed"), False: ("✘", "fout")}.get(regel.juist, ("·", "dim"))
            s.put(yy, KOP + 52, teken, rol)
            s.zones.voeg(yy, KOP, 1, 54, ("klad", eerste_nr + i))
        yy = r + 3 + len(zicht)
        if self.fase == REKEN:
            s.put(yy, KOP, self.buf + " " * (50 - len(self.buf)), "veld")
            self.cursor_pos = (yy, KOP + len(self.buf))
        elif not self.klad:
            s.put(yy, KOP, "typ hier je rekenregels: 3 x 4 = 12" if self.fase != REKEN else "", "dim")
            s.zones.voeg(yy, KOP, 1, 50, ("fase", REKEN))
        # 4 Controle: de antwoordzin
        yc = r + 3 + kh
        self.kop(s, yc, CONTROLE)
        voor, na = self.m.antwoordzin
        s.put(yc, KOP, voor, "")
        vak = KOP + len(voor)
        s.tekstvak(yc, vak, self.antw, 10, "veld" if self.fase == CONTROLE else "dim", ("fase", CONTROLE))
        s.put(yc, vak + 12, na, "")
        if self.fase == CONTROLE:
            self.cursor_pos = (yc, vak + 1 + len(self.antw))
        # de tip
        if self.tiptekst:
            for i, stuk in enumerate(textwrap.wrap(self.tiptekst, 76)[:2]):
                s.put(yc + 1 + i, X, stuk, "accent")

    def teken_uitwerking(self, s, r, uitslag):
        m = self.m
        nodig = [g for g in m.gegevens.values() if g.nodig]
        overbodig = [g for g in m.gegevens.values() if not g.nodig]
        s.put(r, X, "Gegeven:", "bold")
        tekst = "  ·  ".join(f"{g.tekst} ({g.naam})" for g in nodig)
        if len(tekst) > 66:
            tekst = "  ·  ".join(g.tekst for g in nodig)
        s.put(r, KOP, tekst[:66], "")
        if overbodig:
            s.put(r, KOP + min(len(tekst), 66) + 3, f"niet nodig: {overbodig[0].tekst}"[:78 - KOP - len(tekst) - 3],
                  "dim")
        s.put(r + 1, X, "Gevraagd:", "bold")
        s.put(r + 1, KOP, m.gevraagd, "")
        s.put(r + 2, X, "Oplossing:", "bold")
        for i, st in enumerate(m.stappen):
            s.put(r + 2 + i, KOP, st.reken, "")
            s.put(r + 2 + i, KOP + len(st.reken) + 3, f"← {st.naam}"[:78 - KOP - len(st.reken) - 3], "dim")
        ya = r + 2 + len(m.stappen)
        s.put(ya, X, "Antwoord:", "bold")
        s.put(ya, KOP, VS.antwoordzin(m, self.v.antwoord), "goed" if uitslag else "")
        for i, regel in enumerate(self.controle_regels()):
            s.put(ya + 1 + i, KOP, regel, "dim")

    def controle_regels(self):
        """'Kan dat? …' onder het antwoord, over hoogstens 2 regels."""
        if not self.m.controle:
            return []
        return textwrap.wrap(f"Kan dat? {self.m.controle[2]}", 78 - KOP)[:2]

    def hint_tekst(self):
        if self.fase == LEES:
            return ("←→ = wat wordt er gevraagd? · spatie = kiezen · ↑ = terug naar de getallen"
                    if self.onder else "←→ = naar een getal · spatie = aanduiden · ↓ = gevraagd · a = antwoorden")
        if self.fase == PLAN:
            return "Typ de bewerkingen in volgorde: + - x : (o = omzetten) · Enter = verder"
        if self.fase == REKEN:
            return "Eén stap per regel · typ x voor maal, : voor delen · Enter = nakijken"
        return "Typ je antwoord (een getal, met een komma) en druk Enter."

    # ---- toetsen -------------------------------------------------------------------------------------
    def ga(self, fase):
        self.fase = fase % 4
        self.onder = self.fase == LEES and self.onder

    def toets(self, k):
        if isinstance(k, tuple):
            return self.klik(k)
        if k == ord("?"):
            self.volgende_tip()
            return None
        if k == TAB:
            self.ga(self.fase + 1)
            return None
        if k == getattr(curses, "KEY_BTAB", -99):
            self.ga(self.fase - 1)
            return None
        ch = teken_van(k)
        if self.fase in (LEES, PLAN):
            if ch in ("a", "A") and self.fase == LEES:
                self.ga(CONTROLE)
                return None
            if ch and ch.isdigit():  # een getal typen = meteen in het klad
                self.ga(REKEN)
        if self.fase == LEES:
            return self.toets_lees(k, ch)
        if self.fase == PLAN:
            return self.toets_plan(k, ch)
        if self.fase == REKEN:
            return self.toets_reken(k, ch)
        return self.toets_antwoord(k, ch)

    def klik(self, k):
        soort = k[0]
        if soort == "fase":
            self.ga(k[1])
        elif soort == "gegeven":
            self.ga(LEES)
            self.onder = False
            self.cur = self.ids.index(k[1])
            self.duid_aan()
        elif soort == "optie":
            self.ga(LEES)
            self.onder = True
            self.optie = (self.optie + k[1]) % len(self.m.opties)
            if self.gevraagd is not None and self.m.opties[self.gevraagd] != self.m.gevraagd:
                self.gevraagd = None
        elif soort == "kies":
            self.ga(LEES)
            self.onder = True
            self.kies_gevraagd()
        elif soort == "plan":
            self.ga(PLAN)
            if k[1] == "⌫":
                self.plan = self.plan[:-1]
            elif len(self.plan) < 5:
                self.plan.append(k[1])
        elif soort == "klad":
            self.ga(REKEN)
            if not self.buf and 0 <= k[1] < len(self.klad):
                self.buf = self.klad.pop(k[1])[0]
        return None

    def toets_lees(self, k, ch):
        if k == curses.KEY_DOWN:
            if self.onder:
                self.ga(PLAN)
            self.onder = not self.onder and self.fase == LEES
            return None
        if k == curses.KEY_UP:
            self.onder = False
            return None
        if k in (curses.KEY_LEFT, curses.KEY_RIGHT):
            stap = -1 if k == curses.KEY_LEFT else 1
            if self.onder:
                self.optie = (self.optie + stap) % len(self.m.opties)
                if self.gevraagd is not None and self.m.opties[self.gevraagd] != self.m.gevraagd:
                    self.gevraagd = None  # fout gekozen: opnieuw kiezen
            elif self.ids:
                self.cur = (self.cur + stap) % len(self.ids)
            return None
        if ch == " ":
            if self.onder:
                self.kies_gevraagd()
            else:
                self.duid_aan()
            return None
        if k in ENTER:
            if self.onder or self.gevraagd is not None and self.m.opties[self.gevraagd] != self.m.gevraagd:
                self.onder = True
                self.kies_gevraagd()
            elif self.gevraagd is None:
                self.onder = True
            else:
                self.ga(PLAN)
        return None

    def duid_aan(self):
        if not self.ids:
            return
        gid = self.ids[self.cur]
        if gid in self.aangeduid:
            self.aangeduid.remove(gid)
            self.melding = ""
            return
        self.aangeduid.append(gid)
        g = self.m.gegevens[gid]
        if g.nodig:
            self.melding, self.melding_rol = f"✔ {g.tekst}: {g.naam}.", "goed"
        else:
            self.melding, self.melding_rol = f"! {g.tekst} ({g.naam}) heb je niet nodig. Spatie = weer weg.", "accent"
        nodig = [k for k, x in self.m.gegevens.items() if x.nodig]
        if all(n in self.aangeduid for n in nodig) and self.gevraagd is None:
            self.melding += " Kies nu wat er gevraagd wordt (↓)."

    def kies_gevraagd(self):
        if self.gevraagd is not None and self.m.opties[self.gevraagd] != self.m.gevraagd:
            self.gevraagd = None  # opnieuw kiezen
            return
        self.gevraagd = self.optie
        ok = self.m.opties[self.optie] == self.m.gevraagd
        if self.gevraagd_eerst is None:
            self.gevraagd_eerst = ok
        if ok:
            self.melding, self.melding_rol = "✔ Dat wordt er gevraagd. Tab = verder naar het plan.", "goed"
            self.onder = False
        else:
            self.melding, self.melding_rol = "✘ Lees de vraag (de laatste zin) nog eens.", "fout"

    def toets_plan(self, k, ch):
        if k in BACKSPACE:
            self.plan = self.plan[:-1]
        elif ch in PLAN_TOETS and len(self.plan) < 5:
            self.plan.append(PLAN_TOETS[ch])
        elif k in ENTER:
            self.ga(REKEN)
        return None

    def toets_reken(self, k, ch):
        if k in BACKSPACE:
            if self.buf:
                self.buf = self.buf[:-1]
            elif self.klad:
                self.buf = self.klad.pop()[0]
            return None
        if k in ENTER:
            if not self.buf.strip():
                self.ga(CONTROLE)
                return None
            regel = lees_regel(self.buf)
            self.klad.append((self.buf, regel))
            self.buf = ""
            if regel.juist:
                self.melding, self.melding_rol = "✔ Deze regel klopt." + (f" {regel.melding}" if regel.melding
                                                                          else ""), "goed"
            elif regel.juist is False:
                self.melding, self.melding_rol = f"✘ {regel.melding}", "fout"
            else:
                self.melding, self.melding_rol = f"! {regel.melding or 'Schrijf een bewerking met = en de uitkomst.'}", "accent"
            return None
        if ch and ch in KLAD_TEKENS and len(self.buf) < 48:
            self.buf += ch
        return None

    def toets_antwoord(self, k, ch):
        if k in BACKSPACE:
            self.antw = self.antw[:-1]
            return None
        if k in ENTER:
            return self.controleer()
        if ch and ch in ANTW_TEKENS and len(self.antw) < 10:
            self.antw += ch
            self.melding = ""
        return None

    # ---- nakijken ------------------------------------------------------------------------------------
    def controleer(self):
        if not self.antw.strip():
            self.melding, self.melding_rol = "Typ eerst je antwoord.", "fout"
            return None
        getal = self.o.lees_vraag(self.v, self.antw)
        if getal is None:
            self.melding, self.melding_rol = "Typ een getal, bv. 7,60.", "fout"
            return None
        juist = self.o.nakijken(self.v, getal)
        analyse = VS.analyseer_klad(self.m, [r for _, r in self.klad])
        if not juist and self.eerste is None:
            # eerste poging fout: een hulpje en klad maken
            self.eerste = self.antw.strip()
            d = self.o.diagnose(self.v, getal)
            hulp = d[1] if d else "Dat is nog niet juist."
            if not self.klad:
                hulp += " Maak eens klad: duid eerst de gegevens aan en reken stap voor stap."
                self.ga(LEES)
            else:
                hulp += " Kijk je klad nog eens na." + (f" {analyse['eerste'][2]}" if analyse["eerste"] else "")
                self.ga(REKEN)
            self.melding, self.melding_rol = "! " + hulp, "accent"
            self.antw = ""
            return None
        if not juist:
            self.diagnose = self.o.diagnose(self.v, getal) or (
                (analyse["eerste"][1], analyse["eerste"][2]) if analyse["eerste"] else None)
        klad_ok = bool(self.klad) and analyse["eerste"] is None and analyse["compleet"]
        self.extra = {"vraagstuk": 1, "tips": self.tips, "eerste_fout": self.eerste,
                      "klad": [t for t, _ in self.klad], "klad_ok": klad_ok, "aangeduid": list(self.aangeduid),
                      "gevraagd_ok": self.gevraagd_eerst, "plan": " ".join(self.plan),
                      "klad_fout": analyse["eerste"][1] if analyse["eerste"] else None}
        self.uitleg_na = self.maak_uitleg(juist, klad_ok, analyse)
        return self.antw.strip(), getal

    def maak_uitleg(self, juist, klad_ok, analyse):
        uit = []
        if juist:
            if klad_ok:
                uit.append("Je klad is helemaal juist. Netjes gewerkt!")
            elif not self.klad:
                uit.append("Juist, zonder klad! Bij moeilijkere vraagstukken helpt klad om niets te vergeten.")
            elif analyse["eerste"]:
                uit.append(f"Juist antwoord! Maar kijk nog eens naar je klad. {analyse['eerste'][2]}")
            elif not analyse["compleet"]:
                uit.append("Juist antwoord, maar laat ook je tussenstappen zien in je klad.")
            if self.eerste is not None:
                uit.append(f"Eerst schreef je {self.eerste}: knap dat je het daarna zelf vond.")
        elif analyse["eerste"]:
            uit.append(analyse["eerste"][2])
        uit += [f"Waarom? {st.waarom}" for st in self.m.stappen][:3]
        return uit

    # ---- tips ----------------------------------------------------------------------------------------
    def volgende_tip(self):
        if self.tips >= 4:
            self.tiptekst = "Meer tips zijn er niet. Probeer iets en kijk na het nakijken naar de uitleg."
            return
        self.tips += 1
        m = self.m
        if self.tips == 1:
            self.tiptekst = ("Tip 1: de belangrijke woorden en de getallen die je nodig hebt, zijn nu aangeduid in "
                             "het verhaal.")
        elif self.tips == 2:
            self.tiptekst = f"Tip 2: gevraagd is {m.gevraagd}" + (f" (in {m.eenheid})." if m.eenheid else ".")
        elif self.tips == 3:
            rest = [OPWOORD.get(st.op, st.op) for st in m.stappen[1:]]
            self.tiptekst = "Tip 3: " + m.stappen[0].hint + (f" Daarna: {', dan '.join(rest)}." if rest else "")
        else:
            analyse = VS.analyseer_klad(m, [r for _, r in self.klad])
            nodig = [k for k, g in m.gegevens.items() if g.nodig]
            if analyse["eerste"]:
                self.tiptekst = "Tip 4: " + analyse["eerste"][2]
            elif not all(n in self.aangeduid for n in nodig):
                self.tiptekst = "Tip 4: je hebt nog niet alle getallen aangeduid die je nodig hebt (stap 1)."
            elif not self.klad:
                self.tiptekst = f"Tip 4: begin je klad (stap 3) met {m.stappen[0].naam}."
            else:
                ontbreekt = [st.naam for st in m.stappen if st.id not in analyse["gedekt"]]
                self.tiptekst = ("Tip 4: je klad ziet er goed uit. Nog uit te rekenen: " + ", ".join(ontbreekt) + "."
                                 if ontbreekt else "Tip 4: je klad is klaar. Schrijf je antwoord in stap 4.")

    def hulp(self, o):
        return self.tiptekst

    def rijen(self):
        return []

    extra = None


INVOER = {"vraagstuk": VraagstukInvoer}
