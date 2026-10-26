"""Vult de automatische stukken van de handleiding in (docs/handleiding/**/*.md).

Een automatisch stuk staat tussen twee markeringen; de tekst ertussen wordt telkens opnieuw gemaakt:
    <!-- auto:leerlijn wiskunde.breuken.herkennen -->   wat er per leerjaar aan bod komt (uit de leerlijn)
    <!-- auto:denkfouten wiskunde.breuken.herkennen --> de denkfouten die het programma herkent
    <!-- auto:spiekbrief wiskunde.breuken.herkennen --> de spiekbrief zoals in het programma
    <!-- auto:argumenten -->                            alle startargumenten
    <!-- /auto -->

Gebruik:
    python3 docs/tools/handleiding.py               bijwerken
    python3 docs/tools/handleiding.py --controleer  alleen controleren (geeft 1 als iets niet bijgewerkt is)
"""

import re
import sys
from pathlib import Path

WORTEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORTEL))
MAP = WORTEL / "docs" / "handleiding"

from leeravontuur.__main__ import maak_parser  # noqa: E402
from leeravontuur.kern import catalogus, leerjaren, leerlijnen  # noqa: E402,F401  (catalogus: alle onderwerpen laden)
from leeravontuur.kern.onderwerp import ONDERWERPEN  # noqa: E402
from leeravontuur.kern.wiskunde import eenheden as E  # noqa: E402
from leeravontuur.kern.wiskunde.getallen import NAAM as PLAATSNAAM  # noqa: E402

# ---- leesbare namen ----------------------------------------------------------------------------------------

PARAMETERS = {  # parameter → wat het betekent (vaardigheid.parameter gaat voor)
    "soorten": "soorten vragen",
    "tafels": "tafels",
    "max_factor": "tafel tot",
    "delen": "ook deeltafels",
    "veelvoud": "ook met tientallen (7 × 80)",
    "negatief": "ook negatieve getallen",
    "max": "getallen tot",
    "decimalen": "hoogstens cijfers na de komma",
    "machten": "× en : met",
    "max_cijfers": "hoogstens cijfers",
    "plaatsen": "afronden op",
    "delers": "deelbaar door",
    "cijfers": "hoogstens cijfers",
    "cijfers_a": "cijfers van het eerste getal",
    "cijfers_b": "cijfers van het tweede getal",
    "termen": "hoogstens getallen onder elkaar",
    "deler_cijfers": "cijfers van de deler",
    "rest": "ook met een rest",
    "noemers": "noemers",
    "noemer_max": "noemers tot",
    "factor_max": "vermenigvuldigen met hoogstens",
    "kgv": "gelijknamig maken met het kgv",
    "vereenvoudigd": "uitkomst vereenvoudigen",
    "stambreuk": "alleen stambreuken (1/n)",
    "vijfvouden": "alleen vijfvouden",
    "procenten": "procenten",
    "wiskunde.eenheden.omzetten.soorten": "soorten eenheden",
    "max_stap": "komma hoogstens zoveel eenheden verschuiven",
    "wiskunde.hoofdrekenen.splitsen.groot": "× met getallen tot",
    "deler_max": "delen door hoogstens",
    "deeltal_max": "delen: getallen tot",
    "compenseer": "compenseren met",
    "wiskunde.hoofdrekenen.splitsen.komma": "ook kommagetallen (2,4 × 6)",
    "wiskunde.eenheden.omzetten.cijfers": "cijfers in het getal (van–tot)",
    "dec_getal": "cijfers na de komma in de vraag",
    "dec_antw": "cijfers na de komma in het antwoord",
    "max_getal": "getal in de vraag kleiner dan",
    "max_antw": "antwoord kleiner dan",
    "stap": "minuten in stappen van",
    "omrekenen": "omrekenen tussen",
    "max_duur": "tijdsduur hoogstens (minuten)",
    "max_cent": "bedragen tot (cent)",
    "tijden": "tijden (minuten)",
    "vormen": "figuren",
    "rijen": "rijen",
    "kolommen": "kolommen",
    "wiskunde.meetkunde.rooster.rijen": "rooster: rijen",
    "wiskunde.meetkunde.rooster.kolommen": "rooster: kolommen",
    "wiskunde.meetkunde.coordinaten.kolommen": "schatkaart: kolommen",
    "wiskunde.meetkunde.coordinaten.rijen": "schatkaart: rijen",
    "assen": "assenstelsel van −n tot n",
    "wiskunde.meetkunde.formules.max": "afmetingen tot (cm)",
    "komma": "ook afmetingen met ,5",
    "hoeken": "soorten hoeken",
    "schalen": "schalen",
    "wiskunde.vraagstukken.oplossen.structuren": "soorten vraagstukken",
    "wiskunde.vraagstukken.oplossen.max": "getallen tot",
    "factor": "groepjes, stuks of keer: hoogstens",
    "geld": "prijzen in stappen van (€)",
    "gram": "gewichten in stappen van (g)",
    "wiskunde.vraagstukken.oplossen.procenten": "procent korting",
    "overbodig": "kans op een overbodig gegeven",
    "wiskunde.eenheden.klok.stap": "minuten (lezen) in stappen van",
    "wiskunde.eenheden.klok.max_duur": "later/vroeger: hoogstens (minuten)",
    "middernacht": "ook over middernacht",
    "fouten": "soorten klad",
    "wiskunde.vraagstukken.speurneus.structuren": "soorten vraagstukken",
    "wiskunde.vraagstukken.schatten.structuren": "soorten vraagstukken",
    "wiskunde.vraagstukken.speurneus.max": "getallen tot",
    "wiskunde.vraagstukken.schatten.max": "getallen tot",
    "wiskunde.vraagstukken.speurneus.procenten": "procent korting",
    "wiskunde.vraagstukken.schatten.procenten": "procent korting",
    "intro": "kans op een inleidende zin",
}

SOORTEN = {  # de interne namen van soorten vragen → leesbaar
    # hoofdrekenen, getallen
    "maal_splitsen": "× met splitsen (14 × 7)", "deel_splitsen": ": met splitsen (91 : 7)",
    "maal_compenseren": "× met compenseren (99 × 6)",
    "deelbaar": "deelbaar door …?", "delers": "alle delers", "ggd": "ggd", "kgv": "kgv", "priem": "priemgetal?",
    "aflezen": "aflezen", "aanduiden": "aanduiden", "sprong": "sprongen", "temperatuur": "thermometer",
    # breuken
    "arceren": "arceren", "aanvullen": "aanvullen (3/4 = ?/8)", "balk": "op de breukbalk",
    "vereenvoudigen": "vereenvoudigen", "gelijknamig": "gelijknamig", "ongelijknamig": "ongelijknamig",
    "gelijke_teller": "gelijke teller", "gemengd": "gemengde getallen", "negatief": "met negatieve uitkomst",
    "van": "breuk van een getal", "maal_nat": "breuk × getal", "deel_nat": "breuk : getal",
    "maal_breuk": "breuk × breuk", "deel_breuk": "breuk : breuk", "naar_breuk": "kommagetal → breuk",
    "naar_komma": "breuk → kommagetal",
    # procenten
    "kleuren": "kleuren", "kleuren_breuk": "breuk kleuren", "breuk_naar_procent": "breuk → %",
    "komma_naar_procent": "kommagetal → %", "procent_naar_breuk": "% → breuk", "procent_naar_komma": "% → kommagetal",
    "welk_procent": "hoeveel %?", "korting": "korting", "btw": "btw", "stijging": "stijging", "daling": "daling",
    # eenheden
    "massa": "massa", "lengte": "lengte", "inhoud": "inhoud", "oppervlakte": "oppervlakte", "volume": "volume",
    # tijd, geld, snelheid
    "omrekenen": "omrekenen (u, min, s …)", "gemengd_naar": "2 u 15 min = ? min", "naar_gemengd": "135 min = ? u ? min",
    "duur": "tijdsduur", "eindtijd": "aankomstuur", "euro_naar_cent": "euro → cent", "cent_naar_euro": "cent → euro",
    "wisselgeld": "wisselgeld", "samen": "samen betalen", "afstand": "afstand", "tijd": "tijd", "snelheid": "snelheid",
    "omzetten": "km/u ↔ m/s",
    # meetkunde
    "omtrek": "omtrek", "rechthoek": "rechthoek", "L": "L-vorm", "trap": "trap", "driehoek": "driehoek",
    "rechthoek_opp": "opp. rechthoek", "rechthoek_omtrek": "omtrek rechthoek", "vierkant_opp": "opp. vierkant",
    "vierkant_omtrek": "omtrek vierkant", "driehoek_opp": "opp. driehoek", "parallellogram_opp": "opp. parallellogram",
    "trapezium_opp": "opp. trapezium", "cirkel_omtrek": "omtrek cirkel", "cirkel_opp": "opp. cirkel",
    "balk_volume": "volume balk", "kubus_volume": "volume kubus", "tekening": "bij een tekening",
    "graden": "bij een aantal graden", "nevenhoek": "nevenhoeken", "assen_aflezen": "assenstelsel: aflezen",
    "assen_aanduiden": "assenstelsel: aanduiden", "naar_echt": "kaart → echt", "naar_kaart": "echt → kaart",
    "schaal_zoeken": "de schaal zoeken",
    # vraagstukken (structuur/variant)
    "samen/samen": "samen (+)", "samen/deel": "het ontbrekende deel (−)", "verschil/meer": "hoeveel meer? (−)",
    "verschil/erbij": "zoveel meer: hoeveel? (+)", "verschil/minder": "'minder dan' maar optellen (valkuil)",
    "groepen/totaal": "groepjes: hoeveel in totaal? (×)", "groepen/per": "eerlijk verdelen (:)",
    "groepen/aantal": "hoeveel groepjes? (:)", "rest/volle": "hoeveel volle? (: met rest)",
    "rest/over": "wat blijft er over? (de rest)", "rest/nodig": "hoeveel nodig? (naar boven afronden)",
    "samen_delen/gewoon": "samen en dan verdelen (+ :)", "wisselgeld/een": "wisselgeld (−)",
    "wisselgeld/meer": "wisselgeld bij meer stuks (× −)", "twee_soorten/gewoon": "twee soorten kopen (× × +)",
    "twee_soorten/wissel": "twee soorten en wisselgeld (4 stappen)", "per_kg/gewoon": "prijs per kg (omzetten, ×)",
    "per_kg/wissel": "prijs per kg en wisselgeld (3 stappen)", "korting/gewoon": "prijs met korting (% −)",
    "korting/alleen": "hoeveel korting? (%)", "sparen/gewoon": "sparen: hoeveel weken? (− : naar boven)",
    "recept/gewoon": "recept voor meer of minder personen (: ×)", "breuk_van/gewoon": "een breuk van een aantal (: ×)",
    "breuk_van/niet": "het andere deel (: × −)", "omtrek/gewoon": "omtrek: een hek rondom (+ ×)",
    "omtrek/prijs": "omtrek en prijs (+ × ×)",
    "gemiddelde/drie": "gemiddelde van 3 (+ :)", "gemiddelde/vier": "gemiddelde van 4 (+ :)",
    "snelheid/afstand": "snelheid: hoe ver? (×)", "snelheid/tijd": "snelheid: hoe lang? (:)",
    "snelheid/minuten": "snelheid met minuten (omzetten, ×)", "tegels/tegels": "tegels: oppervlakte (× ×)",
    "tegels/prijs": "tegels: prijs per m² (× ×)", "schaal/echt": "schaal: kaart → echt (×, omzetten)",
    "lint/stukken": "in stukken knippen (omzetten, :)", "lint/over": "wat blijft er over? (omzetten, rest)",
    "per_stuk/een": "de prijs van één (:)", "per_stuk/drie": "regel van drie (: ×)",
    "alles_juist": "alles juist", "rekenfout": "met een rekenfout", "denkfout": "met een denkfout",
    "ongeveer": "ongeveer hoeveel?", "kan": "kan dat kloppen?",
    "tijdsduur/duur": "tijdsduur: hoe lang? (−)", "tijdsduur/eind": "aankomstuur (+)",
    "tijdsduur/begin": "vertrekuur: terugtellen (−)", "tijdsduur/twee": "aankomstuur in 2 stukken (+ +)",
    # de klok
    "lezen": "de wijzerklok lezen", "woorden_naar": "woorden → cijfers", "naar_woorden": "cijfers → woorden",
    "zetten": "de wijzers zetten", "24uur": "24 uur", "later": "later", "vroeger": "vroeger",
    # waar dezelfde naam iets anders betekent (vaardigheid.soort gaat voor)
    "wiskunde.procenten.van.van": "procent van een getal",
    "wiskunde.meetkunde.hoeken.driehoek": "de derde hoek van een driehoek",
}
OMREKENEN = ["u ↔ min", "min ↔ s", "dag ↔ u", "week ↔ dagen", "jaar ↔ maanden"]  # kern/wiskunde/grootheden.OMREKENEN


def getal(x):
    """1000000 → '1 000 000', 0.1 → '0,1'."""
    if isinstance(x, float):
        return str(x).replace(".", ",")
    if isinstance(x, int) and abs(x) >= 10000:
        return f"{x:,}".replace(",", " ")
    tekst = str(x)
    return tekst.replace(".", ",") if re.fullmatch(r"-?\d+\.\d+", tekst) else tekst


def waarde(vaardigheid, naam, w):
    if w is None:
        return ""
    if isinstance(w, bool):
        return "ja" if w else "nee"
    if naam == "plaatsen":
        return ", ".join(PLAATSNAAM.get(k, str(k)) for k in w)
    if naam == "omrekenen":
        return ", ".join(OMREKENEN[:w])
    if naam == "cijfers" and vaardigheid == "wiskunde.eenheden.omzetten":
        return f"{w[0]}–{w[1]}"
    if naam == "machten":
        return ", ".join(getal(m) for m in w)
    if naam == "assen":
        return f"−{w} … {w}" if w else "nee (schatkaart)"
    if w in ([], 0) and naam in ("procenten", "gram", "noemers", "compenseer"):
        return "—"  # (komt in dat leerjaar niet voor)
    if naam in ("overbodig", "intro"):
        return f"{round(w * 100)} %"
    if naam == "schalen":
        return ", ".join(f"1 : {getal(s)}" for s in w)
    if isinstance(w, list):
        return ", ".join(SOORTEN.get(f"{vaardigheid}.{x}", SOORTEN.get(x, x)) if isinstance(x, str) else getal(x)
                         for x in w)
    return getal(w)


def leerlijn_tabel(vaardigheid):
    """Een tabel: per leerjaar een kolom, per parameter een rij. Bij een lijst staat na het eerste leerjaar
    alleen wat erbij komt ("+ …"), of "idem" als er niets verandert."""
    data = leerlijnen.laad(vaardigheid)
    jaren = [j for j in leerjaren.LEERJAREN if j in data["leerlijn"]]
    kop = ["", *(leerjaren.NAMEN[j] for j in jaren)]
    regels = ["| " + " | ".join(kop) + " |", "|" + "---|" * len(kop)]
    for naam in data["parameters"]:
        label = PARAMETERS.get(f"{vaardigheid}.{naam}", PARAMETERS.get(naam, naam))
        cellen, vorige = [], None
        for j in jaren:
            p = data["leerlijn"].get(j)
            w = None if p is None else p.get(naam)
            if p is None:
                cellen.append("—")
            elif w == vorige:
                cellen.append("idem")
            elif isinstance(w, list) and isinstance(vorige, list) and vorige and naam not in ("plaatsen", "cijfers") \
                    and set(vorige) < set(w):
                cellen.append("+ " + waarde(vaardigheid, naam, [x for x in w if x not in vorige]))
            else:
                cellen.append(waarde(vaardigheid, naam, w))
            vorige = w if p is not None else vorige
        regels.append(f"| **{label}** | " + " | ".join(cellen) + " |")
    niet = [leerjaren.NAMEN[j] for j in jaren if data["leerlijn"].get(j) is None]
    if niet:
        lijst = niet[0] if len(niet) == 1 else ", ".join(niet[:-1]) + " en " + niet[-1]
        regels += ["", f"— = komt nog niet aan bod in het {lijst}: dat niveau kun je dan niet kiezen "
                   "(er staat \"nog niet in dit leerjaar\")."]
    return regels


def denkfouten(vaardigheid):
    lijst = E.DENKFOUTEN if vaardigheid == E.OMZETTEN.id else ONDERWERPEN[vaardigheid].denkfouten
    if not lijst:
        return ["*(geen speciale denkfouten: het kind krijgt altijd het juiste antwoord met uitleg)*"]
    return [f"- {tekst}" for tekst in lijst.values()]


def spiekbrief(vaardigheid):
    regels = E.spiekbrief() if vaardigheid == E.OMZETTEN.id else ONDERWERPEN[vaardigheid].spiekbrief()
    if not regels:
        return ["*(geen aparte spiekbrief)*"]
    return ["```text", *(t.rstrip() for t, _ in regels), "```"]


def argumenten():
    regels = ["| Argument | Wat het doet |", "|---|---|"]
    for a in maak_parser()._actions:
        if not a.option_strings or a.dest == "help":
            continue
        naam = ", ".join(a.option_strings) + (" [" + " of ".join(a.choices) + "]" if a.choices else "")
        regels.append(f"| `{naam}` | {a.help} |")
    return regels


MAKERS = {"leerlijn": leerlijn_tabel, "denkfouten": denkfouten, "spiekbrief": spiekbrief,
          "argumenten": lambda _: argumenten()}
BLOK = re.compile(r"(<!-- auto:(\w+)\s*([\w.]*) -->\n)(.*?)(<!-- /auto -->)", re.S)


def vul_in(tekst):
    def maak(m):
        soort, arg = m.group(2), m.group(3)
        if soort not in MAKERS:
            raise ValueError(f"onbekend automatisch stuk: {soort}")
        return m.group(1) + "\n".join(MAKERS[soort](arg)) + "\n" + m.group(5)
    return BLOK.sub(maak, tekst)


def pagina_s():
    return sorted(MAP.rglob("*.md"))


def main(argv):
    controleer = "--controleer" in argv
    verouderd = []
    for pad in pagina_s():
        oud = pad.read_text(encoding="utf-8")
        nieuw = vul_in(oud)
        if nieuw != oud:
            verouderd.append(pad.relative_to(WORTEL))
            if not controleer:
                pad.write_text(nieuw, encoding="utf-8")
    for pad in verouderd:
        print(("niet bijgewerkt: " if controleer else "bijgewerkt: ") + str(pad))
    return 1 if controleer and verouderd else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
