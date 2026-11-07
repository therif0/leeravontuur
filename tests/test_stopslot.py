"""Het slot op Stoppen aan de kant van het kind (0.23.2): meteen starten bij het kind, het slotscherm en Ctrl-C."""

import os
import random
import signal
import unittest
from unittest import mock

from leeravontuur.kern import stopslot, wachtwoord
from leeravontuur.terminal import app as app_mod
from leeravontuur.terminal.app import App, zonder_onderbreken
from leeravontuur.terminal.nepscherm import HangtFout, NepScherm, ToetsenOp
try:
    from .test_ouder import WW, OuderBasis
    from .test_schermen import ESC, OK, hm
    from . import test_stabiliteit
except ImportError:  # ook zo te starten: python -m unittest discover -s tests
    from test_ouder import WW, OuderBasis
    from test_schermen import ESC, OK, hm
    import test_stabiliteit

PIN = "4321"
TITEL = "Druk op een toets om te beginnen"
SLOT = "Stoppen staat op slot."


class SlotBasis(OuderBasis):
    def setUp(self):
        super().setUp()
        self.oude_pin_iteraties = stopslot.PIN_ITERATIES
        stopslot.PIN_ITERATIES = 1000  # tests snel houden

    def tearDown(self):
        stopslot.PIN_ITERATIES = self.oude_pin_iteraties
        super().tearDown()

    def met_slot(self, *kinderen, pin=PIN):
        """Een databank met een ouderpin; het eerste kind staat op slot."""
        o = self.met_wachtwoord(*kinderen)
        if pin:
            stopslot.zet_pin(o, pin)
        naam = kinderen[0][0]
        stopslot.zet_slot(o, next(k.id for k in o.kinderen() if k.naam == naam), True)
        return o

    def keren(self, scherm, tekst):
        """Hoe vaak een scherm met de tekst verschijnt (opeenvolgende beelden tellen één keer)."""
        return sum(tekst in b and not (i and tekst in scherm.beelden[i - 1]) for i, b in enumerate(scherm.beelden))

    def titels(self, scherm):
        return self.keren(scherm, TITEL)


class TestStartMetSlot(SlotBasis):
    def test_meteen_bij_het_kind(self):
        # ook een kind met een eigen pincode: de ouder koos het al
        o = self.met_slot(("Lotte", "5"), ("Ander", "4"))
        lotte = next(k for k in o.kinderen() if k.naam == "Lotte")
        o.zet_pincode(lotte.id, wachtwoord.maak("1111", 1000))
        scherm, app = self.speel([], opslag=o)
        self.assertEqual(self.titels(scherm), 0)  # geen titelscherm
        self.assertFalse(self.ergens(scherm, "Wie ben jij?"))
        self.assertFalse(self.ergens(scherm, "Typ je pincode"))
        self.assertIn("Hallo Lotte!", scherm.beelden[0])
        self.assertEqual(app.kind.naam, "Lotte")

    def test_zonder_ouderpin_een_gewone_start(self):
        o = self.met_slot(("Lotte", "5"), pin=None)  # bv. de databank aangepast: niemand zit vast
        scherm, _ = self.speel([OK], opslag=o)
        self.assertIn(TITEL, scherm.beelden[0])
        self.assertTrue(self.ergens(scherm, "Wie ben jij?"))

    def test_zonder_slot_een_gewone_start(self):
        o = self.met_wachtwoord(("Lotte", "5"))
        stopslot.zet_pin(o, PIN)
        scherm, _ = self.speel([], opslag=o)
        self.assertIn(TITEL, scherm.beelden[0])


class TestSlotscherm(SlotBasis):
    def test_esc_vraagt_de_ouderpin_en_juist_is_het_titelscherm(self):
        o = self.met_slot(("Lotte", "5"))
        scherm, _ = self.speel([ESC, *PIN, OK, OK], opslag=o)
        self.assertTrue(self.ergens(scherm, SLOT))
        self.assertTrue(self.ergens(scherm, "De ouderpin (4 cijfers)."))
        self.assertEqual(self.titels(scherm), 1)  # na de juiste pin: het titelscherm
        self.assertIn("Wie ben jij?", scherm.beelden[-1])
        self.assertTrue(stopslot.heeft_slot(o, next(k.id for k in o.kinderen() if k.naam == "Lotte")))  # het slot blijft voor de volgende start

    def test_stoppen_in_het_menu_vraagt_ook_de_pin(self):
        o = self.met_slot(("Lotte", "5"))
        scherm, _ = self.speel([hm("Stoppen"), *PIN, OK], opslag=o)
        self.assertTrue(self.ergens(scherm, SLOT))
        self.assertIn(TITEL, scherm.beelden[-1])

    def test_esc_in_het_slotscherm_is_terug_naar_het_hoofdmenu(self):
        o = self.met_slot(("Lotte", "5"))
        scherm, _ = self.speel([ESC, ESC], opslag=o)
        self.assertEqual(self.titels(scherm), 0)
        self.assertIn("Hallo Lotte!", scherm.beelden[-1])

    def test_drie_keer_fout_is_terug_naar_het_hoofdmenu(self):
        o = self.met_slot(("Lotte", "5"))
        scherm, _ = self.speel([ESC, *"1111", OK, *"2222", OK, *"3333", OK], opslag=o)
        self.assertTrue(self.ergens(scherm, "Dat is niet de ouderpin. Probeer nog eens:"))
        self.assertEqual(self.titels(scherm), 0)
        self.assertIn("Hallo Lotte!", scherm.beelden[-1])

    def test_opnieuw_gekozen_kind_met_slot_heeft_weer_het_slot(self):
        o = self.met_slot(("Lotte", "5"))
        # pin juist → titelscherm → Wie ben jij? → Lotte → Esc = weer het slotscherm
        scherm, _ = self.speel([ESC, *PIN, OK, OK, "1", ESC], opslag=o)
        self.assertEqual(self.keren(scherm, SLOT), 2)

    def test_een_kind_zonder_slot_stopt_gewoon(self):
        o = self.met_slot(("Lotte", "5"), ("Vrij", "5"))
        vrij = next(k for k in o.kinderen() if k.naam == "Vrij")
        nr = str(o.kinderen().index(vrij) + 1)
        scherm, _ = self.speel([ESC, *PIN, OK, OK, nr, ESC], opslag=o)
        self.assertEqual(self.keren(scherm, SLOT), 1)
        self.assertIn(TITEL, scherm.beelden[-1])


class TestOuderOpentHetSlot(SlotBasis):
    def test_met_ouder_slot_af_dan_een_gewone_start(self):
        o = self.met_slot(("Lotte", "5"))
        lotte = next(k for k in o.kinderen() if k.naam == "Lotte")
        # --ouder: het wachtwoord → Kinderen (3) › Lotte (1) › Stoppen op slot (rij 9) = uit
        scherm = NepScherm([OK, *WW, OK, "3", "1", ("klik", 9, 10), ESC, ESC, ESC, ESC])
        try:
            App(scherm, o, kleuren=False).start(ouder=True)
        except (ToetsenOp, SystemExit):
            pass
        self.assertTrue(self.ergens(scherm, "kan weer gewoon stoppen"))
        self.assertFalse(stopslot.heeft_slot(o, lotte.id))
        scherm, _ = self.speel([], opslag=o)
        self.assertIn(TITEL, scherm.beelden[0])


class TestCtrlC(SlotBasis):
    def test_genegeerd_zolang_het_kind_met_slot_actief_is(self):
        o = self.met_slot(("Lotte", "5"))
        voor = signal.getsignal(signal.SIGINT)
        gezien = []
        echt = App.hoofdmenu

        def kijk(app):
            gezien.append(signal.getsignal(signal.SIGINT))
            return echt(app)
        with mock.patch.object(App, "hoofdmenu", kijk):
            self.speel([ESC, *PIN, OK, ESC], opslag=o)
        self.assertEqual(gezien, [signal.SIG_IGN])
        self.assertIs(signal.getsignal(signal.SIGINT), voor)  # daarna weer zoals ervoor

    def test_zonder_slot_blijft_ctrl_c(self):
        o = self.met_wachtwoord(("Lotte", "5"))
        gezien = []
        echt = App.hoofdmenu

        def kijk(app):
            gezien.append(signal.getsignal(signal.SIGINT))
            return echt(app)
        with mock.patch.object(App, "hoofdmenu", kijk):
            self.speel([OK, OK, ESC, ESC], opslag=o)
        self.assertEqual(len(gezien), 1)
        self.assertIsNot(gezien[0], signal.SIG_IGN)

    def test_ook_na_een_fout_teruggezet(self):
        voor = {s: signal.getsignal(s) for s in app_mod.ONDERBREKERS}
        with self.assertRaises(RuntimeError):
            with zonder_onderbreken():
                for s in app_mod.ONDERBREKERS:
                    self.assertEqual(signal.getsignal(s), signal.SIG_IGN)
                raise RuntimeError("expres")
        self.assertEqual({s: signal.getsignal(s) for s in app_mod.ONDERBREKERS}, voor)


class TestAapjesMetSlot(SlotBasis):
    """De aap met Stoppen op slot: hij mag niet vastlopen in het slotscherm (en raadt soms de pin)."""
    STAPPEN = test_stabiliteit.TestAapjes.STAPPEN
    SEEDS = range(max(3, len(test_stabiliteit.TestAapjes.SEEDS) // 2))

    def test_aapjes_met_slot(self):
        with mock.patch.dict(os.environ, {"LEERAVONTUUR_DEBUG": "1"}):
            for seed in self.SEEDS:
                rng = random.Random(1000 + seed)
                o = self.met_slot(("Aap", rng.choice(["3", "4", "5", "6", "m1"])), ("Ander", "5"), pin="1234")
                for k in o.kinderen():  # beide kinderen op slot: ook na Wie ben jij? weer het slot
                    stopslot.zet_slot(o, k.id, True)
                gebeurtenissen = test_stabiliteit.TestAapjes.gebeurtenissen(self, rng, self.STAPPEN)
                # zo nu en dan de juiste pin na een Esc, zodat ook het titelscherm en Wie ben jij? meedoen
                for i in range(0, len(gebeurtenissen), 300):
                    gebeurtenissen[i:i] = [ESC, *"1234", OK]
                scherm = NepScherm(gebeurtenissen)
                while True:
                    try:
                        App(scherm, o, kleuren=False).start()
                    except (ToetsenOp, SystemExit):
                        pass
                    except HangtFout as e:
                        self.fail(f"seed {seed}: het programma hangt ({e})\n{scherm.tekst()}")
                    except Exception as e:  # noqa: BLE001
                        raise AssertionError(f"seed {seed}: {type(e).__name__}: {e}\n{scherm.tekst()}") from e
                    if not scherm.toetsen:
                        break
                    scherm.h, scherm.w = 24, 80


if __name__ == "__main__":
    unittest.main()
