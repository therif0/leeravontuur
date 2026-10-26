"""Het ouderdeel (achter een wachtwoord): rapporten, kalender, export, kinderen beheren."""

import curses
from datetime import date

from ...kern import feedback, foutlog, klok, leerjaren, rapporten, wachtwoord
from ...kern.instellingen import STRAFFEN
from ...kern.paden import documenten_map
from .. import curriculum
from ..scherm import ENTER, ESC, TerugNaar, Vergrendeld

HOOFD = "Leeravontuur"
KR = [HOOFD, "Ouders"]
SLOT_SECONDEN = 600
PIN_ITERATIES = 100_000  # een pincode van 4 cijfers is toch snel te raden; snel controleren is hier belangrijker
VERGETEN = "Vergeten? Start dan met:  python3 oefeningen.py --wachtwoord-vergeten"


class Ouderdeel:
    def __init__(self, app):
        self.app = app
        self.s = app.s
        self.o = app.opslag

    # ---- toegang ---------------------------------------------------------------

    def open(self):
        """Vraagt het wachtwoord en toont het ouderdeel. Komt terug als de ouder klaar is."""
        try:
            if not self.toegang():
                return
            self.s.slot = SLOT_SECONDEN
            try:
                self.menu()
            except Vergrendeld:
                self.s.slot = None
                self.melding("Het ouderdeel is vergrendeld",
                             ["Er werd 10 minuten niets gedaan, dus het ouderdeel is gesloten."])
        except TerugNaar:
            pass
        finally:
            self.s.slot = None

    def toegang(self):
        opgeslagen = self.o.ouder_wachtwoord()
        if not opgeslagen:
            return self.nieuw_wachtwoord(eerste=True)
        for poging in range(3):
            vraag = "Ouderwachtwoord:" if poging == 0 else "Niet juist. Probeer nog eens:"
            ww = self.s.invoer(KR, vraag, verborgen=True, max_lengte=40, uitleg=["", VERGETEN])
            if ww is None:
                return False
            if wachtwoord.controleer(ww, opgeslagen):
                if wachtwoord.verouderd(opgeslagen):
                    self.o.zet_ouder_wachtwoord(wachtwoord.maak(ww))
                return True
        self.melding("Geen toegang", ["Drie keer een verkeerd wachtwoord.", "", VERGETEN])
        return False

    def nieuw_wachtwoord(self, eerste=False):
        uitleg = (["Met dit wachtwoord kom je in het ouderdeel: rapporten, leerjaar, timer, pincodes …",
                   "Kies iets dat je kind niet kan raden."] if eerste else [])
        while True:
            ww = self.s.invoer(KR + ["Wachtwoord"], "Kies een ouderwachtwoord (minstens 4 tekens):",
                               verborgen=True, max_lengte=40, uitleg=uitleg)
            if ww is None:
                return False
            if len(ww) < 4:
                uitleg = ["Dat is te kort: minstens 4 tekens."]
                continue
            nog = self.s.invoer(KR + ["Wachtwoord"], "Typ hetzelfde wachtwoord nog eens:", verborgen=True,
                                max_lengte=40)
            if nog is None:
                return False
            if nog != ww:
                uitleg = ["De twee wachtwoorden waren niet gelijk. Probeer opnieuw."]
                continue
            self.o.zet_ouder_wachtwoord(wachtwoord.maak(ww))
            return True

    def wachtwoord_wijzigen(self):
        oud = self.s.invoer(KR + ["Wachtwoord"], "Huidig wachtwoord:", verborgen=True, max_lengte=40)
        if oud is None:
            return
        if not wachtwoord.controleer(oud, self.o.ouder_wachtwoord() or ""):
            self.melding("Wachtwoord", ["Dat was niet het huidige wachtwoord. Er is niets veranderd."])
            return
        if self.nieuw_wachtwoord():
            self.melding("Wachtwoord", ["✔ Het nieuwe wachtwoord is bewaard."])

    # ---- hulpjes -----------------------------------------------------------------

    def melding(self, titel, regels):
        self.s.lezer(KR + [titel], [(r, "fout" if r.startswith("✘") else "goed" if r.startswith("✔") else "")
                                    for r in regels],
                     [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})

    def kies_kind(self, kr, vraag):
        kinderen = self.o.kinderen()
        if not kinderen:
            self.melding("Kinderen", ["Er zijn nog geen kinderen. Een kind maakt zijn account bij de start aan."])
            return None
        k = self.s.menu(kr, vraag, [(k.naam, leerjaren.NAMEN[k.leerjaar]) for k in kinderen])
        return None if k is None else kinderen[k]

    def lijst(self, kr, titel, items, sel=0, melding=""):
        """Een lijst 'naam: waarde' om te wijzigen. Geeft de gekozen index of None (Esc)."""
        s = self.s
        knoppen = [("↑↓", "kiezen", None), ("Enter", "wijzigen", 10), ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr, knoppen)
            h, w = s.maat()
            s.put(2, 4, titel, "bold")
            for i, (label, waarde) in enumerate(items):
                y = 4 + 2 * i
                s.put(y, 6, f" {label:<28} ", "cursor" if i == sel else "")
                s.put(y, 37, waarde, "accent")
                s.zones.voeg(y, 4, 1, w - 6, ("kies", i))
            s.put(5 + 2 * len(items), 4, melding, "info")
            k = s.toets()
            if isinstance(k, tuple):
                if k[0] == "kies":
                    return k[1]
                if k[0] == "scroll":
                    sel = (sel + k[1]) % len(items)
                continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(items)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(items)
            elif k in ENTER or k == ord(" "):
                return sel
            elif k in (ESC, ord("q")):
                return None

    # ---- menu --------------------------------------------------------------------

    @staticmethod
    def fouten_info():
        n = foutlog.aantal()
        return [f"! {n} onverwachte {'fout' if n == 1 else 'fouten'} bewaard · bekijk ze met --fouten"] if n else []

    def menu(self):
        while True:
            k = self.s.menu(KR, "Ouderdeel", [
                ("Rapporten", "per dag, week, maand · kalender · export"),
                ("Kinderen", "leerjaar, timer, pincode, naam, gegevens, wissen"),
                ("Punten", "logboek bekijken, bonuspunten geven"),
                ("Wachtwoord wijzigen", ""),
                (f"Opmerkingen ({len(feedback.lees())})", "wat er via 'Zeg het ons' geschreven werd"),
                ("Sluiten", "")],
                info=["Het ouderdeel sluit vanzelf na 10 minuten zonder toets."] + self.fouten_info())
            if k is None or k == 5:
                return
            if k == 4:
                self.opmerkingen()
            if k == 0:
                self.rapporten()
            elif k == 1:
                self.kinderen()
            elif k == 2:
                self.punten()
            elif k == 3:
                self.wachtwoord_wijzigen()

    def opmerkingen(self):
        kr = KR + ["Opmerkingen"]
        lijst = feedback.lees()
        regels = [("Opmerkingen uit 'Zeg het ons', nieuwste eerst. Ze staan in:", "dim"),
                  (f"  {feedback.pad()}", "dim"), ("", "")]
        if not lijst:
            regels.append(("Nog geen opmerkingen.", ""))
        for m in lijst:
            regels.append((f"{m['tijdstip'][8:10]}/{m['tijdstip'][5:7]} {m['tijdstip'][11:16]} · {m['naam']}", "accent"))
            regels.append((f"  {m['tekst']}", ""))
        self.s.lezer(kr, regels, [("Esc", "terug", ("terug",))], {k: None for k in (*ENTER, ESC, ("terug",))})

    # ---- rapporten -----------------------------------------------------------------

    def rapporten(self):
        kr = KR + ["Rapporten"]
        while True:
            kind = self.kies_kind(kr, "Van welk kind?")
            if kind is None:
                return
            while True:
                periode = self.kies_periode(kr + [kind.naam])
                if periode is None:
                    break
                self.toon_rapport(kr + [kind.naam], kind, periode)

    def kies_periode(self, kr):
        opties = rapporten.periodes()
        k = self.s.menu(kr, "Welke periode?", [(p.naam.capitalize(), p.tekst.split(" (")[0]) for p in opties]
                        + [("Zelf kiezen", "van … tot …")])
        if k is None:
            return None
        if k < len(opties):
            return opties[k]
        vandaag = klok.nu().date()
        van = self.vraag_datum(kr, "Vanaf welke dag? (bv. 01/10/2026)")
        if van is None:
            return None
        tot = self.vraag_datum(kr, "Tot en met welke dag? (leeg = vandaag)", leeg=vandaag)
        if tot is None:
            return None
        van, tot = min(van, tot), max(van, tot)
        return rapporten.Periode(van, tot, "zelf gekozen")

    def vraag_datum(self, kr, vraag, leeg=None):
        uitleg = []
        while True:
            t = self.s.invoer(kr, vraag, max_lengte=10, uitleg=uitleg)
            if t is None:
                return None
            if not t and leeg:
                return leeg
            d = rapporten.lees_datum(t)
            if d:
                return d
            uitleg = ["Dat is geen geldige datum. Schrijf ze zo: 24/10/2026"]

    def toon_rapport(self, kr, kind, periode):
        r = rapporten.maak_rapport(self.o, kind, periode)
        knoppen = [("E", "exporteren", ("export",)), ("K", "kalender", ("kalender",)), ("Esc", "terug", ("terug",))]
        toetsen = {ord("e"): "export", ord("E"): "export", ("export",): "export",
                   ord("k"): "kalender", ord("K"): "kalender", ("kalender",): "kalender",
                   ESC: None, ("terug",): None}
        while True:
            keuze = self.s.lezer(kr + ["Rapport"], rapporten.regels(r, curriculum.indeling()), knoppen, toetsen)
            if keuze is None:
                return
            if keuze == "export":
                self.exporteer(r)
            elif keuze == "kalender":
                self.kalender(kr, kind, periode.tot)

    def exporteer(self, r):
        try:
            csv_pad, txt_pad = rapporten.exporteer(r, documenten_map(), curriculum.indeling())
        except OSError as e:
            self.melding("Exporteren", [f"✘ Exporteren lukte niet: {e}"])
            return
        self.melding("Exporteren", ["✔ Het rapport is opgeslagen:", "", f"  {txt_pad}", f"  {csv_pad}", "",
                                    "Het CSV-bestand opent in Excel of LibreOffice Calc (alle antwoorden)."])

    def kalender(self, kr, kind, dag):
        s = self.s
        jaar, maand = dag.year, dag.month
        knoppen = [("←", "vorige maand", curses.KEY_LEFT), ("→", "volgende maand", curses.KEY_RIGHT),
                   ("Esc", "terug", ESC)]
        while True:
            if s.te_klein():
                continue
            dagen = rapporten.kalender(self.o, kind.id, jaar, maand)
            s.cursor(False)
            s.nieuw(kr + ["Kalender"], knoppen)
            x, y = 8, 3
            for i, (tekst, kleuren) in enumerate(rapporten.kalender_regels(jaar, maand, dagen)):
                s.put(y + i, x, tekst, "accent" if i == 0 else "dim" if i == 1 else "")
                for kol, breedte, rol in kleuren:
                    s.put(y + i, x + kol, tekst[kol:kol + breedte], rol)
            s.put(y + 10, x, "Gekleurde dagen: er werd geoefend.", "dim")
            for i, d in enumerate(sorted(dagen)[:8]):
                n, j = dagen[d]
                s.put(y + 11 + i, x + 2, f"{d:02d}/{maand:02d}: {n} vragen, {round(100 * j / n)} % juist", "")
            k = s.toets()
            if k == ESC:
                return
            if k == curses.KEY_LEFT:
                jaar, maand = (jaar - 1, 12) if maand == 1 else (jaar, maand - 1)
            elif k == curses.KEY_RIGHT:
                jaar, maand = (jaar + 1, 1) if maand == 12 else (jaar, maand + 1)

    # ---- punten ----------------------------------------------------------------------

    def punten(self):
        kr = KR + ["Punten"]
        while True:
            kind = self.kies_kind(kr, "Van welk kind?")
            if kind is None:
                return
            while True:
                regels = [(f"{kind.naam} heeft {self.o.punten_saldo(kind.id)} punten.", "accent"), ("", ""),
                          ("LAATSTE WIJZIGINGEN", "accent")]
                for p in self.o.punten_log(kind.id, 30):
                    t = p["tijdstip"]
                    regels.append((f"  {t[8:10]}/{t[5:7]} {t[11:16]}  {p['punten']:+5d}  {p['reden']}",
                                   "goed" if p["punten"] > 0 else "fout"))
                if len(regels) == 3:
                    regels.append(("  Nog geen punten.", "dim"))
                keuze = self.s.lezer(kr + [kind.naam], regels,
                                     [("B", "bonus geven", ("bonus",)), ("Esc", "terug", ("terug",))],
                                     {ord("b"): "bonus", ord("B"): "bonus", ("bonus",): "bonus",
                                      ESC: None, ("terug",): None})
                if keuze is None:
                    break
                aantal = self.s.invoer(kr + [kind.naam], "Hoeveel bonuspunten?", max_lengte=4, cijfers=True)
                if not aantal or not int(aantal):
                    continue
                reden = self.s.invoer(kr + [kind.naam], "Waarom? (bv. goed rapport)", max_lengte=40)
                if reden is None:
                    continue
                self.o.punten_bij(kind.id, int(aantal), "bonus van de ouders" + (f": {reden}" if reden else ""))

    # ---- kinderen --------------------------------------------------------------------

    def kinderen(self):
        kr = KR + ["Kinderen"]
        while True:
            kind = self.kies_kind(kr, "Welk kind?")
            if kind is None:
                return
            self.kind_beheren(kr, kind)

    def kind_beheren(self, kr, kind):
        sel, melding = 0, ""
        while True:
            kind = self.o.kind(kind.id)
            if kind is None:
                return
            inst = self.o.instellingen_van(kind.id)
            heeft_pin = bool(self.o.pincode(kind.id))
            items = [("Naam", kind.naam),
                     ("Leerjaar", leerjaren.NAMEN[kind.leerjaar]),
                     ("Weergave", "tekens, muis, avatar, klokvenster …"),
                     ("Timer zichtbaar voor het kind", "ja" if inst.timer_zichtbaar else "nee (alleen in rapport)"),
                     ("Pincode bij het starten", "ja" if heeft_pin else "nee"),
                     ("Winkel: 2x een foute som", STRAFFEN[inst.winkel_straf]),
                     ("Gegevens exporteren", "alle antwoorden (CSV + JSON)"),
                     ("Alles van dit kind wissen", "")]
            sel = self.lijst(kr + [kind.naam], f"Instellingen van {kind.naam}", items, sel, melding)
            melding = ""
            if sel is None:
                return
            if sel == 0:
                naam = self.s.invoer(kr + [kind.naam], "Nieuwe naam:", kind.naam)
                if naam and naam.lower() != kind.naam.lower() and \
                        naam.lower() in {k.naam.lower() for k in self.o.kinderen()}:
                    melding = f"Er is al een kind dat {naam} heet."
                elif naam:
                    inst.naam = naam
                    self.o.bewaar_instellingen(kind.id, inst)
            elif sel == 1:
                k = self.s.menu(kr + [kind.naam], f"In welk leerjaar zit {kind.naam}?",
                                [(leerjaren.NAMEN[j], "") for j in leerjaren.LEERJAREN],
                                start=leerjaren.LEERJAREN.index(kind.leerjaar),
                                info=["De niveaus schuiven mee: Makkelijk = een jaar lager, "
                                      "Heel moeilijk = twee jaar hoger."])
                if k is not None:
                    inst.leerjaar = leerjaren.LEERJAREN[k]
                    self.o.bewaar_instellingen(kind.id, inst)
            elif sel == 2:
                self.weergave(kr + [kind.naam], kind)
            elif sel == 3:
                inst.timer_zichtbaar = not inst.timer_zichtbaar
                self.o.bewaar_instellingen(kind.id, inst)
            elif sel == 4:
                melding = self.pincode(kr + [kind.naam], kind, heeft_pin)
            elif sel == 5:
                straffen = list(STRAFFEN)
                inst.winkel_straf = straffen[(straffen.index(inst.winkel_straf) + 1) % len(straffen)]
                self.o.bewaar_instellingen(kind.id, inst)
                melding = "Wat er gebeurt als je kind 2 keer een foute som maakt bij het kopen."
            elif sel == 6:
                melding = self.exporteer_alles(kind)
            elif sel == 7:
                if self.wissen(kr + [kind.naam], kind):
                    return
            self.app.herlaad_kind()

    def weergave(self, kr, kind):
        """Hoe het programma eruitziet voor dit kind (vroeger Opties bij het kind). Elke keuze wordt meteen bewaard
        en geldt meteen als dit kind het actieve is; een startargument (--ascii …) gaat voor zolang het programma loopt."""
        kr = kr + ["Weergave"]
        sel = 0
        melding = "Een startargument (bv. --ascii) gaat voor zolang het programma loopt."
        while True:
            inst = self.o.instellingen_van(kind.id)
            items = [("Eenvoudige tekens", {None: "automatisch", True: "aan (ASCII)", False: "uit"}[inst.ascii]),
                     ("Muis", "aan" if inst.muis else "uit"),
                     ("Typrichting in tabellen", "→ naar rechts" if inst.typrichting == 1 else "← naar links"),
                     ("Avatar", "aan" if inst.avatar else "uit"),
                     ("Animaties", "aan" if inst.animaties else "uit"),
                     ("Klok in een eigen venster", "aan" if inst.klokvenster else "uit (de klok in de terminal)")]
            sel = self.lijst(kr, f"Weergave voor {kind.naam}", items, sel, melding)
            if sel is None:
                return
            if sel == 0:
                inst.ascii = {None: True, True: False, False: None}[inst.ascii]
            elif sel == 1:
                inst.muis = not inst.muis
            elif sel == 2:
                inst.typrichting = -inst.typrichting
            elif sel == 3:
                inst.avatar = not inst.avatar
            elif sel == 4:
                inst.animaties = not inst.animaties
            elif sel == 5:
                inst.klokvenster = not inst.klokvenster
            self.o.bewaar_instellingen(kind.id, inst)
            self.app.herlaad_kind()

    def pincode(self, kr, kind, heeft_pin):
        if heeft_pin:
            k = self.s.menu(kr, "Pincode", [("Nieuwe pincode", ""), ("Pincode weghalen", "")])
            if k is None:
                return ""
            if k == 1:
                self.o.zet_pincode(kind.id, None)
                return "De pincode is weggehaald."
        pin = self.s.invoer(kr, f"Nieuwe pincode voor {kind.naam} (4 cijfers):", verborgen=True, max_lengte=4,
                            cijfers=True)
        if pin is None:
            return ""
        if len(pin) != 4:
            return "Een pincode heeft precies 4 cijfers. Er is niets veranderd."
        nog = self.s.invoer(kr, "Typ de pincode nog eens:", verborgen=True, max_lengte=4, cijfers=True)
        if nog != pin:
            return "De twee pincodes waren niet gelijk. Er is niets veranderd."
        self.o.zet_pincode(kind.id, wachtwoord.maak(pin, PIN_ITERATIES))
        return f"{kind.naam} moet nu bij het starten de pincode typen."

    def exporteer_alles(self, kind):
        try:
            r = rapporten.maak_rapport(self.o, kind, rapporten.Periode(date(2000, 1, 1), klok.nu().date(), "alles"))
            csv_pad, _ = rapporten.exporteer(r, documenten_map(), curriculum.indeling())
            json_pad = rapporten.exporteer_alles(self.o, kind, documenten_map())
        except OSError as e:
            return f"Exporteren lukte niet: {e}"
        self.melding("Exporteren", ["✔ Alle gegevens zijn opgeslagen:", "", f"  {csv_pad}", f"  {json_pad}"])
        return ""

    def wissen(self, kr, kind):
        naam = self.s.invoer(kr, f"Typ '{kind.naam}' om ALLES van dit kind te wissen:", max_lengte=20,
                             uitleg=["Dit wist het account, de instellingen en alle antwoorden.",
                                     "Dat kan niet ongedaan gemaakt worden. Exporteer eerst als je iets wil bewaren."])
        if naam != kind.naam:
            if naam is not None:
                self.melding("Wissen", ["De naam klopte niet. Er is niets gewist."])
            return False
        self.o.verwijder_kind(kind.id)
        self.melding("Wissen", [f"✔ Alle gegevens van {kind.naam} zijn gewist."])
        return True
