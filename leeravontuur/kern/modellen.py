"""Visuele modellen als gewone data. De terminal (of later een GUI) tekent ze.

Getallenlijn: van..tot met streepjes om de `stap`, een pijl (aflezen) en markeringen (sprongen).
Een getallenlijn kan inzoomen: het stuk tussen twee streepjes wordt de nieuwe lijn met 10 keer kleinere stappen.
"""

import math
from dataclasses import dataclass, field, replace
from decimal import Decimal


@dataclass
class Getallenlijn:
    van: Decimal
    tot: Decimal
    stap: Decimal
    label_elke: int = 1              # elk hoeveelste streepje een getal krijgt
    pijl: Decimal | None = None      # een pijl die het kind moet aflezen
    markeringen: dict = field(default_factory=dict)  # waarde -> korte tekst (bv. "start")
    eenheid: str = ""                # bv. "°C" (thermometer)
    vulling: Decimal | None = None   # thermometer: gekleurd tot hier

    def streepjes(self):
        uit, x = [], self.van
        while x <= self.tot:
            uit.append(x)
            x += self.stap
        return uit

    def inzoomen(self, rond):
        """Het stuk [rond, rond + stap] wordt de nieuwe lijn, met stappen 10 keer kleiner."""
        nieuwe = self.stap / 10
        return replace(self, van=rond, tot=rond + self.stap, stap=nieuwe, label_elke=5, pijl=None,
                       markeringen={})

    def kan_inzoomen(self, minste_stap):
        return self.stap / 10 >= minste_stap

    def dichtst(self, waarde):
        """Het streepje dat het dichtst bij waarde ligt."""
        return min(self.streepjes(), key=lambda s: abs(s - waarde))


def lijn_rond(van, tot, stap, **kw):
    return Getallenlijn(Decimal(van), Decimal(tot), Decimal(stap), **kw)


@dataclass
class Rooster:
    """Cijferen onder elkaar (+, −, ×). Elk cijfer in een vakje; een komma staat tussen twee vakjes.

    Kolommen tellen van links (0) naar rechts (breedte − 1). Bij + en − staan de getallen uitgelijnd op de
    komma (`rechts` = aantal kolommen na de komma, de komma van de uitkomst staat vast). Bij × staan ze
    rechts uitgelijnd en zet het kind de komma van de uitkomst zelf (`komma_zelf`).
    """
    teken: str                 # "+", "−" of "×"
    gegeven: list              # de getallen als tekst, bv. ["347", "12,5"]
    breedte: int
    rechts: int = 0
    invul: list = field(default_factory=lambda: ["uitkomst"])  # rijen om in te vullen; de laatste = de uitkomst
    verwacht: list = field(default_factory=list)                # wat er in elke invulrij hoort (tekst)
    komma_zelf: bool = False

    def macht(self, kolom):
        """De plaats van een kolom als macht van 10 (0 = eenheden, −1 = tienden …)."""
        return self.breedte - 1 - self.rechts - kolom

    def plaats(self, tekst):
        """({kolom: cijfer}, kolom waarna de komma staat of None) voor een getal in dit rooster."""
        geheel, _, na = tekst.partition(",")
        if self.komma_zelf:  # rechts uitgelijnd
            cijfers = geheel + na
            eerste = self.breedte - len(cijfers)
            komma = self.breedte - 1 - len(na) if na else None
        else:
            eerste = self.breedte - self.rechts - len(geheel)
            cijfers = geheel + na
            komma = self.breedte - self.rechts - 1 if na else None
        return {eerste + i: c for i, c in enumerate(cijfers)}, komma

    def vaste_komma(self):
        return None if self.komma_zelf or not self.rechts else self.breedte - self.rechts - 1

    def lees(self, cellen, komma=None):
        """Leest een ingevulde rij {kolom: cijfer}. Geeft (tekst, None) of (None, melding)."""
        if not cellen:
            return None, "Vul eerst de uitkomst in (de onderste rij)."
        kolommen = sorted(cellen)
        if kolommen[-1] - kolommen[0] + 1 != len(kolommen):
            return None, "Er staat een leeg vakje tussen je cijfers. Vul het in (eventueel met een 0)."
        if self.komma_zelf:
            komma = komma
        else:
            komma = self.vaste_komma()
            eenheden = self.breedte - self.rechts - 1
            if kolommen[-1] < eenheden or kolommen[0] > eenheden:
                return None, "Vul ook de eenheden in (een 0 als het moet)."
        geheel = "".join(cellen[k] for k in kolommen if komma is None or k <= komma)
        na = "".join(cellen[k] for k in kolommen if komma is not None and k > komma)
        if not geheel:
            geheel = "0"
        return geheel + ("," + na if na else ""), None


@dataclass
class Stap:
    """Eén stap van een staartdeling: deel, maal, min of neer."""
    soort: str
    vraag: str
    antwoord: int
    tip: str
    plaats: int                # index van het laatste cijfer van het deeltal dat meedoet
    komma_ervoor: bool = False  # deel: zet eerst een komma in het quotiënt


@dataclass
class Staartdeling:
    deeltal: str               # zoals getoond (aangevuld met nullen als er decimalen bij moeten), bv. "49,40"
    deler: int
    stappen: list
    rest: int = 0

    def cijfers(self):
        return self.deeltal.replace(",", "")

    def komma_index(self):
        """Aantal cijfers voor de komma."""
        return len(self.deeltal.partition(",")[0])

    MARGE = 2  # plaats voor het minteken links

    def kolom(self, i):
        """Tekenkolom van cijfer i van het deeltal."""
        return self.MARGE + 2 * i

    def beeld(self, gedaan):
        """Na `gedaan` stappen: (regels links als tekst, quotiënt als tekst)."""
        k = self.komma_index()
        regels = [{self.kolom(i): c for i, c in enumerate(self.cijfers())}]
        if k < len(self.cijfers()):
            regels[0][self.kolom(k) - 1] = ","
        quotient = ""

        def rechts_op(getal, p, voor=""):
            tekst = str(getal)
            regel = {self.kolom(p - j): c for j, c in enumerate(reversed(tekst))}
            if voor:
                regel[self.kolom(p - len(tekst) + 1) - 2] = voor
            return regel

        for st in self.stappen[:gedaan]:
            if st.soort == "deel":
                quotient += ("," if st.komma_ervoor else "") + str(st.antwoord)
            elif st.soort == "maal":
                regels.append(rechts_op(st.antwoord, st.plaats, "−"))
            elif st.soort == "min":
                links = min(regels[-1]) + (2 if regels[-1].get(min(regels[-1])) == "−" else 0)
                regels.append({x: "─" for x in range(links, self.kolom(st.plaats) + 1)})
                regels.append(rechts_op(st.antwoord, st.plaats))
            elif st.soort == "neer":
                if len(regels) > 1:
                    regels[-1] = rechts_op(st.antwoord, st.plaats)
                else:
                    regels.append(rechts_op(st.antwoord, st.plaats))
        tekst = ["".join(r.get(x, " ") for x in range(max(r) + 1)) for r in regels]
        return tekst, quotient


@dataclass
class Breukbalk:
    """Een blok verdeeld in `noemer` gelijke stukken; `gearceerd` = de nummers van de gearceerde stukken."""
    noemer: int
    gearceerd: set = field(default_factory=set)
    label: str = ""

    @classmethod
    def van(cls, teller, noemer, label=""):
        return cls(noemer, set(range(teller)), label)

    @property
    def teller(self):
        return len(self.gearceerd)

    def vereenvoudig(self):
        """Voeg telkens f stukken samen (f = kleinste deler van teller en noemer). None als het niet kan."""
        g = math.gcd(self.teller, self.noemer)
        if g <= 1:
            return None
        f = next(d for d in range(2, g + 1) if g % d == 0)
        return Breukbalk(self.noemer // f, set(range(self.teller // f)), self.label)


@dataclass
class Breukbalken:
    """Balken onder elkaar, even breed (vergelijken, gelijknamig maken)."""
    balken: list


@dataclass
class Groepjes:
    """Een breuk van een getal: `totaal` bolletjes in `groepen` groepjes; de eerste `gekleurd` groepjes gekleurd."""
    totaal: int
    groepen: int
    gekleurd: int = 0


@dataclass
class Honderdveld:
    """10 × 10 vakjes; `gekleurd` = de nummers 0–99 (rij × 10 + kolom)."""
    gekleurd: set = field(default_factory=set)


@dataclass
class Procentstrook:
    """Een strook met 0 % … 100 % bovenaan en 0 … totaal onderaan; `procent` wordt aangeduid."""
    totaal: Decimal
    procent: Decimal
    eenheid: str = ""
    toon_deel: bool = False  # na het nakijken: ook het deel onder de pijl


@dataclass
class Figuur:
    """Een figuur op een rooster van vakjes van 1 cm². `vakjes` = {(rij, kolom)} helemaal gekleurd,
    `halve` = {(rij, kolom)} half gekleurd (de schuine kant van een driehoek, linksonder gekleurd)."""
    rijen: int
    kolommen: int
    vakjes: set = field(default_factory=set)
    halve: set = field(default_factory=set)
    rand: bool = False  # de omtrek aanduiden (na het nakijken)

    def oppervlakte(self):
        return Decimal(len(self.vakjes)) + Decimal(len(self.halve)) / 2

    def omtrek(self):
        """Het aantal randjes van 1 cm tussen een gekleurd en een wit vakje (alleen voor figuren zonder halve)."""
        return sum((r + dr, k + dk) not in self.vakjes for r, k in self.vakjes
                   for dr, dk in ((0, 1), (0, -1), (1, 0), (-1, 0)))

    def binnenranden(self):
        """De randjes tussen twee gekleurde vakjes (die tellen niet mee bij de omtrek)."""
        return (4 * len(self.vakjes) - self.omtrek()) // 2


KOLOMLETTERS = "ABCDEFGHIJ"


@dataclass
class Kaart:
    """Een schatkaart: een rooster met kolommen A, B, C … en rijen 1, 2, 3 … (rij 1 onderaan), of een
    assenstelsel van −n tot n (`assen`). `punten` = {(x, y): teken of (teken, rol)}; x en y zijn kolom- en
    rijnummers (vanaf 1) of coördinaten."""
    kolommen: int = 10
    rijen: int = 10
    assen: int = 0
    punten: dict = field(default_factory=dict)

    def xs(self):
        return list(range(-self.assen, self.assen + 1)) if self.assen else list(range(1, self.kolommen + 1))

    def ys(self):
        return list(range(-self.assen, self.assen + 1)) if self.assen else list(range(1, self.rijen + 1))

    def naam(self, x, y):
        """C4 op een schatkaart, (3, −2) in een assenstelsel."""
        if self.assen:
            return f"({fmt_geheel(x)}, {fmt_geheel(y)})"
        return f"{KOLOMLETTERS[x - 1]}{y}"


def fmt_geheel(n):
    return f"−{-n}" if n < 0 else str(n)


@dataclass
class Hoek:
    """Een hoek van `graden` (0–180): het ene been naar rechts, het andere draait tegen de klok in."""
    graden: int


# ---- vraagstukken ---------------------------------------------------------------------------------------

@dataclass
class Stuk:
    """Een stukje van een zin in een vraagstuk: tekst, een aanduidbaar gegeven of een sleutelwoord."""
    tekst: str
    gegeven: str | None = None   # id van het gegeven (een getal dat het kind kan aanduiden)
    sleutel: bool = False        # een sleutelwoord ('per', 'samen', 'terug' …): oplichten bij tip 1


@dataclass
class Gegeven:
    id: str
    waarde: Decimal
    tekst: str                   # zoals in het verhaal: '€ 3,20', '750 g', '3/4'
    naam: str                    # waar het voor staat: 'de prijs van 1 kg kersen'
    eenheid: str = ""
    nodig: bool = True


@dataclass
class Rekenstap:
    """Eén stap van de oplossing. De operanden zijn ids van gegevens of eerdere stappen, of vaste getallen."""
    op: str                      # + − × : en 'omzet', 'pct' (a % van b), 'boven' (delen, naar boven), 'heel', 'rest'
    operanden: list
    id: str
    uitkomst: Decimal
    naam: str                    # wat je ermee vindt: 'de prijs van de kersen'
    hint: str                    # tip zonder getallen: 'je weet wat 1 kg kost en hoeveel kg … → ×'
    waarom: str                  # na het nakijken, met getallen
    reken: str = ""              # zo schrijf je de stap: '0,75 × 3,20 = 2,40'
    eenheid: str = ""


@dataclass
class Oplossing:
    """Hoe een oefening opgelost kan worden, in klad-regels: de stappen (Rekenstap, met `reken` = de regel zoals het
    kind ze typt) en de bekende foute paden (code, tekst, uitkomst, waarden, handtekeningen). Zie kern/klad.py."""
    stappen: list
    paden: list = field(default_factory=list)


@dataclass
class Verhaal:
    """Een vraagstuk als data: zinnen (lijsten van Stukken; de laatste is de vraag), gegevens en de oplossing."""
    zinnen: list
    gegevens: dict
    stappen: list
    gevraagd: str
    opties: list                 # wat er gevraagd kan worden (3 keuzes, de juiste zit erbij)
    antwoordzin: tuple           # (voor, na) rond het invulvak
    eenheid: str = ""            # van het antwoord ('€', 'm', 'broodjes' …)
    controle: tuple | None = None  # (laagste, hoogste, uitleg): een antwoord daarbuiten kan niet kloppen
    paden: list = field(default_factory=list)  # foute paden: [(code, tekst, waarde, {stap-id: waarde})]
    soort: str = "getal"         # het antwoord: een getal, een tijdstip ('klok', in minuten) of een tijdsduur ('duur')


@dataclass
class Speur:
    """De Speurneus: het klad van een ander kind bij een vraagstuk, met één fout (of geen)."""
    verhaal: Verhaal
    wie: str                     # wie het oploste
    regels: list                 # het klad, regel per regel; de laatste is de antwoordzin
    fout: int                    # het nummer van de foute regel (vanaf 1), 0 = alles juist
    redenen: list                # 3 mogelijke redenen
    reden: int                   # welke reden juist is (−1 als alles juist is)
    uitleg: str                  # wat er mis is (na het nakijken)


@dataclass
class Keuze:
    """Een vraag bij een vraagstuk met 2 of 3 keuzes (schatten, kan dat kloppen?)."""
    verhaal: Verhaal
    vraag: str
    opties: list
    juist: int
    uitleg: list


@dataclass
class Wijzerklok:
    """Een wijzerklok die `minuten` (na middernacht) aanwijst. De terminal tekent ze rond, met 2 wijzers."""
    minuten: int
    wijzers: bool = True

    def hoeken(self):
        """(hoek uurwijzer, hoek minutenwijzer) in graden, met de klok mee vanaf 12."""
        u, m = divmod(int(self.minuten) % 720, 60)
        return (u + m / 60) * 30, m * 6
