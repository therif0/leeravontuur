"""Een oefensessie: houdt de tijd per vraag bij en bewaart elk antwoord."""

import time


class Sessie:
    def __init__(self, opslag, kind_id, modus, vaardigheid, leerjaar, na_antwoord=None):
        self.opslag = opslag
        self.kind_id = kind_id
        self.modus = modus
        self.vaardigheid = vaardigheid
        self.leerjaar = leerjaar
        self.na_antwoord = na_antwoord  # bv. om de titelbalk bij te werken
        self.id = opslag.start_sessie(kind_id, modus, vaardigheid, leerjaar)
        self.aantal = 0
        self.juist = 0
        self.gesloten = False
        self._start = None

    def vraag_getoond(self):
        """Roep dit één keer op wanneer een nieuwe vraag verschijnt: daar start de tijdmeting."""
        self._start = time.monotonic()

    def antwoord(self, sleutel, vraag, gegeven, juist, diagnose=None, hulp=False, extra=None):
        tijd_ms = int((time.monotonic() - self._start) * 1000) if self._start is not None else 0
        self._start = None
        self.opslag.bewaar_antwoord(self.id, self.kind_id, self.vaardigheid, self.leerjaar, self.modus, sleutel,
                                    vraag, gegeven, juist, diagnose, tijd_ms, hulp, extra)
        self.aantal += 1
        self.juist += bool(juist)
        if self.na_antwoord:
            self.na_antwoord()

    def sluit(self):
        if not self.gesloten:
            self.gesloten = True
            self.opslag.sluit_sessie(self.id)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.sluit()
        return False
