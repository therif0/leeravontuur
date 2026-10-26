"""De terminal-app: startscherm en hoofdmenu (de vakken komen uit het leerplan: terminal/curriculum)."""

import curses
import json
import os
import time
from dataclasses import replace

from .. import LICENTIE, MAKER, MOTTO, VERSIE
from ..kern import feedback, foutlog, herhaling, klok, leerjaren
from ..kern.instellingen import Instellingen
from ..kern.sessie import Sessie
from .scherm import ENTER, ESC, Scherm, TerugNaar, Vergrendeld
from ..kern.wiskunde.eenheden import OMZETTEN
from . import curriculum as CU
from . import navigatie
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
            try:
                plek = json.loads(self.opslag.algemeen("klokvenster_plek") or "null")
            except ValueError:
                plek = None
            self.s.klokvenster = Klokvenster(plek, lambda p: self.opslag.zet_algemeen("klokvenster_plek", json.dumps(p)))
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
                del self.voorrang[veld]  # zelf aangepast (bv. Schermkleuren): vanaf nu gewoon bewaren
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
                keuzes = [("▶ Verder", self.voorstel()[0][:32], lambda: self.voorstel()[1]()),
                          (f"Herhalen ({te_herhalen})", "wat je moeilijk vond" if te_herhalen else "vandaag niets",
                           self.herhalen),
                          *[(v.label, v.uitleg, lambda v=v: navigatie.vak(self, v, [HOOFD])) for v in CU.VAKKEN],
                          ("Spiekbrieven", "uitleg om terug te kijken", lambda: navigatie.spiekbrieven(
                              self, [HOOFD, "Spiekbrieven"])),
                          ("Mijn avatar", "winkel, kast, punten en schermkleuren", self.mijn_avatar),
                          ("Zeg het ons", "wat vind je leuk of moeilijk?", self.zeg_het_ons),
                          ("Wissel van kind", "iemand anders wil oefenen", self.wissel_van_kind),
                          ("Stoppen", "", None)]
                k = self.s.menu([HOOFD], f"Hallo{' ' + naam if naam else ''}! Wat wil je doen?",
                                [(label, uitleg) for label, uitleg, _ in keuzes], info=info,
                                onder=f"{MAKER} · gratis · {MOTTO.lower()}", extra=self.teken_avatar_menu)
                if k is None or keuzes[k][2] is None:
                    return
                keuzes[k][2]()
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

    def mijn_avatar(self):
        from .schermen.winkel import AvatarSchermen
        AvatarSchermen(self).hub()

    def voorstel(self):
        """(uitleg, actie) voor 'Verder': eerst herhalen, anders de vorige oefening, anders kiezen."""
        n = len(herhaling.aan_de_beurt(self.opslag, self.kind.id))
        if n:
            return f"eerst je {n} herhaalvragen", self.herhalen
        try:
            return self._vorige_voorstel()
        except (KeyError, IndexError, TypeError, ValueError, AttributeError, StopIteration):  # oude of vreemde gegevens
            return self.kiezen()

    def kiezen(self):
        """Geen vorige oefening: het eerste vak openen."""
        return "kies iets om te leren", lambda: navigatie.vak(self, CU.VAKKEN[0], [HOOFD])

    def kruimel_van(self, opslag_id):
        """Hoofdmenu › Vak › Domein › Onderwerp van een bewaarde id (via het leerplan), en het domein."""
        o = CU.van_opslag(opslag_id)[0]
        d = CU.domein_van(o)
        return [HOOFD, CU.vak_van(d).label, d.label, o.label], d

    def _vorige_voorstel(self):
        """De vorige oefening (ook een die nog door een oudere versie bewaard is: het leerplan vindt ze via opslag)."""
        vorige = self.laatste_oefening()
        if not isinstance(vorige, dict):
            return self.kiezen()
        if vorige.get("onderwerp") == "oefenaar" and not 0 <= vorige["niveau"] < len(leerjaren.NIVEAUS):
            return self.kiezen()
        if vorige.get("onderwerp") == "oefenaar":
            from ..kern import catalogus
            o = catalogus.ONDERWERPEN.get(vorige["vaardigheid"])
            if o:
                vorm = {"vrij": "vrij oefenen", "reeks": "reeks van 10"}[vorige["vorm"]]
                kr, d = self.kruimel_van(o.id)
                return (f"{o.naam.lower()} · {vorm}",
                        lambda: Oefenaar(self, kr, [o], d.label).start(o, vorige["vorm"], vorige["niveau"]))
        if vorige.get("onderwerp") == "eenheden":
            vorm = {"vrij": "vrij oefenen", "reeks": "reeks van 10", "tabel": "tabel-oefening"}[vorige["vorm"]]
            kr = self.kruimel_van(OMZETTEN.id)[0][:-1]
            return f"eenheden · {vorm} · {vorige['soort'].lower()}", lambda: Eenheden(self, kr).hervat(vorige)
        return self.kiezen()

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
