"""De terminal-app: startscherm, hoofdmenu, menu's per vak en domein, en opties."""

import curses
import json
import os
import time
from dataclasses import replace

from .. import LICENTIE, MAKER, MOTTO, VERSIE
from ..kern import feedback, foutlog, herhaling, instellingen, klok, leerjaren
from ..kern.instellingen import Instellingen
from ..kern.sessie import Sessie
from .scherm import ENTER, ESC, Scherm, TerugNaar, Vergrendeld
from ..kern.wiskunde import breuken as BR
from ..kern.wiskunde import cijferen as C
from ..kern.wiskunde import getallen as G
from ..kern.wiskunde import grootheden as TG
from ..kern.wiskunde import hoofdrekenen as H
from ..kern.wiskunde import klok as KL
from ..kern.wiskunde import meetkunde as MK
from ..kern.wiskunde import procenten as PR
from ..kern.wiskunde import vraagstukken as VS
from .oefenaar import Oefenaar
from .schermen.eenheden import Eenheden
from .schermen.kinderen import kies_kind
from .venster import Klokvenster

HOOFD = "Leeravontuur"


class App:
    def __init__(self, win, opslag, voorrang=None, kleuren=True):
        """voorrang = instellingen uit de argumenten bij het starten (bv. {"thema": "contrast"})."""
        self.opslag = opslag
        self.voorrang = dict(voorrang or {})
        self.kind = None
        laatste = opslag.kind(opslag.algemeen("laatste_kind") or "")
        self.basis = opslag.instellingen_van(laatste.id) if laatste else Instellingen()
        self.inst = replace(self.basis, **self.voorrang)
        self.s = Scherm(win, self.inst, kleuren)
        self.zet_klokvenster()

    # ---- het actieve kind ------------------------------------------------------

    def activeer(self, kind):
        self.kind = kind
        self.basis = self.opslag.instellingen_van(kind.id)
        self.inst = replace(self.basis, **self.voorrang)
        self.s.inst = self.inst
        self.s.pas_toe()
        self.zet_klokvenster()
        self.opslag.zet_algemeen("laatste_kind", kind.id)
        self.ververs_status()

    def zet_klokvenster(self, aan=None):
        """Het klokvenster (terminal/venster.py) volgens de instelling: aan, of uit (en het proces stoppen).
        Niet met LEERAVONTUUR_KLOKVENSTER=0 (bv. de schermafdrukken); bij de tests (NepScherm) zet de test het zelf."""
        if getattr(self.s.win, "nep", False) and aan is None:
            return
        if aan is None:
            aan = self.inst.klokvenster and os.environ.get("LEERAVONTUUR_KLOKVENSTER", "1") != "0"
        if aan and self.s.klokvenster is None:
            self.s.klokvenster = Klokvenster()
        elif not aan and self.s.klokvenster is not None:
            self.s.klokvenster.stop()
            self.s.klokvenster = None

    def herlaad_kind(self):
        """Na wijzigingen in het ouderdeel: het actieve kind opnieuw laden (of loslaten als het gewist is)."""
        if self.kind is None:
            return
        kind = self.opslag.kind(self.kind.id)
        if kind is None:
            self.kind = None
            self.s.status = self.s.status_kort = ""
        else:
            self.activeer(kind)

    def vandaag(self):
        """(aantal, juist) van vandaag voor het actieve kind."""
        return self.opslag.telling(self.kind.id, klok.dag()) if self.kind else (0, 0)

    def ververs_status(self):
        n, j = self.vandaag()
        self.s.status = f"Vandaag: {j}/{n} juist" if n else ""
        self.s.status_kort = f"{j}/{n} juist" if n else ""

    def bewaar(self):
        """Bewaart de instellingen van het kind. Wat enkel via een startargument geldt, wordt niet bewaard."""
        if not self.kind:
            return
        te_bewaren = replace(self.inst)
        for veld, waarde in list(self.voorrang.items()):
            if getattr(self.inst, veld) == waarde:
                setattr(te_bewaren, veld, getattr(self.basis, veld))
            else:
                del self.voorrang[veld]  # zelf aangepast in Opties: vanaf nu gewoon bewaren
        self.opslag.bewaar_instellingen(self.kind.id, te_bewaren)
        self.basis = te_bewaren
        self.kind = self.opslag.kind(self.kind.id) or self.kind

    def avatar_config(self):
        from ..kern import avatar as A
        return A.geldig(self.opslag.avatar(self.kind.id) if self.kind else None)

    def onthoud_oefening(self, data):
        """Voor 'Verder waar je was'."""
        self.opslag.zet_algemeen(f"laatste_oefening:{self.kind.id}", json.dumps(data, ensure_ascii=False))

    def laatste_oefening(self):
        try:
            return json.loads(self.opslag.algemeen(f"laatste_oefening:{self.kind.id}") or "null")
        except ValueError:
            return None

    def sessie(self, modus, vaardigheid, leerjaar):
        return Sessie(self.opslag, self.kind.id, modus, vaardigheid, leerjaar, na_antwoord=self.ververs_status,
                      eigen_leerjaar=self.inst.leerjaar)

    # ---- schermen ------------------------------------------------------------

    def start(self, ouder=False):
        self.startscherm()
        if self.opslag.probleem:  # bv. een teruggezette reservekopie: meteen zeggen, niet pas in het hoofdmenu
            self.s.lezer([HOOFD, "Let op"], [("! " + self.opslag.probleem, "accent")],
                         [("Enter", "verder", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})
        if ouder:
            from .schermen.ouder import Ouderdeel
            Ouderdeel(self).open()
            return
        kind = kies_kind(self)
        if kind is None:
            return
        self.activeer(kind)
        self.hoofdmenu()

    def wissel_van_kind(self):
        kind = kies_kind(self)
        if kind is not None:
            self.activeer(kind)

    def startscherm(self):
        s = self.s
        while True:
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw([HOOFD], [("Enter", "starten", 10), ("Esc", "stoppen", ESC)])
            h, w = s.maat()
            breedte = 50
            x = (w - breedte) // 2
            y = max(2, (h - 12) // 2)
            regels = [
                ("", ""),
                ("L E E R A V O N T U U R", "accent"),
                ("", ""),
                ("rekenen · taal · Frans", "info"),
                ("", ""),
                (f"Een gratis leerprogramma van {MAKER}", "bold"),
                (MOTTO, "dim"),
                ("", ""),
                ("Druk op een toets om te beginnen", "goed"),
                ("", ""),
            ]
            s.put(y, x, "┌" + "─" * (breedte - 2) + "┐", "accent2")
            for i, (tekst, rol) in enumerate(regels, 1):
                s.put(y + i, x, "│", "accent2")
                s.put(y + i, x + 1 + (breedte - 2 - len(tekst)) // 2, tekst, rol)
                s.put(y + i, x + breedte - 1, "│", "accent2")
            s.put(y + len(regels) + 1, x, "└" + "─" * (breedte - 2) + "┘", "accent2")
            s.put(y + len(regels) + 3, x, f"versie {VERSIE} · {LICENTIE}", "dim")
            s.zones.voeg(1, 0, h - 2, w, 10)
            k = s.toets()
            if k == curses.KEY_RESIZE:
                continue
            if k == ESC:
                raise SystemExit
            return

    def hoofdmenu(self):
        while True:
            if self.kind is None:  # bv. gewist in het ouderdeel
                kind = kies_kind(self)
                if kind is None:
                    return
                self.activeer(kind)
            try:
                naam = self.inst.naam
                n, j = self.vandaag()
                info = []
                from ..kern import winkel as W
                for item in W.lever_pakjes(self.opslag, self.kind.id):
                    info.append(f"Je pakje is aangekomen: {item.naam}! Kijk in je kast.")
                if n:
                    lof = " Goed bezig!" if j >= 0.6 * n else ""
                    info.append(f"Vandaag al {n} {'vraag' if n == 1 else 'vragen'} geoefend, {j} juist.{lof}")
                if self.opslag.probleem:
                    info.append(self.opslag.probleem)
                te_herhalen = len(herhaling.aan_de_beurt(self.opslag, self.kind.id))
                k = self.s.menu([HOOFD], f"Hallo{' ' + naam if naam else ''}! Wat wil je doen?", [
                    ("▶ Verder", self.voorstel()[0][:32]),
                    ("Leren & oefenen", "wiskunde (taal, Frans volgen)"),
                    ("Snelrekenen", "tegen de klok, met records"),
                    (f"Herhalen ({te_herhalen})", "wat je moeilijk vond" if te_herhalen else "vandaag niets"),
                    ("Mijn avatar", "winkel, kast en punten"),
                    ("Spiekbrieven", "uitleg om terug te kijken"),
                    ("Opties", "kleuren, muis, avatar …"),
                    ("Wissel van kind", "iemand anders wil oefenen"),
                    ("Zeg het ons", "wat vind je leuk of moeilijk?"),
                    ("Stoppen", "")], info=info,
                    onder=f"{MAKER} · gratis · {MOTTO.lower()}", extra=self.teken_avatar_menu)
                if k is None or k == 9:
                    return
                actie = [lambda: self.voorstel()[1](), self.leren, self.snelrekenen, self.herhalen,
                         self.mijn_avatar, self.spiekbrieven, self.opties, self.wissel_van_kind,
                         self.zeg_het_ons][k]
                actie()
            except TerugNaar:
                continue
            except (SystemExit, KeyboardInterrupt, Vergrendeld):
                raise
            except Exception as e:  # vangnet: een fout in een scherm sluit het programma niet af
                self.oeps(e)

    def oeps(self, fout):
        """Een onverwachte fout: bewaren in fouten.log, het kind geruststellen en terug naar het menu.
        Drie fouten binnen een minuut: dan toch stoppen (geen eindeloze lus)."""
        if os.environ.get("LEERAVONTUUR_DEBUG"):
            raise fout
        nu = time.monotonic()
        self._fouten = [t for t in getattr(self, "_fouten", []) if nu - t < 60] + [nu]
        foutlog.schrijf(" › ".join(self.s.kruimel), fout)
        if len(self._fouten) >= 3:
            raise fout
        try:
            self.s.cursor(False)
            self.s.lezer([HOOFD, "Oeps"], [
                ("! Oei, er ging iets mis.", "accent"), ("", ""),
                ("Je punten en antwoorden zijn bewaard. Je gaat terug naar het menu.", ""), ("", ""),
                ("Voor de ouder: de fout staat in het foutenlogboek", "dim"),
                (f"  {foutlog.pad()}", "dim"),
                ("  (of start met --fouten om ze te bekijken).", "dim")],
                [("Enter", "naar het menu", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})
        except Exception:
            pass

    def zeg_het_ons(self):
        """Een opmerking van het kind (of de ouder) bewaren in feedback.txt."""
        kr = [HOOFD, "Zeg het ons"]
        tekst = self.s.invoer(kr, "Wat wil je ons vertellen?", max_lengte=70, vrij=True, uitleg=[
            "Iets wat je leuk vindt, te moeilijk of te makkelijk, of iets wat niet werkt.",
            "Het blijft op deze computer; je mama of papa kan het lezen en doorgeven."])
        if not tekst:
            return
        gelukt = feedback.bewaar(self.inst.naam, tekst, "hoofdmenu")
        regels = ([("✔ Bedankt! Je opmerking is bewaard.", "goed")] if gelukt else
                  [("! Bewaren lukte niet, sorry. Zeg het gewoon aan je mama of papa.", "accent")])
        self.s.lezer(kr, regels, [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})

    def teken_avatar_menu(self):
        """Rechts in het hoofdmenu: de avatar en de punten."""
        if not self.inst.avatar:
            return
        from . import avatar as AV
        h, w = self.s.maat()
        x = w - AV.BREEDTE - 2
        AV.teken(self.s, 4, x, self.avatar_config(), "blij")
        self.s.put(4 + AV.HOOGTE + 1, x, f"★ {self.opslag.punten_saldo(self.kind.id)} punten", "accent")

    def snelrekenen(self):
        from .schermen.snelrekenen import Snelrekenen
        Snelrekenen(self).menu()

    def mijn_avatar(self):
        from .schermen.winkel import AvatarSchermen
        AvatarSchermen(self).hub()

    def voorstel(self):
        """(uitleg, actie) voor 'Verder': eerst herhalen, anders de vorige oefening, anders leren."""
        n = len(herhaling.aan_de_beurt(self.opslag, self.kind.id))
        if n:
            return f"eerst je {n} herhaalvragen", self.herhalen
        try:
            return self._vorige_voorstel()
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):  # oude of vreemde gegevens
            return "kies iets om te leren", self.leren

    def _vorige_voorstel(self):
        vorige = self.laatste_oefening()
        if not isinstance(vorige, dict):
            return "kies iets om te leren", self.leren
        if vorige.get("onderwerp") == "oefenaar" and not 0 <= vorige["niveau"] < len(leerjaren.NIVEAUS):
            return "kies iets om te leren", self.leren
        if vorige.get("onderwerp") == "oefenaar":
            from ..kern import catalogus
            o = catalogus.ONDERWERPEN.get(vorige["vaardigheid"])
            if o:
                vorm = {"vrij": "vrij oefenen", "reeks": "reeks van 10"}[vorige["vorm"]]
                kr = [HOOFD, "Leren", "Wiskunde", vorige["domein"]]
                return (f"{o.naam.lower()} · {vorm}",
                        lambda: Oefenaar(self, kr, [o], vorige["domein"]).start(o, vorige["vorm"], vorige["niveau"]))
        if vorige and vorige.get("onderwerp") == "eenheden":
            vorm = {"vrij": "vrij oefenen", "reeks": "reeks van 10", "tabel": "tabel-oefening"}[vorige["vorm"]]
            kr = [HOOFD, "Leren", "Wiskunde", "Eenheden"]
            return f"eenheden · {vorm} · {vorige['soort'].lower()}", lambda: Eenheden(self, kr).hervat(vorige)
        return "kies iets om te leren", self.leren

    def herhalen(self):
        kr = [HOOFD, "Herhalen"]
        items = herhaling.aan_de_beurt(self.opslag, self.kind.id)[:10]
        if not items:
            self.s.lezer(kr, [("Vandaag is er niets te herhalen. Goed zo!", "goed"), ("", ""),
                              ("Vragen die je fout had, komen hier de volgende dagen terug, met nieuwe getallen.",
                               ""), ("Na 3 keer juist zijn ze beheerst.", "dim")],
                         [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})
            return
        from ..kern import catalogus
        eenheden = [i for i in items if i["vaardigheid"] == "wiskunde.eenheden.omzetten"]
        andere = [i for i in items if i["vaardigheid"] in catalogus.ONDERWERPEN]
        res, gestopt = [], False
        if eenheden:
            r, gestopt = Eenheden(self, kr).herhalen(kr, eenheden)
            res += r
        if andere and not gestopt:
            r, _ = Oefenaar(self, kr, [], "Herhalen").herhalen(kr, andere, catalogus.ONDERWERPEN)
            res += r
        items = eenheden + andere
        if not res:
            return
        na = {i["onderwerp"]: i for i in self.opslag.herhaalbak(self.kind.id)}
        beheerst = later = morgen = 0
        for item, r in zip(items, res):
            if item["onderwerp"] not in na:
                beheerst += 1
            elif r["goed"]:
                later += 1
            else:
                morgen += 1
        goed = sum(r["goed"] for r in res)
        regels = [(f"Je herhaalde {len(res)} {'vraag' if len(res) == 1 else 'vragen'}: {goed} juist.",
                   "goed" if goed == len(res) else "accent"), ("", "")]
        if beheerst:
            regels.append((f"✔ {beheerst} {'onderwerp is' if beheerst == 1 else 'onderwerpen zijn'} nu beheerst "
                           f"en {'verdwijnt' if beheerst == 1 else 'verdwijnen'} uit de herhaalbak.", "goed"))
        if later:
            regels.append((f"{later} {'vraag komt' if later == 1 else 'vragen komen'} over een paar dagen nog eens "
                           "terug (om te zien of het blijft zitten).", "info"))
        if morgen:
            regels.append((f"✘ {morgen} {'vraag komt' if morgen == 1 else 'vragen komen'} morgen terug.", "fout"))
        self.s.lezer(kr + ["Klaar"], regels, [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})

    def leren(self):
        kr = [HOOFD, "Leren"]
        while True:
            try:
                k = self.s.menu(kr, "Welk vak?", [("Wiskunde", "rekenen, eenheden, breuken, meetkunde …")])
                if k is None:
                    return
                self.wiskunde(kr + ["Wiskunde"])
            except TerugNaar as t:
                if t.niveau < 1:
                    raise

    def domeinen(self):
        """De domeinen van Wiskunde: (naam, uitleg, onderwerpen of None voor Eenheden, spiekbrief-onderwerp(en))."""
        return [("Eenheden", "lengte, massa, inhoud, oppervlakte, volume", None, None),
                ("Hoofdrekenen", "tafels, plus en min, × 10, dubbel en helft", H.ALLE, H.TAFELS),
                ("Getallen", "plaatswaarde, afronden, deelbaarheid, getallenlijn", G.ALLE, G.PLAATSWAARDE),
                ("Cijferen", "onder elkaar: + − × en de staartdeling", C.ALLE, C.OPTELLEN),
                ("Breuken", "breukbalk, vereenvoudigen, vergelijken, + −, van", BR.ALLE, BR.HERKENNEN),
                ("Procenten", "honderdveld, procent van, korting en btw", PR.ALLE, PR.VELD),
                ("Tijd, geld en snelheid", "de klok, uren en minuten, wisselgeld, km/u", TG.ALLE + [KL.KLOK], [TG.TIJD, KL.KLOK]),
                ("Meetkunde", "oppervlakte en omtrek, formules, hoeken, schatkaart, schaal", MK.ALLE, MK.ROOSTER),
                ("Vraagstukken", "oplossen in 4 stappen, Speurneus, schatten", VS.ALLE, VS.VRAAGSTUKKEN)]

    def wiskunde(self, kr):
        domeinen = self.domeinen()
        while True:
            try:
                k = self.s.menu(kr, "Welk onderwerp?", [(naam, uitleg) for naam, uitleg, *_ in domeinen])
                if k is None:
                    return
                naam, _, onderwerpen, _ = domeinen[k]
                if onderwerpen is None:
                    Eenheden(self, kr + [naam]).menu()
                else:
                    Oefenaar(self, kr + [naam], onderwerpen, naam).menu()
            except TerugNaar as t:
                if t.niveau < len(kr) - 1:
                    raise

    def spiekbrieven(self):
        kr = [HOOFD, "Spiekbrieven"]
        domeinen = self.domeinen()
        while True:
            try:
                k = self.s.menu(kr, "Welke spiekbrief?", [(naam, uitleg) for naam, uitleg, *_ in domeinen])
                if k is None:
                    return
                naam, _, onderwerpen, spiek = domeinen[k]
                if onderwerpen is None:
                    Eenheden(self, kr).spiekbrief(kr + [naam])
                else:
                    Oefenaar(self, kr, onderwerpen, naam).spiekbrief(kr + [naam], spiek)
            except TerugNaar as t:
                if t.niveau < 1:
                    raise

    def opties(self):
        s, inst = self.s, self.inst
        kr = [HOOFD, "Opties"]
        themas = list(instellingen.THEMAS)
        sel, melding = 0, ""
        knoppen = [("↑↓", "kiezen", None), ("Enter", "wijzigen", 10), ("Esc", "klaar", ESC)]
        while True:
            items = [
                ("Naam", inst.naam or "(nog geen naam)"),
                ("Leerjaar", leerjaren.NAMEN[inst.leerjaar] + "  (wijzigen: ouders)"),
                ("Kleuren", instellingen.THEMAS[inst.thema]),
                ("Eenvoudige tekens", {None: "automatisch", True: "aan (ASCII)", False: "uit"}[inst.ascii]),
                ("Muis", "aan" if inst.muis else "uit"),
                ("Typrichting in tabellen", "→ naar rechts" if inst.typrichting == 1 else "← naar links"),
                ("Avatar", "aan" if inst.avatar else "uit"),
                ("Animaties", "aan" if inst.animaties else "uit"),
                ("Klok in een eigen venster", "aan" if inst.klokvenster else "uit (de klok in de terminal)"),
            ]
            if s.te_klein():
                continue
            s.cursor(False)
            s.nieuw(kr, knoppen)
            h, w = s.maat()
            s.put(1, 4, "Kies een optie en druk Enter (of klik) om ze te wijzigen.", "bold")
            for i, (label, waarde) in enumerate(items):
                y = 3 + 2 * i
                s.put(y, 6, f" {label:<24} ", "cursor" if i == sel else "")
                s.put(y, 33, waarde, "accent")
                s.zones.voeg(y, 4, 1, w - 6, ("kies", i))
            y = 3 + 2 * len(items)
            s.put(y, 4, "Voorbeeld:", "dim")
            s.put(y, 15, "✔ juist", "goed")
            s.put(y, 25, "✘ fout", "fout")
            s.put(y, 34, "  5  ", "goedvak")
            s.put(y, 40, "! 6  ", "foutvak")
            s.put(y, 46, " actief ", "cursor")
            if melding:
                s.put(y + 1, 4, melding, "info")
            else:
                s.put(y + 1, 4, "Ook bij het starten: --kleurenblind, --contrast, --ascii … (zie --help)", "dim")
            k = s.toets()
            melding = ""
            if isinstance(k, tuple):
                if k[0] == "kies":
                    sel = k[1]
                    k = 10
                elif k[0] == "scroll":
                    sel = (sel + k[1]) % len(items)
                    continue
                else:
                    continue
            if k in (curses.KEY_UP, ord("k")):
                sel = (sel - 1) % len(items)
            elif k in (curses.KEY_DOWN, ord("j"), 9):
                sel = (sel + 1) % len(items)
            elif k in (ESC, ord("q")):
                self.bewaar()
                return
            elif k in ENTER or k in (curses.KEY_RIGHT, ord(" ")):
                if sel == 0:
                    naam = s.invoer(kr + ["Naam"], "Hoe heet je?", inst.naam)
                    if naam:
                        inst.naam = naam
                elif sel == 1:
                    melding = "Het leerjaar kan een ouder wijzigen: Wissel van kind → Ouders → Kinderen."
                    continue
                elif sel == 2:
                    inst.thema = themas[(themas.index(inst.thema) + 1) % len(themas)]
                elif sel == 3:
                    inst.ascii = {None: True, True: False, False: None}[inst.ascii]
                elif sel == 4:
                    inst.muis = not inst.muis
                elif sel == 5:
                    inst.typrichting = -inst.typrichting
                elif sel == 6:
                    inst.avatar = not inst.avatar
                elif sel == 7:
                    inst.animaties = not inst.animaties
                elif sel == 8:
                    inst.klokvenster = not inst.klokvenster
                    self.zet_klokvenster()
                s.pas_toe()
                self.bewaar()
