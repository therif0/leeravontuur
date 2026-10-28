"""De databank (SQLite): kinderen, instellingen per kind, sessies en antwoorden.

Afspraken:
- Alles wat bewaard wordt, gaat via deze klasse.
- Antwoorden worden alleen toegevoegd, nooit aangepast (een trigger bewaakt dat).
- Elk record heeft een UUID en tijdstempels; het schema groeit via MIGRATIES.
- Lukt bewaren of lezen niet, dan werkt het programma gewoon verder (en meldt het één keer een probleem).
- Elke dag een reservekopie (map 'reserve', ververst bij het afsluiten), en altijd een kopie vóór een migratie. Een beschadigd bestand wordt
  opzij gezet en de nieuwste goede kopie teruggezet.
"""

import json
import shutil
import sqlite3
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from . import instellingen as inst_mod
from . import klok
from .instellingen import Instellingen
from .paden import data_map

BESTAND = "leeravontuur.db"
RESERVE = "reserve"   # map naast de databank met reservekopieën
DAGKOPIEEN = 7        # zoveel dagelijkse kopieën blijven bewaard
MIGRATIEKOPIEEN = 3   # en zoveel kopieën van vóór een migratie

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
    # versie 2: optionele pincode per kind, het juiste antwoord bij elke vraag (voor rapporten)
    """
    ALTER TABLE kinderen ADD COLUMN pincode TEXT;
    ALTER TABLE antwoorden ADD COLUMN verwacht TEXT;
    """,
    # versie 3: de herhaalbak (Leitner): foute onderwerpen komen op latere dagen terug
    """
    CREATE TABLE herhaalbak (
        id          TEXT PRIMARY KEY,
        kind_id     TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        vaardigheid TEXT NOT NULL,
        onderwerp   TEXT NOT NULL,
        data        TEXT NOT NULL,
        bak         INTEGER NOT NULL,
        volgende    TEXT NOT NULL,
        toegevoegd  TEXT NOT NULL,
        gewijzigd   TEXT NOT NULL,
        UNIQUE (kind_id, vaardigheid, onderwerp)
    );
    CREATE INDEX herhaalbak_kind_volgende ON herhaalbak(kind_id, volgende);
    """,
    # versie 4: punten (logboek: elke wijziging met reden) en de avatar per kind
    """
    CREATE TABLE punten (
        id       TEXT PRIMARY KEY,
        kind_id  TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        tijdstip TEXT NOT NULL,
        dag      TEXT NOT NULL,
        punten   INTEGER NOT NULL,
        reden    TEXT NOT NULL,
        sleutel  TEXT
    );
    CREATE INDEX punten_kind ON punten(kind_id, tijdstip);
    CREATE TABLE avatar (
        kind_id   TEXT PRIMARY KEY REFERENCES kinderen(id) ON DELETE CASCADE,
        config    TEXT NOT NULL,
        gewijzigd TEXT NOT NULL
    );
    """,
    # versie 5: de winkel (wat het kind bezit, en pakjes die nog onderweg zijn) en opgeslagen combinaties
    """
    CREATE TABLE bezit (
        kind_id         TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        laag            TEXT NOT NULL,
        sleutel         TEXT NOT NULL,
        gekocht         TEXT NOT NULL,
        prijs           INTEGER NOT NULL,
        geleverd        INTEGER NOT NULL,
        levering        TEXT,
        challenge_juist INTEGER,
        PRIMARY KEY (kind_id, laag, sleutel)
    );
    CREATE TABLE outfits (
        id         TEXT PRIMARY KEY,
        kind_id    TEXT NOT NULL REFERENCES kinderen(id) ON DELETE CASCADE,
        naam       TEXT NOT NULL,
        config     TEXT NOT NULL,
        aangemaakt TEXT NOT NULL
    );
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


def _beschadigd(fout):
    """Is dit een beschadigd bestand (en niet bv. een vergrendelde databank)?"""
    if isinstance(fout, sqlite3.OperationalError):
        return False
    tekst = str(fout).lower()
    return "not a database" in tekst or "malformed" in tekst or "corrupt" in tekst


def _goed(pad):
    """Is dit databankbestand leesbaar en heel?"""
    try:
        con = sqlite3.connect(str(pad))
        try:
            return con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        finally:
            con.close()
    except sqlite3.Error:
        return False


def _ruim_op(map_, patroon, bewaar):
    """Houd alleen de nieuwste `bewaar` bestanden die op het patroon passen."""
    try:
        bestanden = sorted(map_.glob(patroon), key=lambda k: k.stat().st_mtime)
        for oud in bestanden[:-bewaar]:
            oud.unlink()
    except OSError:
        pass


def _json(tekst, standaard):
    """JSON uit de databank lezen; is het beschadigd, dan de standaardwaarde (geen crash)."""
    try:
        return json.loads(tekst)
    except (TypeError, ValueError):
        return standaard


def _nieuw_id():
    return str(uuid.uuid4())


class Opslag:
    def __init__(self, pad=":memory:"):
        self.pad = str(pad)
        self.probleem = None  # tekst als er iets niet bewaard kon worden
        self.con = sqlite3.connect(self.pad, timeout=5)  # wacht even als een ander programma schrijft
        try:
            self.con.row_factory = sqlite3.Row
            self.con.execute("PRAGMA foreign_keys = ON")
            self._migreer()
        except Exception:
            self.con.close()  # anders blijft het bestand vergrendeld (Windows)
            raise

    @classmethod
    def open(cls, pad=None):
        """Opent de databank in de datamap en maakt (één keer per dag) een reservekopie.

        Is het bestand beschadigd, dan wordt het opzij gezet en de nieuwste goede reservekopie teruggezet.
        Lukt openen helemaal niet: een databank in het geheugen + een melding."""
        pad = Path(pad) if pad else data_map() / BESTAND
        try:
            pad.parent.mkdir(parents=True, exist_ok=True)
            try:
                opslag = cls(pad)
                opslag.controleer()
            except sqlite3.DatabaseError as e:
                if not _beschadigd(e):
                    raise
                opslag = cls._herstel(pad)
        except (OSError, sqlite3.Error, OpslagFout) as e:
            opslag = cls(":memory:")
            opslag.probleem = f"Je vooruitgang wordt nu niet bewaard ({e})."
            return opslag
        opslag.dagkopie()
        opslag.zet_om_uit_json(inst_mod.pad())
        return opslag

    def controleer(self):
        """Geeft een sqlite3.DatabaseError als het bestand beschadigd is."""
        uitslag = self.con.execute("PRAGMA quick_check").fetchone()[0]
        if uitslag != "ok":
            self.con.close()
            raise sqlite3.DatabaseError(f"database disk image is malformed ({uitslag})")

    # ---- reservekopieën ---------------------------------------------------------

    def reserve_map(self):
        return Path(self.pad).parent / RESERVE

    def _kopie(self, naam):
        """Een veilige kopie (sqlite-backup, ook terwijl de databank open is). Mag nooit crashen."""
        if self.pad == ":memory:":
            return None
        try:
            map_ = self.reserve_map()
            map_.mkdir(parents=True, exist_ok=True)
            doel = map_ / naam
            kopie = sqlite3.connect(str(doel))
            try:
                self.con.backup(kopie)
            finally:
                kopie.close()
            return doel
        except (OSError, sqlite3.Error):
            return None

    def dagkopie(self):
        """Eén reservekopie per dag; de oudste verdwijnen (er blijven er DAGKOPIEEN)."""
        if self.pad == ":memory:":
            return
        if not (self.reserve_map() / f"leeravontuur-{klok.dag()}.db").exists():
            self._kopie(f"leeravontuur-{klok.dag()}.db")
        _ruim_op(self.reserve_map(), "leeravontuur-????-??-??.db", DAGKOPIEEN)

    @classmethod
    def _herstel(cls, pad):
        """Het bestand is beschadigd: zet het opzij en zet de nieuwste goede reservekopie terug."""
        opzij = pad.with_name(f"{pad.name}.beschadigd-{klok.nu():%Y%m%d-%H%M%S}")
        pad.replace(opzij)
        kopieen = sorted((pad.parent / RESERVE).glob("leeravontuur-*.db"), key=lambda k: k.stat().st_mtime,
                         reverse=True)
        for kopie in kopieen:
            if _goed(kopie):
                shutil.copy2(kopie, pad)
                opslag = cls(pad)
                datum = klok.nu().fromtimestamp(kopie.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
                opslag.probleem = (f"De databank was beschadigd. De reservekopie van {datum} is teruggezet "
                                   f"(het beschadigde bestand: {opzij.name}).")
                return opslag
        opslag = cls(pad)
        opslag.probleem = (f"De databank was beschadigd en er was geen reservekopie. Er is een nieuwe gestart "
                           f"(het beschadigde bestand: {opzij.name}).")
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
        if 0 < huidig < len(MIGRATIES):  # een bestaande databank wordt omgezet: eerst een kopie
            self._kopie(f"leeravontuur-voor-v{len(MIGRATIES)}.db")
            _ruim_op(self.reserve_map(), "leeravontuur-voor-v*.db", MIGRATIEKOPIEEN)
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

    def _lees(self, sql, waarden=()):
        """De rijen van een leesopdracht. Lukt lezen niet (bv. de databank is vergrendeld of beschadigd), dan een
        lege lijst en een melding: het programma mag daardoor nooit crashen."""
        try:
            return self.con.execute(sql, waarden).fetchall()
        except sqlite3.Error as e:
            self.probleem = f"Lezen uit de databank lukte niet ({e})."
            return []

    def _een(self, sql, waarden=(), standaard=None):
        rijen = self._lees(sql, waarden)
        return rijen[0] if rijen else standaard

    def sluit(self):
        """Sluit de databank en ververst de reservekopie van vandaag (zo is een teruggezette kopie zo recent
        mogelijk: van de laatste keer dat het programma gewoon afgesloten werd)."""
        try:
            if self.pad != ":memory:" and self.probleem is None:
                self._kopie(f"leeravontuur-{klok.dag()}.db")
        finally:
            self.con.close()

    # ---- algemeen --------------------------------------------------------------

    def algemeen(self, sleutel, standaard=None):
        rij = self._een("SELECT waarde FROM algemeen WHERE sleutel = ?", (sleutel,))
        return rij[0] if rij else standaard

    def zet_algemeen(self, sleutel, waarde):
        self._schrijf("INSERT INTO algemeen (sleutel, waarde) VALUES (?, ?) "
                      "ON CONFLICT(sleutel) DO UPDATE SET waarde = excluded.waarde", (sleutel, waarde))

    # ---- kinderen en instellingen ---------------------------------------------

    def kinderen(self):
        rijen = self._lees("SELECT id, naam, leerjaar FROM kinderen ORDER BY naam COLLATE NOCASE, aangemaakt")
        return [Kind(r["id"], r["naam"], r["leerjaar"]) for r in rijen]

    def kind(self, kind_id):
        r = self._een("SELECT id, naam, leerjaar FROM kinderen WHERE id = ?", (kind_id,))
        return Kind(r["id"], r["naam"], r["leerjaar"]) if r else None

    def nieuw_kind(self, naam, leerjaar, inst=None):
        inst = replace(inst or Instellingen(), naam=naam, leerjaar=leerjaar).gecontroleerd()
        kind = Kind(_nieuw_id(), inst.naam, inst.leerjaar)
        nu = klok.iso()
        self._schrijf("INSERT INTO kinderen (id, naam, leerjaar, aangemaakt, gewijzigd) VALUES (?, ?, ?, ?, ?)",
                      (kind.id, kind.naam, kind.leerjaar, nu, nu))
        self._schrijf("INSERT INTO instellingen (kind_id, data, gewijzigd) VALUES (?, ?, ?)",
                      (kind.id, self._data(inst), nu))
        return kind

    @staticmethod
    def _data(inst):
        return json.dumps({k: v for k, v in asdict(inst).items() if k not in _IN_KINDEREN}, ensure_ascii=False)

    def instellingen_van(self, kind_id):
        kind = self.kind(kind_id)
        if kind is None:
            raise OpslagFout(f"onbekend kind {kind_id}")
        rij = self._een("SELECT data FROM instellingen WHERE kind_id = ?", (kind_id,))
        data = _json(rij[0], {}) if rij else {}
        if not isinstance(data, dict):
            data = {}
        velden = {f for f in Instellingen.__dataclass_fields__ if f not in _IN_KINDEREN}
        inst = Instellingen(**{k: v for k, v in data.items() if k in velden})
        inst.naam, inst.leerjaar = kind.naam, kind.leerjaar
        return inst.gecontroleerd()

    def bewaar_instellingen(self, kind_id, inst):
        inst = replace(inst).gecontroleerd()
        nu = klok.iso()
        self._schrijf("UPDATE kinderen SET naam = ?, leerjaar = ?, gewijzigd = ? WHERE id = ?",
                      (inst.naam, inst.leerjaar, nu, kind_id))
        self._schrijf("INSERT INTO instellingen (kind_id, data, gewijzigd) VALUES (?, ?, ?) "
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
                        diagnose=None, tijd_ms=0, hulp=False, extra=None, verwacht=None):
        t = klok.nu()
        return self._schrijf(
            "INSERT INTO antwoorden (id, sessie_id, kind_id, tijdstip, dag, vaardigheid, leerjaar, modus, sleutel, "
            "vraag, gegeven, juist, diagnose, tijd_ms, hulp, extra, verwacht) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (_nieuw_id(), sessie_id, kind_id, klok.iso(t), klok.dag(t), vaardigheid, leerjaar, modus, sleutel,
             vraag, gegeven, int(bool(juist)), diagnose, max(0, int(tijd_ms)), int(bool(hulp)),
             json.dumps(extra, ensure_ascii=False) if extra is not None else None, verwacht))

    def telling(self, kind_id, van, tot=None):
        """(aantal, juist) voor een kind tussen twee dagen (JJJJ-MM-DD of date, beide inbegrepen)."""
        van = str(van)
        tot = str(tot) if tot is not None else van
        r = self._een("SELECT COUNT(*), COALESCE(SUM(juist), 0) FROM antwoorden "
                      "WHERE kind_id = ? AND dag BETWEEN ? AND ?", (kind_id, van, tot), (0, 0))
        return r[0], r[1]

    def antwoorden(self, kind_id, van=None, tot=None):
        """Alle antwoorden van een kind, eventueel tussen twee dagen (beide inbegrepen), oudste eerst."""
        if van is None:
            rijen = self._lees("SELECT * FROM antwoorden WHERE kind_id = ? ORDER BY tijdstip, rowid",
                               (kind_id,))
        else:
            rijen = self._lees("SELECT * FROM antwoorden WHERE kind_id = ? AND dag BETWEEN ? AND ? "
                               "ORDER BY tijdstip, rowid", (kind_id, str(van), str(tot or van)))
        return [dict(r) for r in rijen]

    def laatste_antwoorden(self, kind_id, aantal=50):
        """De laatste antwoorden van een kind, nieuwste eerst (het logboek voor de ouder, #24)."""
        rijen = self._lees("SELECT * FROM antwoorden WHERE kind_id = ? ORDER BY tijdstip DESC, rowid DESC LIMIT ?",
                           (kind_id, aantal))
        return [dict(r) for r in rijen]

    def antwoord_met_sleutel(self, kind_id, sleutel, tot):
        """Het laatste antwoord op deze vraag tot en met dit tijdstip (bv. bij een punt in het logboek), of None."""
        r = self._een("SELECT * FROM antwoorden WHERE kind_id = ? AND sleutel = ? AND tijdstip <= ? "
                      "ORDER BY tijdstip DESC, rowid DESC LIMIT 1", (kind_id, sleutel, tot))
        return dict(r) if r else None

    def sessie_overzicht(self, kind_id, modus, vaardigheid):
        """Afgesloten sessies van één soort: [{start, aantal, juist, tijd_ms}], oudste eerst."""
        rijen = self._lees(
                           "SELECT s.id, s.start, COUNT(a.id) AS aantal, COALESCE(SUM(a.juist), 0) AS juist, "
                           "COALESCE(SUM(a.tijd_ms), 0) AS tijd_ms FROM sessies s LEFT JOIN antwoorden a ON a.sessie_id = s.id "
                           "WHERE s.kind_id = ? AND s.modus = ? AND s.vaardigheid = ? AND s.einde IS NOT NULL "
                           "GROUP BY s.id ORDER BY s.start, s.rowid", (kind_id, modus, vaardigheid))
        return [dict(r) for r in rijen]

    def gezien_sleutels(self, kind_id, vaardigheid, sinds):
        """Vraagsleutels die dit kind sinds die dag al kreeg (om herhaling te vermijden)."""
        rijen = self._lees("SELECT DISTINCT sleutel FROM antwoorden WHERE kind_id = ? AND vaardigheid = ? "
                           "AND dag >= ?", (kind_id, vaardigheid, str(sinds)))
        return {r[0] for r in rijen}

    def recente_antwoorden(self, kind_id, vaardigheid, aantal=200, zonder_modi=()):
        zonder = f" AND modus NOT IN ({', '.join('?' * len(zonder_modi))})" if zonder_modi else ""
        rijen = self._lees(f"SELECT * FROM antwoorden WHERE kind_id = ? AND vaardigheid = ?{zonder} "
                           "ORDER BY tijdstip DESC, rowid DESC LIMIT ?", (kind_id, vaardigheid, *zonder_modi, aantal))
        return [dict(r) for r in rijen]

    def recente_antwoorden_van_sessies(self, kind_id, sessie_vaardigheid, aantal=200):
        """De nieuwste antwoorden uit sessies met deze vaardigheid (bv. snelrekenen.tafels), wat de vragen ook waren."""
        rijen = self._lees("SELECT a.* FROM antwoorden a JOIN sessies s ON s.id = a.sessie_id "
                           "WHERE a.kind_id = ? AND s.vaardigheid = ? ORDER BY a.tijdstip DESC, a.rowid DESC LIMIT ?",
                           (kind_id, sessie_vaardigheid, aantal))
        return [dict(r) for r in rijen]

    def al_juist(self, kind_id, sleutel):
        """Had dit kind deze exacte vraag ooit al juist? (dan levert ze geen punten meer op)"""
        r = self._een("SELECT 1 FROM antwoorden WHERE kind_id = ? AND sleutel = ? AND juist = 1 LIMIT 1",
                      (kind_id, sleutel))
        return r is not None

    # ---- punten en avatar --------------------------------------------------------------

    def punten_bij(self, kind_id, punten, reden, sleutel=None):
        if not punten:
            return
        t = klok.nu()
        self._schrijf("INSERT INTO punten (id, kind_id, tijdstip, dag, punten, reden, sleutel) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (_nieuw_id(), kind_id, klok.iso(t), klok.dag(t), int(punten), reden, sleutel))

    def punten_saldo(self, kind_id):
        return self._een("SELECT COALESCE(SUM(punten), 0) FROM punten WHERE kind_id = ?", (kind_id,), (0,))[0]

    def punten_log(self, kind_id, aantal=20):
        rijen = self._lees("SELECT * FROM punten WHERE kind_id = ? ORDER BY tijdstip DESC, rowid DESC LIMIT ?",
                           (kind_id, aantal))
        return [dict(r) for r in rijen]

    def avatar(self, kind_id):
        r = self._een("SELECT config FROM avatar WHERE kind_id = ?", (kind_id,))
        return _json(r[0], None) if r else None

    def bewaar_avatar(self, kind_id, config):
        self._schrijf("INSERT INTO avatar (kind_id, config, gewijzigd) VALUES (?, ?, ?) "
                      "ON CONFLICT(kind_id) DO UPDATE SET config = excluded.config, gewijzigd = excluded.gewijzigd",
                      (kind_id, json.dumps(config, ensure_ascii=False), klok.iso()))

    # ---- winkel --------------------------------------------------------------------

    def bezit(self, kind_id):
        rijen = self._lees("SELECT * FROM bezit WHERE kind_id = ? ORDER BY gekocht", (kind_id,))
        uit = []
        for r in rijen:
            d = dict(r)
            d["levering"] = _json(d["levering"], None) if d["levering"] else None
            uit.append(d)
        return uit

    def zet_bezit(self, kind_id, laag, sleutel, prijs, geleverd, levering=None, challenge_juist=None):
        self._schrijf("INSERT INTO bezit (kind_id, laag, sleutel, gekocht, prijs, geleverd, levering, challenge_juist) "
                      "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(kind_id, laag, sleutel) DO UPDATE SET "
                      "geleverd = excluded.geleverd",
                      (kind_id, laag, sleutel, klok.iso(), int(prijs), int(bool(geleverd)),
                       json.dumps(levering) if levering else None,
                       None if challenge_juist is None else int(bool(challenge_juist))))

    def lever(self, kind_id, laag, sleutel):
        self._schrijf("UPDATE bezit SET geleverd = 1 WHERE kind_id = ? AND laag = ? AND sleutel = ?",
                      (kind_id, laag, sleutel))

    def sinds(self, kind_id, tijdstip):
        """(juiste antwoorden, totale antwoordtijd in ms) sinds een tijdstip."""
        r = self._een("SELECT COALESCE(SUM(juist), 0), COALESCE(SUM(tijd_ms), 0) FROM antwoorden "
                      "WHERE kind_id = ? AND tijdstip >= ?", (kind_id, tijdstip), (0, 0))
        return r[0], r[1]

    def outfits(self, kind_id):
        rijen = self._lees("SELECT * FROM outfits WHERE kind_id = ? ORDER BY aangemaakt", (kind_id,))
        return [dict(r, config=_json(r["config"], {})) for r in rijen]

    def bewaar_outfit(self, kind_id, naam, config):
        self._schrijf("INSERT INTO outfits (id, kind_id, naam, config, aangemaakt) VALUES (?, ?, ?, ?, ?)",
                      (_nieuw_id(), kind_id, naam, json.dumps(config, ensure_ascii=False), klok.iso()))

    def verwijder_outfit(self, outfit_id):
        self._schrijf("DELETE FROM outfits WHERE id = ?", (outfit_id,))

    # ---- herhaalbak ----------------------------------------------------------------

    def herhaal_zet(self, kind_id, vaardigheid, onderwerp, data, bak, volgende):
        nu = klok.iso()
        self._schrijf("INSERT INTO herhaalbak (id, kind_id, vaardigheid, onderwerp, data, bak, volgende, toegevoegd, "
                      "gewijzigd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                      "ON CONFLICT(kind_id, vaardigheid, onderwerp) DO UPDATE SET data = excluded.data, "
                      "bak = excluded.bak, volgende = excluded.volgende, gewijzigd = excluded.gewijzigd",
                      (_nieuw_id(), kind_id, vaardigheid, onderwerp, json.dumps(data, ensure_ascii=False), bak,
                       str(volgende), nu, nu))

    def herhaal_weg(self, kind_id, vaardigheid, onderwerp):
        self._schrijf("DELETE FROM herhaalbak WHERE kind_id = ? AND vaardigheid = ? AND onderwerp = ?",
                      (kind_id, vaardigheid, onderwerp))

    def herhaalbak(self, kind_id, tot_dag=None):
        """Items in de herhaalbak (alleen die tot en met tot_dag aan de beurt zijn, als die gegeven is)."""
        if tot_dag is None:
            rijen = self._lees("SELECT * FROM herhaalbak WHERE kind_id = ? ORDER BY volgende, bak",
                               (kind_id,))
        else:
            rijen = self._lees("SELECT * FROM herhaalbak WHERE kind_id = ? AND volgende <= ? "
                               "ORDER BY volgende, bak", (kind_id, str(tot_dag)))
        uit = []
        for r in rijen:
            d = dict(r)
            d["data"] = _json(d["data"], {})
            uit.append(d)
        return uit

    # ---- ouder, pincodes, wissen ------------------------------------------------

    def ouder_wachtwoord(self):
        return self.algemeen("ouder_wachtwoord")

    def zet_ouder_wachtwoord(self, opgeslagen):
        if opgeslagen is None:
            self._schrijf("DELETE FROM algemeen WHERE sleutel = 'ouder_wachtwoord'")
        else:
            self.zet_algemeen("ouder_wachtwoord", opgeslagen)

    def pincode(self, kind_id):
        r = self._een("SELECT pincode FROM kinderen WHERE id = ?", (kind_id,))
        return r[0] if r else None

    def zet_pincode(self, kind_id, opgeslagen):
        self._schrijf("UPDATE kinderen SET pincode = ?, gewijzigd = ? WHERE id = ?", (opgeslagen, klok.iso(), kind_id))

    def verwijder_kind(self, kind_id):
        """Wist een kind met al zijn gegevens (instellingen, sessies, antwoorden)."""
        self._schrijf("DELETE FROM kinderen WHERE id = ?", (kind_id,))
        if self.algemeen("laatste_kind") == kind_id:
            self._schrijf("DELETE FROM algemeen WHERE sleutel = 'laatste_kind'")

    def sessies(self, kind_id):
        rijen = self._lees("SELECT * FROM sessies WHERE kind_id = ? ORDER BY start", (kind_id,))
        return [dict(r) for r in rijen]
