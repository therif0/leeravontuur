"""Snelrekenen: een klok die meeloopt, records en een verloop over de dagen."""

import time

from ...kern import snelrekenen as SR
from .. import maatje
from ..scherm import BACKSPACE, ENTER, ESC, NIETS, teken_van

HOOFD = "Leeravontuur"


class Snelrekenen:
    klok = staticmethod(time.monotonic)  # tests kunnen dit vervangen

    def __init__(self, app):
        self.app = app
        self.s = app.s
        self.o = app.opslag

    def menu(self):
        kr = [HOOFD, "Snelrekenen"]
        zichtbaar = self.app.inst.timer_zichtbaar
        while True:
            k = self.s.menu(kr, "Wat wil je snel rekenen?", [(naam, "") for naam, _ in SR.SOORTEN.values()])
            if k is None:
                return
            soort = list(SR.SOORTEN)[k]
            modi = ["snel60", "snel20"] if zichtbaar else ["snel20"]
            if len(modi) > 1:
                m = self.s.menu(kr + [SR.SOORTEN[soort][0]], "Hoe?",
                                [("60 seconden", "zoveel mogelijk juist"), ("20 sommen", "zo snel mogelijk")])
                if m is None:
                    continue
                modus = modi[m]
            else:
                modus = "snel20"
            self.ronde(kr + [SR.SOORTEN[soort][0], SR.MODI[modus]], soort, modus)

    def ronde(self, kr, soort, modus):
        s = self.s
        jaar = self.app.inst.leerjaar
        zichtbaar = self.app.inst.timer_zichtbaar
        vorig_record = SR.record(self.o, self.app.kind.id, modus, soort)
        juist = fout = 0
        laatste = ""
        gezicht = "normaal"
        vermijd = set()
        with self.app.sessie(modus, SR.vaardigheid(soort), jaar) as ses:
            start = self.klok()
            o, v = SR.vraag(soort, jaar, vermijd)
            ses.vraag_getoond()
            buf = ""
            while True:
                verstreken = self.klok() - start
                if modus == "snel60" and verstreken >= SR.SECONDEN:
                    break
                if modus == "snel20" and juist + fout >= SR.SOMMEN:
                    break
                if s.te_klein():
                    continue
                s.nieuw(kr, [("Enter", "ok", 10), ("Esc", "stoppen", ESC)])
                if modus == "snel60":
                    rest = max(0, SR.SECONDEN - int(verstreken))
                    balk = "█" * (rest // 3) + "░" * ((SR.SECONDEN - rest) // 3)
                    s.put(2, 4, f"Nog {rest:2d} seconden  {balk}", "accent" if rest > 10 else "fout")
                else:
                    tekst = f"Som {juist + fout + 1} van {SR.SOMMEN}"
                    if zichtbaar:
                        tekst += f"   ·   {int(verstreken) // 60}:{int(verstreken) % 60:02d}"
                    s.put(2, 4, tekst, "accent")
                s.put(4, 4, f"Juist: {juist}    Fout: {fout}", "bold")
                s.put(7, 6, v.tekst + "  ", "bold")
                vx = 8 + len(v.tekst)
                s.tekstvak(7, vx, buf, 10, "veld")
                s.put(10, 6, laatste, "goed" if laatste.startswith("✔") else "fout")
                maatje.teken(self.app, gezicht, ruim=True)
                s.cursor(True, 7, vx + 1 + len(buf))
                k = s.toets(wacht_ms=200)
                if k == NIETS:
                    continue
                if k == ESC:
                    break
                if k in ENTER and buf.strip():
                    getal = o.lees(buf)
                    goed = getal is not None and getal == v.antwoord
                    ses.antwoord(v.sleutel, v.tekst + " ?", buf.strip(), goed, None, verwacht=v.verwacht,
                                 vaardigheid=o.id, leerjaar=v.leerjaar)
                    juist += goed
                    fout += not goed
                    laatste = "✔ juist!" if goed else f"✘ {v.tekst} {v.verwacht}"
                    gezicht = "blij" if goed else "oeps"
                    vermijd.add(v.sleutel)
                    o, v = SR.vraag(soort, jaar, vermijd)
                    ses.vraag_getoond()
                    buf = ""
                elif isinstance(k, int):
                    if k in BACKSPACE:
                        buf = buf[:-1]
                    elif (teken_van(k) or "x") in "0123456789,-−" and len(buf) < 10:
                        buf += teken_van(k)
        s.cursor(False)
        rondes = self.o.sessie_overzicht(self.app.kind.id, modus, SR.vaardigheid(soort))
        if not rondes or rondes[-1]["aantal"] == 0:
            return
        ronde = rondes[-1]
        bonussen = SR.beloon(self.o, self.app.kind.id, modus, soort, ronde, vorig_record)
        self.uitslag(kr, modus, soort, ronde, vorig_record, bonussen)

    def uitslag(self, kr, modus, soort, ronde, vorig_record, bonussen):
        zichtbaar = self.app.inst.timer_zichtbaar
        regels = [(f"Juist: {ronde['juist']} van {ronde['aantal']}", "accent")]
        if zichtbaar:
            regels.append((f"Tijd: {round(ronde['tijd_ms'] / 1000)} seconden", ""))
        for p, reden in bonussen:
            regels.append((f"★ +{p} punten: {reden}", "goed"))
        if vorig_record and not any("record" in r for _, r in bonussen):
            if modus == "snel60":
                regels.append((f"Je record: {vorig_record['juist']} juist in 60 seconden.", "info"))
            elif zichtbaar:
                regels.append((f"Je record: 20 sommen in {round(vorig_record['tijd_ms'] / 1000)} s "
                               f"({vorig_record['juist']} juist).", "info"))
        regels += [("", ""), ("JE LAATSTE RONDES", "accent")]
        verloop = SR.verloop(self.o, self.app.kind.id, modus, soort)
        beste = max(r["juist"] for r in verloop) or 1
        for r in verloop:
            balk = "█" * round(20 * r["juist"] / beste)
            tijd = f"  {round(r['tijd_ms'] / 1000)} s" if zichtbaar and modus == "snel20" else ""
            regels.append((f"  {r['start'][8:10]}/{r['start'][5:7]}  {balk:<20} {r['juist']:2d} juist{tijd}", ""))
        self.s.lezer(kr + ["Uitslag"], regels, [("Enter", "ok", ("ok",))], {k: None for k in (*ENTER, ESC, ("ok",))})

