"""Rapporten voor ouders: per periode, per dag, per vaardigheid, denkfouten, kalender en export.

Alles hier geeft gewone gegevens of regels (tekst, rol) terug; de weergave kiest de kleuren.
"""

import calendar
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from . import catalogus, herhaling, klok, leerjaren, vaardigheden
from . import snelrekenen as SR

DAGEN = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
           "oktober", "november", "december"]
MODI = {"vrij": "vrij oefenen", "reeks": "reeks van 10", "tabel": "tabel-oefening"}  # ook zo in de CSV (vast)
MODI_RAPPORT = {**MODI, "snel60": "60 seconden", "snel20": "20 sommen"}
SNEL = ("snel60", "snel20")


@dataclass
class Periode:
    van: date
    tot: date
    naam: str

    @property
    def tekst(self):
        if self.van == self.tot:
            return f"{datum(self.van)} ({self.naam})"
        return f"{datum(self.van)} – {datum(self.tot)} ({self.naam})"


def datum(d):
    return d.strftime("%d/%m/%Y")


def begin_schooljaar(d):
    return date(d.year if d.month >= 9 else d.year - 1, 9, 1)


def periodes(vandaag=None):
    v = vandaag or klok.nu().date()
    return [
        Periode(v, v, "vandaag"),
        Periode(v - timedelta(days=v.weekday()), v, "deze week"),
        Periode(v.replace(day=1), v, "deze maand"),
        Periode(v - timedelta(days=29), v, "laatste 30 dagen"),
        Periode(begin_schooljaar(v), v, "dit schooljaar"),
    ]


def lees_datum(tekst, vandaag=None):
    """'24/10/2026', '24-10-2026', '24/10' (dit jaar) of '2026-10-24' → date, of None."""
    t = tekst.strip()
    v = vandaag or klok.nu().date()
    try:
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
        if m:
            return date(int(m[1]), int(m[2]), int(m[3]))
        m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?", t)
        if m:
            jaar = int(m[3]) if m[3] else v.year
            if jaar < 100:
                jaar += 2000
            return date(jaar, int(m[2]), int(m[1]))
    except ValueError:
        return None
    return None


@dataclass
class Rapport:
    kind: object
    periode: Periode
    antwoorden: list
    bronnen: list = field(default_factory=list)       # per antwoord: de vaardigheid, of snelrekenen.<soort>
    aantal: int = 0
    juist: int = 0
    tijd_ms: int = 0
    per_dag: dict = field(default_factory=dict)          # "JJJJ-MM-DD" -> [aantal, juist]
    per_vaardigheid: dict = field(default_factory=dict)  # bron -> {"aantal", "juist", "tijd_ms", "modi": Counter}
    denkfouten: Counter = field(default_factory=Counter)
    status: list = field(default_factory=list)        # [(vaardigheid, status, aantal, laatst, pct)]
    herhaalbak: int = 0
    herhaal_vandaag: int = 0

    @property
    def procent(self):
        return round(100 * self.juist / self.aantal) if self.aantal else 0


def maak_rapport(opslag, kind, periode):
    rijen = opslag.antwoorden(kind.id, periode.van.isoformat(), periode.tot.isoformat())
    r = Rapport(kind, periode, rijen)
    r.status = herhaling.overzicht(opslag, kind.id, list(vaardigheden.REGISTER.values()))
    r.herhaalbak = len(opslag.herhaalbak(kind.id))
    r.herhaal_vandaag = len(herhaling.aan_de_beurt(opslag, kind.id))
    # snelrekenen telt apart: een snelrekensom is bewaard met de vaardigheid van de vraag (bv. de tafels), de sessie
    # met snelrekenen.<soort>; zo staat ook Gemengd bij Gemengd
    snel = {s["id"]: s["vaardigheid"] for s in opslag.sessies(kind.id) if s["modus"] in SNEL}
    for a in rijen:
        bron = snel.get(a.get("sessie_id"), a["vaardigheid"]) if a["modus"] in SNEL else a["vaardigheid"]
        r.bronnen.append(bron)
        r.aantal += 1
        r.juist += a["juist"]
        r.tijd_ms += a["tijd_ms"]
        d = r.per_dag.setdefault(a["dag"], [0, 0])
        d[0] += 1
        d[1] += a["juist"]
        pv = r.per_vaardigheid.setdefault(bron, {"aantal": 0, "juist": 0, "tijd_ms": 0,
                                                              "modi": Counter()})
        pv["aantal"] += 1
        pv["juist"] += a["juist"]
        pv["tijd_ms"] += a["tijd_ms"]
        pv["modi"][a["modus"]] += 1
        if a["diagnose"]:
            r.denkfouten[a["diagnose"]] += 1
        extra = _extra(a)
        if extra.get("vraagstuk"):  # vraagstukken: tips, meteen juist, het klad
            vs = pv.setdefault("vraagstuk", Counter())
            vs["aantal"] += 1
            vs["tips"] += extra.get("tips", 0)
            vs["zonder_tip"] += bool(a["juist"] and not extra.get("tips"))
            vs["meteen"] += bool(a["juist"] and extra.get("eerste_fout") is None)
            vs["klad"] += bool(extra.get("klad"))
            vs["klad_ok"] += bool(extra.get("klad_ok"))
            if extra.get("klad_fout") and extra["klad_fout"] != a["diagnose"]:
                r.denkfouten[extra["klad_fout"]] += 1
    return r


def _extra(a):
    try:
        uit = json.loads(a.get("extra") or "{}")
    except (TypeError, ValueError):
        return {}
    return uit if isinstance(uit, dict) else {}


def _getal(x):
    return f"{x:.1f}".replace(".", ",").replace(",0", "")


def _balk(deel, geheel, breedte=10):
    vol = round(breedte * deel / geheel) if geheel else 0
    return "█" * vol + "░" * (breedte - vol)


def _duur(ms):
    minuten = round(ms / 60000)
    if minuten < 1:
        return "minder dan een minuut"
    if minuten < 60:
        return f"{minuten} minuten"
    return f"{minuten // 60} u {minuten % 60:02d} min"


def naam(bron):
    """De naam van een vaardigheid, of "Snelrekenen: Tafels" voor snelrekenen.tafels."""
    if bron.startswith("snelrekenen.") and bron.split(".", 1)[1] in SR.SOORTEN:
        return f"Snelrekenen: {SR.SOORTEN[bron.split('.', 1)[1]][0]}"
    return catalogus.naam(bron)


def _onderwerp_regels(label, pv, inspring, woord="vragen"):
    n = pv["aantal"]
    uit = [(f"{inspring}{label}: {n} {woord}, {round(100 * pv['juist'] / n)} % juist, "
            f"gemiddeld {round(pv['tijd_ms'] / n / 1000)} s", "bold")]
    modi = " · ".join(f"{MODI_RAPPORT.get(m, m)} {k}" for m, k in pv["modi"].most_common())
    uit.append((f"{inspring}  {modi}", "dim"))
    if pv.get("vraagstuk"):
        vs = pv["vraagstuk"]
        uit.append((f"{inspring}  gemiddeld {_getal(vs['tips'] / vs['aantal'])} tips per vraagstuk · juist zonder "
                    f"tip: {vs['zonder_tip']} · meteen juist: {vs['meteen']} · met klad: {vs['klad']} "
                    f"(helemaal juist: {vs['klad_ok']})", "dim"))
    return uit


def _rang(indeling):
    """Sorteersleutel in de volgorde van het leerplan: (plaats van het onderwerp, snelrekenen na het gewone)."""
    volgorde = {p: i for i, p in enumerate(dict.fromkeys(indeling.values()))}
    return lambda bron: (volgorde.get(indeling.get(bron), len(volgorde)), bron.startswith("snelrekenen."), bron)


def _per_domein(items, indeling, regel):
    """items = [(bron, …)] gesorteerd; per (vak, domein) een kopregel, daaronder regel(label, item)."""
    uit, vorig = [], None
    for item in items:
        vak, domein, label = indeling.get(item[0], ("", "Overig", naam(item[0])))
        if (vak, domein) != vorig:
            uit.append((f"  {vak} › {domein}" if vak else f"  {domein}", "info"))
            vorig = (vak, domein)
        uit += regel(label, item)
    return uit


def regels(r, indeling=None):
    """Het rapport als regels (tekst, rol), voor op het scherm en in het tekstbestand.

    indeling (uit het leerplan): {bewaarde id: (vak, domein, onderwerp)} in de volgorde van het leerplan. Dan staat
    PER ONDERWERP (en de status) per vak en domein; snelrekenen staat apart onder zijn onderwerp. Zonder: een lijst."""
    uit = [(f"Rapport van {r.kind.naam} · {leerjaren.NAMEN[r.kind.leerjaar]}", "accent"),
           (f"Periode: {r.periode.tekst}", "dim"), ("", "")]
    if not r.aantal:
        uit.append(("In deze periode werd er nog niet geoefend.", ""))
        uit += _status_regels(r, indeling)
        return uit
    dagen = len(r.per_dag)
    uit += [("SAMENVATTING", "accent"),
            (f"  Vragen: {r.aantal}    Juist: {r.juist} ({r.procent} %)", "bold"),
            (f"  Geoefend op {dagen} {'dag' if dagen == 1 else 'dagen'} · actieve tijd: {_duur(r.tijd_ms)}", ""),
            (f"  Gemiddeld {round(r.tijd_ms / r.aantal / 1000)} seconden per vraag", ""),
            ("", "")]
    uit.append(("PER DAG", "accent"))
    for dag in sorted(r.per_dag):
        n, j = r.per_dag[dag]
        d = date.fromisoformat(dag)
        uit.append((f"  {DAGEN[d.weekday()]} {d.strftime('%d/%m')}  {_balk(j, n)}  "
                    f"{n:3d} {'vraag ' if n == 1 else 'vragen'}  {round(100 * j / n):3d} % juist", ""))
    uit += [("", ""), ("PER ONDERWERP", "accent")]
    if indeling is None:
        for bron, pv in sorted(r.per_vaardigheid.items(), key=lambda x: -x[1]["aantal"]):
            uit += _onderwerp_regels(naam(bron), pv, "  ")
    else:
        def regel(label, item):
            bron, pv = item
            if bron.startswith("snelrekenen."):
                return _onderwerp_regels(f"{label}, snelrekenen", pv, "    ", "sommen")
            return _onderwerp_regels(label, pv, "    ")
        rang = _rang(indeling)
        uit += _per_domein(sorted(r.per_vaardigheid.items(), key=lambda x: rang(x[0])), indeling, regel)
    if r.denkfouten:
        uit += [("", ""), ("MEEST GEMAAKTE DENKFOUTEN", "accent")]
        for code, k in r.denkfouten.most_common(5):
            uit.append((f"  {k}× {catalogus.denkfout(code)}", ""))
    uit += _status_regels(r, indeling)
    fouten = [a for a in r.antwoorden if not a["juist"]][-10:]
    if fouten:
        uit += [("", ""), ("LAATSTE FOUTEN", "accent")]
        for a in reversed(fouten):
            tijd = a["tijdstip"][8:10] + "/" + a["tijdstip"][5:7] + " " + a["tijdstip"][11:16]
            juist = f" (juist: {a['verwacht']})" if a.get("verwacht") else ""
            uit.append((f"  {tijd}  {a['vraag']}  schreef {a['gegeven'] or '—'}{juist}", ""))
    return uit


def _status_regels(r, indeling=None):
    """Status per vaardigheid (los van de periode) en de herhaalbak; met een indeling per vak en domein."""
    if not r.status:
        return []
    uit = [("", ""), ("STATUS PER VAARDIGHEID (alle tijd)", "accent")]

    def regel(label, item):
        _, (v, st, n, laatst, pct) = item
        rol = "goed" if st == herhaling.BEHEERST else "dim" if st == herhaling.NIET_GEZIEN else ""
        extra = "" if not n else f" · {n} vragen · laatst {datum(laatst)} · laatste 20: {pct} % juist"
        return [(f"{inspring}{label}: {st}{extra}", rol)]

    if indeling is None:
        inspring = "  "
        for rij in r.status:
            uit += regel(rij[0].naam, (rij[0].id, rij))
    else:
        inspring, rang = "    ", _rang(indeling)
        uit += _per_domein(sorted(((rij[0].id, rij) for rij in r.status), key=lambda x: rang(x[0])), indeling, regel)
    uit.append((f"  Herhaalbak: {r.herhaalbak} {'onderwerp' if r.herhaalbak == 1 else 'onderwerpen'}"
                f" ({r.herhaal_vandaag} vandaag aan de beurt)", "info"))
    return uit


def kalender(opslag, kind_id, jaar, maand):
    """De dagen van een maand met (aantal, juist) voor elke dag waarop geoefend werd."""
    laatste = calendar.monthrange(jaar, maand)[1]
    rijen = opslag.antwoorden(kind_id, date(jaar, maand, 1).isoformat(), date(jaar, maand, laatste).isoformat())
    dagen = {}
    for a in rijen:
        d = dagen.setdefault(int(a["dag"][8:10]), [0, 0])
        d[0] += 1
        d[1] += a["juist"]
    return dagen


def kalender_regels(jaar, maand, dagen):
    """Een maandkalender als tekstregels: [(tekst, [(kolom, breedte, rol), …])]."""
    regels_ = [(f"{MAANDEN[maand - 1].capitalize()} {jaar}", [])]
    regels_.append(("  ".join(f"{d:>2}" for d in DAGEN), []))
    for week in calendar.Calendar(firstweekday=0).monthdayscalendar(jaar, maand):
        tekst, kleuren = "", []
        for i, d in enumerate(week):
            stuk = "  " if d == 0 else f"{d:2d}"
            if d in dagen:
                kleuren.append((i * 4, 2, "goedvak"))
            tekst += stuk + ("  " if i < 6 else "")
        regels_.append((tekst, kleuren))
    return regels_


def bestandsnaam(r):
    naam = re.sub(r"[^\w\- ]", "", r.kind.naam).strip() or "kind"
    return f"Leeravontuur - {naam} - {r.periode.van.isoformat()} tot {r.periode.tot.isoformat()}"


def exporteer(r, map_, indeling=None):
    """Schrijft een CSV (alle antwoorden) en een TXT (het rapport). Geeft de twee paden terug.
    De kolommen vak en domein komen achteraan (uit de indeling; snelrekenen via zijn sessie)."""
    map_ = Path(map_)
    map_.mkdir(parents=True, exist_ok=True)
    basis = bestandsnaam(r)
    csv_pad, txt_pad = map_ / f"{basis}.csv", map_ / f"{basis}.txt"
    with open(csv_pad, "w", newline="", encoding="utf-8-sig") as f:  # met BOM: Excel leest dan UTF-8
        w = csv.writer(f, delimiter=";")
        w.writerow(["tijdstip", "onderwerp", "leerjaar", "manier", "vraag", "antwoord", "juist antwoord",
                    "juist", "denkfout", "tijd (s)", "tip gebruikt", "vak", "domein"])
        for a, bron in zip(r.antwoorden, r.bronnen):
            vak, domein, _ = (indeling or {}).get(bron, ("", "", ""))
            w.writerow([a["tijdstip"].replace("T", " ")[:16], catalogus.naam(a["vaardigheid"]),
                        leerjaren.NAMEN.get(a["leerjaar"], a["leerjaar"]), MODI.get(a["modus"], a["modus"]),
                        a["vraag"], a["gegeven"], a.get("verwacht") or "", "ja" if a["juist"] else "nee",
                        catalogus.denkfout(a["diagnose"]) if a["diagnose"] else "",
                        f"{a['tijd_ms'] / 1000:.1f}".replace(".", ","), "ja" if a["hulp"] else "nee", vak, domein])
    txt_pad.write_text("\n".join(t for t, _ in regels(r, indeling)) + "\n", encoding="utf-8")
    return csv_pad, txt_pad


def exporteer_alles(opslag, kind, map_):
    """Alle gegevens van één kind als JSON (recht op inzage/meenemen)."""
    map_ = Path(map_)
    map_.mkdir(parents=True, exist_ok=True)
    naam = re.sub(r"[^\w\- ]", "", kind.naam).strip() or "kind"
    pad = map_ / f"Leeravontuur - {naam} - alle gegevens.json"
    data = {"kind": {"naam": kind.naam, "leerjaar": kind.leerjaar},
            "sessies": opslag.sessies(kind.id), "antwoorden": opslag.antwoorden(kind.id)}
    pad.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return pad
