"""De schermafdrukken van de handleiding: per beeld welke toetsen het programma krijgt.

Elke functie krijgt een `Draai` (docs/tools/schermafdrukken.py) die al in het hoofdmenu staat (tenzij kind=False)
en roept d.foto(naam) op. Toetsen zijn tmux-namen ("Enter", "Escape", "Up", "Tab", "BSpace"), ("tekst", "…")
voor getypte tekst en ("klik", rij, kolom) voor een muisklik (vanaf 0).
"""

import re
import time

SCENARIOS = {}


def scenario(naam, **opties):
    def zet(f):
        SCENARIOS[naam] = (f, opties)
        return f
    return zet


def wiskunde(d, domein, onderwerp=None):
    """Hoofdmenu → Leren & oefenen → Wiskunde → domein (→ onderwerp)."""
    d.toets("2")
    d.wacht("Welk vak")
    d.toets("1")
    d.wacht("Welk onderwerp")
    d.toets(str(domein))
    if onderwerp is not None:
        d.wacht("wat wil je oefenen")
        d.toets(str(onderwerp))
        d.wacht("Hoe wil je oefenen")


def oefen(d, domein, onderwerp, vorm=1, niveau=2):
    """… → onderwerp → vorm (1 vrij, 2 reeks) → niveau (1 makkelijk … 4 heel moeilijk)."""
    wiskunde(d, domein, onderwerp)
    d.toets(str(vorm))
    d.wacht("Hoe moeilijk")
    d.toets(str(niveau))
    time.sleep(0.3)


def scherm_tekst(d):
    from schermafdrukken import scherm
    return scherm()


def antwoord(d, tekst):
    d.toets(("tekst", tekst), "Enter")


OPNIEUW = ["Escape", "1", "2"]  # stoppen en opnieuw vrij oefenen op Normaal: een nieuwe vraag


# ---- basis -----------------------------------------------------------------------------------------------

@scenario("basis-start", kind=False)
def _(d):
    d.foto("basis-start", "Het startscherm")
    d.toets("Enter")
    d.wacht("Wie ben jij?")
    d.foto("basis-kind-kiezen", "Wie ben jij?")


@scenario("basis-hoofdmenu")
def _(d):
    d.foto("basis-hoofdmenu", "Het hoofdmenu")


@scenario("basis-menus")
def _(d):
    d.toets("2")
    d.wacht("Welk vak")
    d.foto("basis-vak", "Welk vak?")
    d.toets("1")
    d.wacht("Welk onderwerp")
    d.foto("basis-domeinen", "De domeinen van Wiskunde")
    d.toets("2")
    d.wacht("wat wil je oefenen")
    d.foto("basis-onderwerpen", "De onderwerpen van Hoofdrekenen")
    d.toets("1")
    d.wacht("Hoe wil je oefenen")
    d.foto("basis-vorm", "Hoe wil je oefenen?")
    d.toets("1")
    d.wacht("Hoe moeilijk")
    d.foto("basis-niveau", "Hoe moeilijk?")


@scenario("basis-oefenen")
def _(d):
    oefen(d, 2, 1)
    d.wacht("Vrij oefenen")
    d.foto("basis-vraag", "Een vraag")
    d.toets("?")
    d.foto("basis-tip", "Een tip met ?")
    vraag = re.search(r"(\d+) ([×:]) (\d+) =", scherm_tekst(d))
    a, op, b = int(vraag.group(1)), vraag.group(2), int(vraag.group(3))
    antwoord(d, str(a * b if op == "×" else a // b))
    d.foto("basis-juist", "Een juist antwoord")
    d.toets("Enter")
    antwoord(d, "1")
    d.foto("basis-fout", "Een fout antwoord, met uitleg")


@scenario("basis-reeks")
def _(d):
    oefen(d, 2, 1, vorm=2)
    d.wacht("Vraag 1 van 10")
    d.foto("basis-reeks-vraag", "Een reeks van 10")
    for i in range(10):
        vraag = re.search(r"(\d+) ([×:]) (\d+) =", scherm_tekst(d))
        juist = i not in (3, 7) and vraag
        if juist:
            a, op, b = int(vraag.group(1)), vraag.group(2), int(vraag.group(3))
            antwoord(d, str(a * b if op == "×" else a // b))
        else:
            antwoord(d, "1")
        d.toets("Enter")
    d.wacht("Je score")
    d.foto("basis-reeks-rapport", "Het rapport na een reeks")
    d.toets("f")
    d.foto("basis-fouten-opnieuw", "Fouten opnieuw")


# ---- eenheden --------------------------------------------------------------------------------------------

def eenheden(d, vorm, soort, niveau=2):
    wiskunde(d, 1)
    d.wacht("Hoe wil je oefenen")
    d.toets(str(vorm))
    d.wacht("Welke eenheden")
    d.toets(str(soort))
    d.wacht("Hoe moeilijk")
    d.toets(str(niveau))
    time.sleep(0.3)


@scenario("eenheden-menu")
def _(d):
    wiskunde(d, 1)
    d.wacht("Hoe wil je oefenen")
    d.foto("eenheden-vorm", "Eenheden: hoe wil je oefenen?")
    d.toets("1")
    d.wacht("Welke eenheden")
    d.foto("eenheden-soort", "Welke eenheden?")
    d.toets("7")
    d.wacht("Spatie")
    d.toets("Down", "Space", "Down", "Space")
    d.foto("eenheden-zelf", "Zelf eenheden kiezen")


@scenario("eenheden-vrij")
def _(d):
    eenheden(d, 1, 2)
    d.wacht(r"\d (\w+) +=")
    d.foto("eenheden-vraag", "Een omzetting")
    m = re.search(r"([\d,]+) (\w+) += +(\w+)", scherm_tekst(d))
    from leeravontuur.kern.wiskunde import eenheden as E
    from decimal import Decimal
    getal, van, naar = Decimal(m.group(1).replace(",", ".")), m.group(2), m.group(3)
    juist = getal.scaleb(E.MACHT[van] - E.MACHT[naar])
    fout = juist.scaleb(1)  # één kolom te ver
    antwoord(d, f"{fout.normalize():f}".replace(".", ","))
    d.foto("eenheden-fout", "Een denkfout: een kolom te ver")


def vul_tabel(d, soort):
    """Leest de tabelvraag van het scherm en vult de tabel juist in: cijfers, komma en antwoord."""
    from decimal import Decimal
    from leeravontuur.kern.getal import fmt
    from leeravontuur.kern.wiskunde import eenheden as E
    m = re.search(r"([\d,]+) (\S+) += +\? +(\S+)", scherm_tekst(d))
    getal, van, naar = Decimal(m.group(1).replace(",", ".")), m.group(2), m.group(3)
    v = E.Omzetting(soort, van, naar, getal)
    machten = [k for _, k, _ in E.TABELLEN[soort]]
    verw = E.verwachte_cijfers(v)
    eerste = machten.index(max(verw))
    d.toets(*["Tab"] * eerste)
    for k in sorted(verw, reverse=True):
        d.toets(("tekst", str(verw[k])))
    plek = min(eerste + len(verw), len(machten) - 1)  # de cursor staat nu na het laatste cijfer
    komma = E.kolom(soort, naar)
    d.toets(*(["Left"] * (plek - komma) if plek > komma else ["Tab"] * (komma - plek)))
    d.toets(",", "Down", ("tekst", fmt(v.antwoord)))


@scenario("eenheden-tabel")
def _(d):
    eenheden(d, 3, 2)
    d.wacht("Typrichting")
    d.foto("eenheden-tabel", "De tabel-oefening")
    vul_tabel(d, "lengte")
    d.foto("eenheden-tabel-bezig", "De tabel ingevuld, met de komma en het antwoord")
    d.toets("Enter")
    d.foto("eenheden-tabel-juist", "Nagekeken")


@scenario("eenheden-oppervlakte")
def _(d):
    eenheden(d, 3, 4)
    d.wacht("Typrichting")
    vul_tabel(d, "oppervlakte")
    d.toets("Enter")
    d.foto("eenheden-oppervlakte", "De tabel voor oppervlakte: 2 vakjes per eenheid")


@scenario("eenheden-volume")
def _(d):
    eenheden(d, 3, 5, niveau=3)
    d.wacht("Typrichting")
    d.foto("eenheden-volume", "De tabel voor volume")


@scenario("eenheden-spiekbrief")
def _(d):
    wiskunde(d, 1)
    d.wacht("Hoe wil je oefenen")
    d.toets("4")
    d.wacht("Hoe werkt omzetten")
    d.foto("eenheden-spiekbrief", "De spiekbrief van Eenheden")


# ---- hoofdrekenen ----------------------------------------------------------------------------------------

def volgende(d, fout="1"):
    """Een (fout) antwoord geven en naar de volgende vraag."""
    antwoord(d, fout)
    d.toets("Enter")


@scenario("hoofdrekenen")
def _(d):
    oefen(d, 2, 2)
    d.wacht("Vrij oefenen")
    d.foto("hoofdrekenen-plusmin", "Optellen en aftrekken")
    antwoord(d, "1")
    d.foto("hoofdrekenen-plusmin-uitleg", "De uitleg met een strategie")


@scenario("hoofdrekenen-maal10")
def _(d):
    oefen(d, 2, 3)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("hoofdrekenen-maal10", "× en : met 10, 100, 1000")


@scenario("hoofdrekenen-dubbel")
def _(d):
    oefen(d, 2, 4)
    d.wacht("Vrij oefenen")
    d.foto("hoofdrekenen-dubbel", "Verdubbelen en halveren")


# ---- getallen --------------------------------------------------------------------------------------------

@scenario("getallen-plaatswaarde")
def _(d):
    oefen(d, 3, 1)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("getallen-plaatswaarde", "Plaatswaarde")


@scenario("getallen-afronden")
def _(d):
    oefen(d, 3, 2)
    d.wacht("Rond")
    d.foto("getallen-afronden", "Afronden")


@scenario("getallen-deelbaarheid")
def _(d):
    oefen(d, 3, 3)
    d.wacht("Vrij oefenen")
    d.zoek("deelbaar door", ["Escape", "1", "2"])
    antwoord(d, "nee")
    d.foto("getallen-deelbaarheid", "Deelbaarheid")


@scenario("getallen-lijn")
def _(d):
    oefen(d, 3, 4)
    d.wacht("Vrij oefenen")
    d.zoek("Duid", OPNIEUW)
    d.foto("getallen-lijn-aanduiden", "Aanduiden op de getallenlijn")


@scenario("getallen-lijn-zoom")
def _(d):
    from decimal import Decimal
    oefen(d, 3, 4)
    d.wacht("Vrij oefenen")
    for _ in range(40):  # een getal dat tussen twee streepjes ligt
        d.zoek("Duid", OPNIEUW)
        t = scherm_tekst(d)
        x = Decimal(re.search(r"Duid (-?[\d,]+) aan", t).group(1).replace(",", "."))
        regels = t.split("\n")
        lijn = next(i for i, r in enumerate(regels) if r.count("┼") > 3)
        getallen = [Decimal(g.replace(",", ".")) for g in re.findall(r"-?\d+(?:,\d+)?", regels[lijn + 1])]
        van, tot, n = getallen[0], getallen[-1], regels[lijn].count("┼") - 1
        stap = (tot - van) / n
        if (x - van) % stap:
            break
        d.toets(*OPNIEUW)
    d.toets(*["Right"] * int((x - van) / stap), "+")
    d.foto("getallen-lijn-zoom", "Ingezoomd op de getallenlijn")


@scenario("getallen-lijn-aflezen")
def _(d):
    oefen(d, 3, 4, niveau=3)
    d.wacht("Vrij oefenen")
    d.zoek("Welk getal staat bij de pijl|°C", OPNIEUW[:2] + ["3"])
    antwoord(d, "1")
    d.foto("getallen-lijn-aflezen", "Aflezen op de getallenlijn of de thermometer")


# ---- cijferen --------------------------------------------------------------------------------------------

def rooster_getallen(d):
    """De getallen in het rooster (cijfers met een spatie ertussen), van boven naar onder."""
    uit = []
    for regel in scherm_tekst(d).split("\n")[8:20]:
        stuk = regel[8:44]
        if re.fullmatch(r"[\s+−×]*[\d ,]+", stuk) and re.search(r"\d", stuk):
            uit.append(stuk.replace("+", "").replace("−", "").replace("×", "").replace(" ", ""))
    return uit


@scenario("cijferen-optellen")
def _(d):
    oefen(d, 4, 1)
    d.wacht("rechts naar links")
    d.foto("cijferen-optellen", "Cijferend optellen in het rooster")
    getallen = rooster_getallen(d)
    som = str(sum(int(g.replace(",", "")) for g in getallen[:2]))
    d.toets(("tekst", som[-1]))
    d.toets("?")
    d.foto("cijferen-optellen-hulp", "Hulp bij een vakje met ?")


@scenario("cijferen-vermenigvuldigen")
def _(d):
    oefen(d, 4, 3)
    d.wacht("rechts naar links")
    d.foto("cijferen-vermenigvuldigen", "Cijferend vermenigvuldigen")


@scenario("cijferen-staart")
def _(d):
    oefen(d, 4, 4)
    d.wacht("Stap 1")
    d.foto("cijferen-staart", "De staartdeling: stap 1")
    rest = 0
    for _ in range(6):
        t = scherm_tekst(d)
        m = re.search(r"Stap \d+: (.*?)(?:  |$)", t, re.M)
        if not m:
            break
        vraag = m.group(1)
        if g := re.search(r"Hoeveel keer gaat (\d+) in (\d+)", vraag):
            uit = int(g.group(2)) // int(g.group(1))
        elif g := re.search(r"(\d+) × (\d+) =", vraag):
            uit = int(g.group(1)) * int(g.group(2))
        elif g := re.search(r"(\d+) − (\d+) =", vraag):
            uit = rest = int(g.group(1)) - int(g.group(2))
        elif g := re.search(r"Haal de (\d) neer", vraag):
            uit = rest * 10 + int(g.group(1))
        else:
            break
        antwoord(d, str(uit))
    d.foto("cijferen-staart-bezig", "De staartdeling groeit mee")


# ---- breuken ---------------------------------------------------------------------------------------------

@scenario("breuken-arceren")
def _(d):
    oefen(d, 5, 1)
    d.wacht("Vrij oefenen")
    d.zoek("Arceer", OPNIEUW)
    m = re.search(r"Arceer (\d+)/(\d+)", scherm_tekst(d))
    t = int(m.group(1))
    d.foto("breuken-arceren", "Arceren op de breukbalk")
    for i in range(t):
        d.toets("Space", "Right")
    d.foto("breuken-arceren-bezig", "Stukken gearceerd")
    d.toets("Enter")
    d.foto("breuken-arceren-juist", "Nagekeken")


@scenario("breuken-vereenvoudigen")
def _(d):
    oefen(d, 5, 2)
    d.wacht("Vrij oefenen")
    d.zoek("Vereenvoudig", OPNIEUW)
    m = re.search(r"Vereenvoudig (\d+)/(\d+)", scherm_tekst(d))
    t, n = int(m.group(1)), int(m.group(2))
    import math
    g = 2 if (t % 2 == 0 and n % 2 == 0 and math.gcd(t, n) > 2) else math.gcd(t, n)
    antwoord(d, f"{t // g}/{n // g}")  # (soms) maar half vereenvoudigd
    d.foto("breuken-vereenvoudigen", "Vereenvoudigen")


@scenario("breuken-vergelijken")
def _(d):
    oefen(d, 5, 3)
    d.wacht("Vrij oefenen")
    d.foto("breuken-vergelijken", "Breuken vergelijken")
    antwoord(d, ">")
    d.foto("breuken-vergelijken-uitleg", "Vergelijken: nagekeken")


@scenario("breuken-optellen")
def _(d):
    oefen(d, 5, 4)
    d.wacht("Vrij oefenen")
    d.zoek(r"\d+/\d+ \+ \d+/\d+", OPNIEUW)
    m = re.search(r"(\d+)/(\d+) \+ (\d+)/(\d+)", scherm_tekst(d))
    a, b, c, e = map(int, m.groups())
    d.foto("breuken-optellen", "Breuken optellen")
    antwoord(d, f"{a + c}/{b + e}")  # de klassieke fout: tellers en noemers opgeteld
    d.foto("breuken-optellen-fout", "Tellers én noemers opgeteld: de balken tonen waarom")


@scenario("breuken-van")
def _(d):
    oefen(d, 5, 5)
    d.wacht("Vrij oefenen")
    d.zoek(r"\d+/\d+ van \d+", OPNIEUW)
    d.foto("breuken-van", "Een breuk van een getal")
    antwoord(d, "1")
    d.foto("breuken-van-uitleg", "Een breuk van een getal: de groepjes")


@scenario("breuken-kommagetal")
def _(d):
    oefen(d, 5, 6)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("breuken-kommagetal", "Breuk en kommagetal")


# ---- procenten -------------------------------------------------------------------------------------------

@scenario("procenten-veld")
def _(d):
    oefen(d, 6, 1)
    d.wacht("Vrij oefenen")
    d.zoek(r"Kleur \d+ %", OPNIEUW)
    pct = int(re.search(r"Kleur (\d+) %", scherm_tekst(d)).group(1))
    d.foto("procenten-veld", "Kleuren in het honderdveld")
    for _ in range(pct // 10):
        d.toets("r", "Down")
    for _ in range(pct % 10):
        d.toets("Space", "Right")
    d.foto("procenten-veld-bezig", "Hele rijen met r, losse vakjes met spatie")
    d.toets("Enter")
    d.foto("procenten-veld-juist", "Nagekeken")


@scenario("procenten-omzetten")
def _(d):
    oefen(d, 6, 2)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("procenten-omzetten", "Procent, breuk en kommagetal")


@scenario("procenten-van")
def _(d):
    oefen(d, 6, 3)
    d.wacht("Vrij oefenen")
    d.zoek(r"\d+ % van \d+ =", OPNIEUW)
    pct = re.search(r"(\d+) % van", scherm_tekst(d)).group(1)
    d.foto("procenten-van", "Procent van een getal, met de procentstrook")
    antwoord(d, pct)  # het percentage als antwoord
    d.foto("procenten-van-fout", "Het percentage als antwoord gegeven")


@scenario("procenten-korting")
def _(d):
    oefen(d, 6, 4, niveau=3)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("procenten-korting", "Korting en btw")


# ---- tijd, geld en snelheid ------------------------------------------------------------------------------

@scenario("tijd-gemengd")
def _(d):
    oefen(d, 7, 1)
    d.wacht("Vrij oefenen")
    d.zoek(r"min = \? u \? min", OPNIEUW)
    d.foto("tijd-gemengd", "Minuten omzetten in uren en minuten")
    minuten = int(re.search(r"(\d+) min = \? u", scherm_tekst(d)).group(1))
    u, m = divmod(minuten, 100)  # de klassieke fout: rekenen met 100
    antwoord(d, f"{u} u {m} min" if m < 60 else "1 u")
    d.foto("tijd-gemengd-fout", "Gerekend met 100 in plaats van 60")


@scenario("tijd-eindtijd")
def _(d):
    oefen(d, 7, 1)
    d.wacht("Vrij oefenen")
    d.zoek("Je vertrekt om", OPNIEUW)
    d.foto("tijd-eindtijd", "Hoe laat kom je aan?")
    antwoord(d, "12:00")
    d.foto("tijd-eindtijd-uitleg", "Aankomstuur: nagekeken")


@scenario("tijd-geld")
def _(d):
    oefen(d, 7, 2)
    d.wacht("Vrij oefenen")
    d.zoek("terug", OPNIEUW)
    d.foto("tijd-geld", "Wisselgeld")
    antwoord(d, "1")
    d.foto("tijd-geld-uitleg", "Wisselgeld: de uitleg")


@scenario("tijd-snelheid")
def _(d):
    oefen(d, 7, 3, niveau=3)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("tijd-snelheid", "Snelheid")


# ---- meetkunde -------------------------------------------------------------------------------------------

@scenario("meetkunde-rooster")
def _(d):
    oefen(d, 8, 1)
    d.wacht("Vrij oefenen")
    d.zoek("omtrek", OPNIEUW)
    d.foto("meetkunde-omtrek", "De omtrek op het cm²-rooster")
    antwoord(d, "1")
    d.foto("meetkunde-omtrek-uitleg", "Na het nakijken: de omtrek aangeduid")


@scenario("meetkunde-driehoek")
def _(d):
    oefen(d, 8, 1)
    d.wacht("Vrij oefenen")
    d.zoek("half vakje", OPNIEUW)
    d.foto("meetkunde-driehoek", "Een driehoek met halve vakjes")


@scenario("meetkunde-formules")
def _(d):
    oefen(d, 8, 2, niveau=3)
    d.wacht("Vrij oefenen")
    d.zoek("cirkel", OPNIEUW[:2] + ["3"])
    antwoord(d, "1")
    d.foto("meetkunde-formules", "Formules: de cirkel")


@scenario("meetkunde-hoek")
def _(d):
    oefen(d, 8, 3)
    d.wacht("Vrij oefenen")
    d.zoek("Wat voor hoek is dit", OPNIEUW)
    d.foto("meetkunde-hoek", "Wat voor hoek is dit?")
    antwoord(d, "recht")
    d.foto("meetkunde-hoek-uitleg", "Een hoek: nagekeken")


@scenario("meetkunde-schatkaart")
def _(d):
    oefen(d, 8, 4)
    d.wacht("Vrij oefenen")
    d.zoek("Waar ligt de schat", OPNIEUW)
    d.foto("meetkunde-schatkaart", "Waar ligt de schat?")


@scenario("meetkunde-kruisje")
def _(d):
    oefen(d, 8, 4)
    d.wacht("Vrij oefenen")
    d.zoek("Zet een kruisje", OPNIEUW)
    d.toets("Left", "Left", "Up")
    d.foto("meetkunde-kruisje", "Een kruisje zetten met de pijltjes of een klik")


@scenario("meetkunde-assen")
def _(d):
    oefen(d, 8, 4, niveau=4)
    d.wacht("Vrij oefenen")
    d.zoek(r"het punt \(", OPNIEUW[:2] + ["4"])
    d.toets("Right", "Down", "Down")
    d.foto("meetkunde-assen", "Het assenstelsel (1ste middelbaar)")


@scenario("meetkunde-schaal")
def _(d):
    oefen(d, 8, 5, niveau=3)
    d.wacht("Vrij oefenen")
    antwoord(d, "1")
    d.foto("meetkunde-schaal", "Schaal")


@scenario("meetkunde-spiekbrief")
def _(d):
    wiskunde(d, 8, 1)
    d.toets("3")
    d.wacht("FORMULES|OPPERVLAKTE")
    d.foto("meetkunde-spiekbrief", "De spiekbrief van Meetkunde")


# ---- vraagstukken -----------------------------------------------------------------------------------------

def verhaal(d):
    """De tekst in het kader 'Het verhaal' als één regel."""
    regels = scherm_tekst(d).split("\n")
    binnen = [r for r in regels if r.strip().startswith("│")]
    return " ".join(r.strip().strip("│").strip() for r in binnen)


def getal(t):
    return float(t.replace(",", "."))


def bedrag(x):
    return f"{x:.2f}".replace(".", ",")


def wisselgeld_vraag(d):
    """Vrij oefenen op Normaal tot er een wisselgeld-vraagstuk zonder overbodig gegeven staat: (a, p, b)."""
    wiskunde(d, 9)
    d.wacht("Hoe wil je oefenen")
    d.toets("1")
    d.wacht("Hoe moeilijk")
    d.toets("2")
    for _ in range(300):
        time.sleep(0.15)
        t = verhaal(d)
        m = re.search(r"koopt (\d+) .* € ([\d,]+)\. \w+ betaalt met € (\d+)\. Hoeveel", t)
        if m and len(re.findall(r"\d+(?:,\d+)?", t)) == 3:
            return int(m.group(1)), getal(m.group(2)), int(m.group(3))
        d.toets(*OPNIEUW)
    raise RuntimeError("geen wisselgeld-vraagstuk gevonden")


@scenario("vraagstukken-stappen")
def _(d):
    a, p, b = wisselgeld_vraag(d)
    d.foto("vraagstukken-start", "Een vraagstuk in 4 stappen")
    d.toets("Space", "Right", "Space", "Right", "Space", "Down")
    for _ in range(3):
        if "◂ het wisselgeld ▸" in scherm_tekst(d):
            break
        d.toets("Right")
    d.toets("Space")
    d.foto("vraagstukken-lezen", "Stap 1: de gegevens aangeduid en gekozen wat er gevraagd wordt")
    d.toets("Tab", ("tekst", "x-"), "Enter")
    k = a * p
    d.toets(("tekst", f"{a} x {bedrag(p)} = {bedrag(k)}"), "Enter")
    d.toets(("tekst", f"{b} - {bedrag(k)} = {bedrag((b - k) * 10)}"), "Enter")
    d.foto("vraagstukken-klad", "Stap 2 en 3: het plan en het klad (elke regel wordt nagekeken)")
    d.toets("?", "?", "?")
    d.foto("vraagstukken-tips", "Drie keer ? : de sleutelwoorden licht op en de tip zegt welke bewerkingen")
    for _ in range(1 + len(f"{b} - {bedrag(k)} = {bedrag((b - k) * 10)}")):  # de foute regel terughalen en wissen
        d.toets("BSpace")
    d.toets(("tekst", f"{b} - {bedrag(k)} = {bedrag(b - k)}"), "Enter", "Enter")
    antwoord(d, bedrag(b - k))
    d.foto("vraagstukken-uitwerking", "Nagekeken: de uitgewerkte oplossing (Gegeven, Gevraagd, Oplossing, Antwoord)")


@scenario("vraagstukken-tweede-kans")
def _(d):
    a, p, b = wisselgeld_vraag(d)
    d.toets("a")
    antwoord(d, bedrag(a * p))
    d.foto("vraagstukken-tweede-kans", "Meteen geantwoord, maar het is een tussenuitkomst: een hulpje en klad maken")


@scenario("vraagstukken-spiekbrief")
def _(d):
    wiskunde(d, 9)
    d.wacht("Hoe wil je oefenen")
    d.toets("3")
    d.wacht("4 STAPPEN")
    d.foto("vraagstukken-spiekbrief", "De spiekbrief van Vraagstukken")


# ---- deel 2: de rest van het programma -------------------------------------------------------------------

def tafel_antwoord(d):
    m = re.search(r"(\d+) ([×:+−]) (\d+) =", scherm_tekst(d))
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    return str({"×": a * b, ":": a // b if b else 0, "+": a + b, "−": a - b}[op])


@scenario("snelrekenen")
def _(d):
    d.toets("3")
    d.wacht("Wat wil je snel rekenen")
    d.foto("snelrekenen-menu", "Snelrekenen: wat wil je snel rekenen?")
    d.toets("1")
    d.wacht("Hoe\\?")
    d.foto("snelrekenen-hoe", "60 seconden of 20 sommen")
    d.toets("2")
    d.wacht("Som 1 van 20")
    for i in range(20):
        if i == 6:
            d.foto("snelrekenen-bezig", "20 sommen: de klok loopt mee")
        antwoord(d, tafel_antwoord(d) if i != 4 else "1")
    time.sleep(0.5)
    d.foto("snelrekenen-klaar", "Het resultaat met je record")


@scenario("herhalen")
def _(d):
    d.toets("4")
    time.sleep(0.5)
    d.foto("herhalen-start", "Herhalen")


@scenario("avatar")
def _(d):
    d.toets("5")
    d.wacht("winkel")
    d.foto("avatar-hub", "Mijn avatar")
    d.toets("w")
    d.wacht("Wat wil je bekijken")
    d.foto("avatar-winkel", "De winkel")
    d.toets("6")
    time.sleep(0.4)
    d.foto("avatar-hoeden", "De hoeden in de winkel")
    d.toets("Down", "Enter")
    time.sleep(0.4)
    d.foto("avatar-kopen", "Bij elke aankoop een rekenvraag")
    m = re.search(r"Je hebt (\d+) punten. Dit kost (\d+) punten", scherm_tekst(d))
    antwoord(d, str(int(m.group(1)) - int(m.group(2))))
    time.sleep(0.4)
    d.foto("avatar-gekocht", "Gekocht!")


@scenario("avatar-kast")
def _(d):
    d.toets("5")
    d.wacht("winkel")
    d.toets("k")
    d.wacht("Kies wat je aantrekt")
    d.toets("Down", "Down", "Down", "Down", "Down", "Left")
    d.foto("avatar-kast", "De kast: kies wat je aantrekt")
    d.toets("c")
    time.sleep(0.4)
    d.foto("avatar-combinaties", "Combinaties")


@scenario("spiekbrieven")
def _(d):
    d.toets("6")
    d.wacht("Welke spiekbrief")
    d.foto("spiekbrieven", "Spiekbrieven")


@scenario("opties")
def _(d):
    d.toets("7")
    d.wacht("Kies een optie")
    d.foto("opties", "Opties")


@scenario("zeg-het-ons")
def _(d):
    d.toets("9")
    d.wacht("Wat wil je ons vertellen")
    d.toets(("tekst", "De schatkaart is leuk!"))
    d.foto("zeg-het-ons", "Zeg het ons")
    d.toets("Enter")
    d.foto("zeg-het-ons-bedankt", "Je opmerking is bewaard")


def ouderdeel(d):
    d.toets("Enter")
    d.wacht("Wie ben jij?")
    d.toets("3")
    d.wacht("Ouderwachtwoord")


@scenario("ouder-menu", kind=False)
def _(d):
    ouderdeel(d)
    d.foto("ouder-wachtwoord", "Het ouderwachtwoord")
    d.toets(("tekst", "ouder"), "Enter")
    d.wacht("Rapporten")
    d.foto("ouder-menu", "Het ouderdeel")


@scenario("ouder-rapport", kind=False)
def _(d):
    ouderdeel(d)
    d.toets(("tekst", "ouder"), "Enter")
    d.wacht("Rapporten")
    d.toets("1")
    d.wacht("Van welk kind")
    d.toets("1")
    d.wacht("Welke periode")
    d.foto("ouder-periode", "Welke periode?")
    d.toets("4")
    time.sleep(0.5)
    d.foto("ouder-rapport", "Een rapport")
    d.toets(*["Down"] * 12)
    d.foto("ouder-rapport-onderwerpen", "Het rapport per onderwerp")
    d.toets("k")
    time.sleep(0.4)
    d.foto("ouder-kalender", "De kalender")
    d.toets("Escape", "e")
    time.sleep(0.4)
    d.foto("ouder-export", "Een rapport exporteren")


@scenario("ouder-kinderen", kind=False)
def _(d):
    ouderdeel(d)
    d.toets(("tekst", "ouder"), "Enter")
    d.wacht("Rapporten")
    d.toets("2")
    d.wacht("Welk kind")
    d.toets("1")
    time.sleep(0.4)
    d.foto("ouder-kind", "De instellingen van een kind")


@scenario("ouder-punten", kind=False)
def _(d):
    ouderdeel(d)
    d.toets(("tekst", "ouder"), "Enter")
    d.wacht("Rapporten")
    d.toets("3")
    d.wacht("Van welk kind")
    d.toets("1")
    time.sleep(0.4)
    d.foto("ouder-punten", "Het puntenlogboek")


@scenario("ouder-opmerkingen", kind=False)
def _(d):
    ouderdeel(d)
    d.toets(("tekst", "ouder"), "Enter")
    d.wacht("Rapporten")
    d.toets("5")
    time.sleep(0.4)
    d.foto("ouder-opmerkingen", "Opmerkingen uit 'Zeg het ons'")


def thema_beeld(d, naam, titel):
    oefen(d, 5, 1)
    d.wacht("Vrij oefenen")
    d.zoek("Arceer", OPNIEUW)
    t = int(re.search(r"Arceer (\d+)/", scherm_tekst(d)).group(1))
    for _ in range(t + 1):
        d.toets("Space", "Right")
    d.toets("Enter")
    d.foto(naam, titel)


@scenario("start-standaard")
def _(d):
    thema_beeld(d, "start-standaard", "Het standaardthema")


@scenario("start-kleurenblind", argumenten=["--kleurenblind"])
def _(d):
    thema_beeld(d, "start-kleurenblind", "--kleurenblind")


@scenario("start-blauw-geel", argumenten=["--kleurenblind", "blauw-geel"])
def _(d):
    thema_beeld(d, "start-blauw-geel", "--kleurenblind blauw-geel")


@scenario("start-contrast", argumenten=["--contrast"])
def _(d):
    thema_beeld(d, "start-contrast", "--contrast")


@scenario("start-geen-kleur", argumenten=["--geen-kleur"])
def _(d):
    thema_beeld(d, "start-geen-kleur", "--geen-kleur")


@scenario("start-ascii", argumenten=["--ascii"])
def _(d):
    thema_beeld(d, "start-ascii", "--ascii")


@scenario("start-ouder", argumenten=["--ouder"], kind=False)
def _(d):
    d.toets("Enter")
    d.wacht("Ouderwachtwoord")
    d.foto("start-ouder", "--ouder: meteen naar het ouderdeel")
