"""De databank (SQLite): kinderen, instellingen per kind, sessies en antwoorden.

Afspraken:
- Alles wat bewaard wordt, gaat via deze klasse.
- Antwoorden worden alleen toegevoegd, nooit aangepast (een trigger bewaakt dat).
- Elk record heeft een UUID en tijdstempels; het schema groeit via MIGRATIES.
- Lukt bewaren niet, dan werkt het programma gewoon verder (en meldt het één keer een probleem).
"""

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from . import instellingen as inst_mod
from . import klok
from .instellingen import Instellingen
from .paden import data_map

BESTAND = "leeravontuur.db"

MIGRATIES = [
    # versie 1: kinderen, instellingen, sessies, antwoorden
    """
    CREATE TABLE algemeen (
        sleutel TEXT PRIMARY KEY,
        waarde  TEXT
    );
    CREATE TABLE kinderen (
        id         TEXT PRIMARY KEY,
        naam       TEXT NOT NULL,
        leerjaar   TEXT NOT NULL,
        aangemaakt TEXT NOT NULL,
        gewijzigd  TEXT NOT NULL
    );
    CREATE TABLE instellingen (
        kind_id   TEXT PRIMARY KEY REFERENCES kinderen(id) ON DELETE CASCADE,
        data      TEXT NOT NULL,
        gewijzigd TEXT NOT NULL
    );
    CREATE TABLE sessies (
        id          TEXT PRIMARY KEY,
        kind_id     TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        modus       TEXT NOT NULL,
        vaardigheid TEXT NOT NULL,
        leerjaar    TEXT NOT NULL,
        start       TEXT NOT NULL,
        einde       TEXT
    );
    CREATE TABLE antwoorden (
        id          TEXT PRIMARY KEY,
        sessie_id   TEXT NOT NULL REFERENCES sessies(id) ON DELETE CASCADE,
        kind_id     TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        tijdstip    TEXT NOT NULL,
        dag         TEXT NOT NULL,
        vaardigheid TEXT NOT NULL,
        leerjaar    TEXT NOT NULL,
        modus       TEXT NOT NULL,
        sleutel     TEXT NOT NULL,
        vraag       TEXT NOT NULL,
        gegeven     TEXT NOT NULL,
        juist       INTEGER NOT NULL,
        diagnose    TEXT,
        tijd_ms     INTEGER NOT NULL,
        hulp        INTEGER NOT NULL DEFAULT 0,
        extra       TEXT
    );
    CREATE INDEX antwoorden_kind_dag ON antwoorden(kind_id, dag);
    CREATE INDEX antwoorden_kind_sleutel ON antwoorden(kind_id, sleutel);
    CREATE TRIGGER antwoorden_alleen_toevoegen BEFORE UPDATE ON antwoorden
    BEGIN
        SELECT RAISE(ABORT, 'antwoorden worden alleen toegevoegd, niet aangepast');
    END;
    """,
]

# deze velden van Instellingen staan in de tabel kinderen, de rest in instellingen.data
_IN_KINDEREN = ("naam", "leerjaar")


class OpslagFout(Exception):
    pass


@dataclass(frozen=True)
class Kind:
    id: str
    naam: str
    leerjaar: str


def _nieuw_id():
    return str(uuid.uuid4())


class Opslag:
    def __init__(self, pad=":memory:"):
        self.pad = str(pad)
        self.probleem = None  # tekst als er iets niet bewaard kon worden
        self.con = sqlite3.connect(self.pad)
        try:
            self.con.row_factory = sqlite3.Row
            self.con.execute("PRAGMA foreign_keys = ON")
            self._migreer()
        except Exception:
            self.con.close()  # anders blijft het bestand vergrendeld (Windows)
            raise

    @classmethod
    def open(cls, pad=None):
        """Opent de databank in de datamap. Lukt dat niet: een databank in het geheugen + een melding."""
        pad = Path(pad) if pad else data_map() / BESTAND
        try:
            pad.parent.mkdir(parents=True, exist_ok=True)
            opslag = cls(pad)
        except (OSError, sqlite3.Error, OpslagFout) as e:
            opslag = cls(":memory:")
            opslag.probleem = f"Je vooruitgang wordt nu niet bewaard ({e})."
            return opslag
        opslag.zet_om_uit_json(inst_mod.pad())
        return opslag

    # ---- schema --------------------------------------------------------------

    @property
    def versie(self):
        return self.con.execute("SELECT versie FROM schema").fetchone()[0]

    def _migreer(self):
        c = self.con
        c.execute("CREATE TABLE IF NOT EXISTS schema (versie INTEGER NOT NULL)")
        if c.execute("SELECT versie FROM schema").fetchone() is None:
            c.execute("INSERT INTO schema VALUES (0)")
            c.commit()
        huidig = self.versie
        if huidig > len(MIGRATIES):
            raise OpslagFout("de databank is van een nieuwere versie van het programma")
        for nr in range(huidig + 1, len(MIGRATIES) + 1):
            try:
                c.executescript(f"BEGIN;\n{MIGRATIES[nr - 1]}\nUPDATE schema SET versie = {nr};\nCOMMIT;")
            except sqlite3.Error:
                try:
                    c.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise

    def _schrijf(self, sql, waarden=()):
        """Een schrijfopdracht die het programma nooit laat crashen."""
        try:
            self.con.execute(sql, waarden)
            self.con.commit()
            return True
        except sqlite3.IntegrityError:
            self.con.rollback()
            raise
        except sqlite3.Error as e:
            self.con.rollback()
            self.probleem = f"Bewaren lukte niet ({e})."
            return False

    def sluit(self):
        self.con.close()

    # ---- algemeen --------------------------------------------------------------

    def algemeen(self, sleutel, standaard=None):
        rij = self.con.execute("SELECT waarde FROM algemeen WHERE sleutel = ?", (sleutel,)).fetchone()
        return rij[0] if rij else standaard

    def zet_algemeen(self, sleutel, waarde):
        self._schrijf("INSERT INTO algemeen VALUES (?, ?) ON CONFLICT(sleutel) DO UPDATE SET waarde = excluded.waarde",
                      (sleutel, waarde))

    # ---- kinderen en instellingen ---------------------------------------------

    def kinderen(self):
        rijen = self.con.execute("SELECT id, naam, leerjaar FROM kinderen ORDER BY naam COLLATE NOCASE, aangemaakt")
        return [Kind(r["id"], r["naam"], r["leerjaar"]) for r in rijen]

    def kind(self, kind_id):
        r = self.con.execute("SELECT id, naam, leerjaar FROM kinderen WHERE id = ?", (kind_id,)).fetchone()
        return Kind(r["id"], r["naam"], r["leerjaar"]) if r else None

    def nieuw_kind(self, naam, leerjaar, inst=None):
        inst = replace(inst or Instellingen(), naam=naam, leerjaar=leerjaar).gecontroleerd()
        kind = Kind(_nieuw_id(), inst.naam, inst.leerjaar)
        nu = klok.iso()
        self._schrijf("INSERT INTO kinderen VALUES (?, ?, ?, ?, ?)", (kind.id, kind.naam, kind.leerjaar, nu, nu))
        self._schrijf("INSERT INTO instellingen VALUES (?, ?, ?)", (kind.id, self._data(inst), nu))
        return kind

    @staticmethod
    def _data(inst):
        return json.dumps({k: v for k, v in asdict(inst).items() if k not in _IN_KINDEREN}, ensure_ascii=False)

    def instellingen_van(self, kind_id):
        kind = self.kind(kind_id)
        if kind is None:
            raise OpslagFout(f"onbekend kind {kind_id}")
        rij = self.con.execute("SELECT data FROM instellingen WHERE kind_id = ?", (kind_id,)).fetchone()
        data = json.loads(rij[0]) if rij else {}
        velden = {f for f in Instellingen.__dataclass_fields__ if f not in _IN_KINDEREN}
        inst = Instellingen(**{k: v for k, v in data.items() if k in velden})
        inst.naam, inst.leerjaar = kind.naam, kind.leerjaar
        return inst.gecontroleerd()

    def bewaar_instellingen(self, kind_id, inst):
        inst = replace(inst).gecontroleerd()
        nu = klok.iso()
        self._schrijf("UPDATE kinderen SET naam = ?, leerjaar = ?, gewijzigd = ? WHERE id = ?",
                      (inst.naam, inst.leerjaar, nu, kind_id))
        self._schrijf("INSERT INTO instellingen VALUES (?, ?, ?) "
                      "ON CONFLICT(kind_id) DO UPDATE SET data = excluded.data, gewijzigd = excluded.gewijzigd",
                      (kind_id, self._data(inst), nu))

    def zet_om_uit_json(self, pad):
        """Fase 1 bewaarde instellingen in een JSON-bestand: maak daar één kind van (eenmalig)."""
        pad = Path(pad)
        if not pad.exists() or self.kinderen():
            return None
        oud = inst_mod.laad_json(pad)
        kind = self.nieuw_kind(oud.naam or "Mij", oud.leerjaar, oud)
        self.zet_algemeen("laatste_kind", kind.id)
        try:
            pad.replace(pad.with_name(pad.name + ".oud"))
        except OSError:
            pass
        return kind

    # ---- sessies en antwoorden -----------------------------------------------

    def start_sessie(self, kind_id, modus, vaardigheid, leerjaar):
        sessie_id = _nieuw_id()
        self._schrijf("INSERT INTO sessies (id, kind_id, modus, vaardigheid, leerjaar, start) VALUES (?, ?, ?, ?, ?, ?)",
                      (sessie_id, kind_id, modus, vaardigheid, leerjaar, klok.iso()))
        return sessie_id

    def sluit_sessie(self, sessie_id):
        self._schrijf("UPDATE sessies SET einde = ? WHERE id = ? AND einde IS NULL", (klok.iso(), sessie_id))

    def bewaar_antwoord(self, sessie_id, kind_id, vaardigheid, leerjaar, modus, sleutel, vraag, gegeven, juist,
                        diagnose=None, tijd_ms=0, hulp=False, extra=None):
        t = klok.nu()
        return self._schrijf(
            "INSERT INTO antwoorden VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_nieuw_id(), sessie_id, kind_id, klok.iso(t), klok.dag(t), vaardigheid, leerjaar, modus, sleutel,
             vraag, gegeven, int(bool(juist)), diagnose, max(0, int(tijd_ms)), int(bool(hulp)),
             json.dumps(extra, ensure_ascii=False) if extra is not None else None))

    def telling(self, kind_id, van, tot=None):
        """(aantal, juist) voor een kind tussen twee dagen (JJJJ-MM-DD of date, beide inbegrepen)."""
        van = str(van)
        tot = str(tot) if tot is not None else van
        r = self.con.execute("SELECT COUNT(*), COALESCE(SUM(juist), 0) FROM antwoorden "
                             "WHERE kind_id = ? AND dag BETWEEN ? AND ?", (kind_id, van, tot)).fetchone()
        return r[0], r[1]

    def antwoorden(self, kind_id):
        rijen = self.con.execute("SELECT * FROM antwoorden WHERE kind_id = ? ORDER BY tijdstip", (kind_id,))
        return [dict(r) for r in rijen]

    def sessies(self, kind_id):
        rijen = self.con.execute("SELECT * FROM sessies WHERE kind_id = ? ORDER BY start", (kind_id,))
        return [dict(r) for r in rijen]
