"""Een oefensessie: houdt de tijd per vraag bij en bewaart elk antwoord."""

import time

from . import punten as P


class Sessie:
    def __init__(self, opslag, kind_id, modus, vaardigheid, leerjaar, na_antwoord=None, eigen_leerjaar=None):
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
        self.laatste_tijd_ms = 0
        self.eigen_leerjaar = eigen_leerjaar or leerjaar
        self.laatste_punten = 0   # punten voor het laatste antwoord (incl. bonus)
        self.op_rij = 0           # aantal juist na elkaar
        self.punten = 0           # totaal in deze sessie

    def vraag_getoond(self):
        """Roep dit één keer op wanneer een nieuwe vraag verschijnt: daar start de tijdmeting."""
        self._start = time.monotonic()

    def antwoord(self, sleutel, vraag, gegeven, juist, diagnose=None, hulp=False, extra=None, verwacht=None):
        tijd_ms = int((time.monotonic() - self._start) * 1000) if self._start is not None else 0
        self._start = None
        al_juist = self.opslag.al_juist(self.kind_id, sleutel)
        self.opslag.bewaar_antwoord(self.id, self.kind_id, self.vaardigheid, self.leerjaar, self.modus, sleutel,
                                    vraag, gegeven, juist, diagnose, tijd_ms, hulp, extra, verwacht)
        self.laatste_tijd_ms = tijd_ms
        self.aantal += 1
        self.juist += bool(juist)
        p, reden = P.voor_antwoord(juist, self.eigen_leerjaar, self.leerjaar, self.modus, al_juist, extra)
        self.op_rij = self.op_rij + 1 if juist else 0
        if p:
            self.opslag.punten_bij(self.kind_id, p, reden, sleutel)
        if juist and self.op_rij % P.OP_RIJ == 0:
            self.opslag.punten_bij(self.kind_id, P.BONUS_OP_RIJ, f"{self.op_rij} juist op rij")
            p += P.BONUS_OP_RIJ
        self.laatste_punten = p
        self.punten += p
        if self.na_antwoord:
            self.na_antwoord()

    def bonus(self, punten, reden):
        self.opslag.punten_bij(self.kind_id, punten, reden)
        self.punten += punten

    def sluit(self):
        if not self.gesloten:
            self.gesloten = True
            self.opslag.sluit_sessie(self.id)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.sluit()
        return False
