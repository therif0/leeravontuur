# Leeravontuur: afspraken voor wie aan deze code werkt

Gratis leerprogramma van **Solve It Now** ("Iedereen moet kunnen leren"), licentie CC BY-NC-SA 4.0.
Voor kinderen in Vlaanderen (nu een kind in het 5de leerjaar). Alle teksten in het programma zijn
Nederlands (Vlaams), met komma als decimaalteken.
**Het doel:** twee doelen, even zwaar, om beurten: de zoon (wat hij dit jaar nodig heeft, en niets vergeten) en het
product (gratis voor alle Vlaamse kinderen). Richting: `docs/koers.md`.

## Architectuur (niet doorbreken)
**In één oogopslag** (elke laag kent alleen de lagen eronder):
```
terminal/curriculum/  leerplan: Vak › Domein › Onderwerp = de menu's (wijst naar kern-ids en schermen)
terminal/             weergave en invoer (curses): schermen, Oefenaar, navigatie, thema, tekens
venster/              tkinter-vensters, elk in een eigen proces (klokvenster)
kern/                 alle logica en opslag: onderwerpen, nakijken, diagnose, klad, punten, rapporten (geen curses)
inhoud/               data: leerlijnen per vaardigheid, vraagstukwerelden, avatar (JSON)
```
Gouden regels:
1. Logica in de kern, nooit in een scherm; de kern kent geen curses, kleuren of menu's.
2. Wat het kind ziet, komt uit data of de registry (leerlijnen, `curriculum/`), niet uit losse code per scherm.
3. Eén codepad: toets en klik doen hetzelfde; elke oefening gebruikt dezelfde werkwijze (lees, klad, antwoord).
4. Bewaarde gegevens zijn heilig: alleen via `kern/opslag.py`, antwoorden alleen toevoegen, ids nooit hernoemen,
   schema alleen via een nieuwe migratie.
5. Een kind ziet nooit een crash of verloren werk; elke nieuwe regel krijgt een test die haar bewaakt.

## Altijd (de details staan in `docs/architectuur.md`)
- De kern importeert nooit curses; teksten uit de kern hebben een *rol*, geen kleur. Kleuren alleen via de rollen van
  `terminal/thema.py`; juist/fout altijd ook met een symbool (✔ ✘ !).
- Elk klikbaar element krijgt een klikzone met dezelfde actie als de toets. Alles past in 80×24. Nieuwe speciale tekens
  in `terminal/tekens.py`. Een getypt teken via `scherm.teken_van(k)`, nooit `chr(k)`.
- Exact rekenen met `Decimal`/`Fraction`. Tijd via `kern/klok.py`. Opslag alleen via `kern/opslag.py`; elke oefening via
  een `Sessie`.
- Elke oefening: lees, klad (Tab), antwoord; F1 = tips (niet `?`), dan de spiekbrief; fout = één tweede kans. Een nieuw
  onderwerp = een `Onderwerp`-subklasse + leerlijn-JSON + `kern/catalogus.py` + een regel in `terminal/curriculum/`.

## Waar staat wat (`docs/architectuur.md`)
Lagen (kern, venster/klokvenster, terminal) · gegevens, opslag en stabiliteit · de vaste werkwijze (klad, tips,
tweede kans, spiekbrief, stoppen) · nieuwe onderwerpen en soorten invoer · vraagstukken · punten, wachtwoorden,
rapporten en het slot · Gemengd oefenen · Taal · Werkwoordspelling · Menu's. Taal heeft ook een eigen plan:
`docs/taal.md`. De kaart van de hele code (elk bestand, elke functie, wie wie aanroept):
`leeravontuur structuur/README.md`.

## Menu's
Alle menu's komen uit het leerplan `terminal/curriculum/` (`Vak` › `Domein` › `Onderwerp`). Bewaarde ids nooit
hernoemen; hoogstens 10 items per menu; over de indeling beslist de vader (eerst een voorstel, dan bouwen).

## Platformen
Windows, macOS en Linux. Alleen de standaardbibliotheek; op Windows `windows-curses` (requirements.txt).
Python 3.10+.
Starten: `leeravontuur.py` (de Python-versie en curses nakijken, dan `leeravontuur/__main__.py`), met een
dubbelklik-bestand per systeem: `leeravontuur-win.bat`, `leeravontuur-mac.command`, `leeravontuur-linux.sh`
(`.gitattributes` bewaakt CRLF/LF). `oefeningen.py` is de oude naam en start `leeravontuur.py`.

## Testen
- `python3 -m unittest discover -s tests` (of `python3 leeravontuur.py --test`). Draait ook in CI op 3 systemen.
- Schermen testen zonder terminal met `terminal/nepscherm.py` (toetsen, ("klik_op", actie), ("wiel", ±1)); een klik
  via de zone van een actie, niet via ("klik", y, x), zodat een test juist blijft als een vak verschuift.
- Een echte terminaltest: tmux 80×24. Muisklikken sturen in tmux met SGR-codes:
  `tmux send-keys -t <sessie> -l $'\e[<0;X;YM'` (X en Y vanaf 1), en daarna de loslaat-code `$'\e[<0;X;Ym'` (anders
  denkt ncurses dat de knop nog ingedrukt is en telt de volgende klik niet). Start het programma in tmux met
  `TERM=xterm-256color`, anders leest ncurses de code als Esc + tekens. X10-codes (`\e[M` + 3 bytes) worden als Esc
  gelezen.

## Werkwijze met Claude (zo werken we samen)
- **De vader beslist** over alles wat het kind of de ouder ziet: menu's, namen, volgorde, teksten, rapport, export.
  Claude doet een voorstel met een aanbeveling en bouwt pas na zijn akkoord. Noem hem "de vader", geen namen.
- **Een grote verandering** (een verbouwing, een nieuw vak): eerst een **inventaris** van wat er nu is (afvinkbaar,
  zodat niets vergeten wordt), dan een **plan in fasen**. Elke fase: eigen commit(s), tests groen, en dan **stoppen**:
  melden wat er veranderde, afwijkingen van het plan, de testoutput en wat de volgende fase doet. Pas verder na
  zijn akkoord.
- **Bewijs vóór "klaar":** de volledige suite (ook de lange aapjestest bij grote wijzigingen), schermen echt
  bekeken in tmux 80×24, en bij een verbouwing een vergelijking met de vorige versie op echte gegevens (een kopie).
  Wat niet nagekeken is, wordt niet "klaar" genoemd.
- **Grotere stukken** (de vader, 10/11/2026): hij kan een voorstel voor meer versies tegelijk goedkeuren. Dan bouwt
  Claude die versies na elkaar zonder een stop per fase: elke versie op een eigen branch (op de vorige gestapeld) met
  een pull request naar `main`, hetzelfde bewijs per versie, en een kort bericht per pull request. Claude neemt kleine
  keuzes die het voorstel niet noemt zelf en zet ze onder "Keuzes" in de pull request. Claude stopt toch en vraagt bij:
  een migratie van de databank, een verandering aan het hoofdmenu, iets dat tegen een eerdere keuze van de vader
  ingaat, of een test die niet netjes op te lossen is. Op het afgesproken stoppunt komt een volledig verslag.
- **Werkbestanden** (de vader, 12/11/2026): elke nieuwe functie of update wordt eerst uitgedacht in een md-bestand in
  `werk/` (vragen, keuzes, fasen; zie `werk/README.md`). Pas als de vader "actie" zegt, wordt er gebouwd. Plannen
  blijven kort: het werkbestand is het plan.
- **Zuinig met tokens** (de vader, 16/11/2026): korte plannen en verslagen, het planbestand bevat alleen de huidige
  taak, testoutput alleen de laatste regels. CLAUDE.md blijft kort; details komen in `docs/architectuur.md`.
- Een fout of iets vreemds gezien buiten de opdracht: melden en voorstellen, niet zelf de opdracht uitbreiden.
  Een kleine fout die het kind zou merken: melden, en na akkoord meteen in dezelfde branch.
- Testen door de vader gebeurt op een kopie van de gegevens (`LEERAVONTUUR_DATA`), met een testlijst.
- **Claude voegt nooit samen**, maakt geen tags of releases en verwijdert geen branches: dat doet de vader.
  De geschiedenis van `main` wordt nooit herschreven.
- Taal: in het programma en in de documenten van de repo Vlaams-Nederlands; Claude antwoordt de vader in het
  Engels (hij schrijft Nederlands of Engels).

## Werkwijze (uitbrengen)
- `main` = de versie die het kind gebruikt. Er wordt nooit rechtstreeks op `main` gewerkt.
- Elke fase of verbetering op een eigen branch vanaf `main` (bv. `fase-13-werkwoorden`), met een pull request
  naar `main`. Samenvoegen pas als de CI groen is én de vader akkoord geeft (merge-commit, geen squash).
- Elke versie: `VERSIE` in `leeravontuur/__init__.py`, een stukje in `CHANGELOG.md` (in gewone taal), README
  bijwerken, na het samenvoegen een tag `vX.Y.Z` en een GitHub-release met de tekst uit de changelog.
- De handleiding (`docs/handleiding/`) wordt niet meer per versie herschreven: dat gebeurt in één
  **handleidingproject** (een volledige test van alle functies + de handleiding voor kind, ouder en coach), als de
  vader het vraagt. Tot dan:
  - een nieuw onderwerp gaat in `NOG_TE_BESCHRIJVEN` in `tests/test_handleiding.py` (de to-do van dat project);
  - een nieuw startargument komt wel meteen in `startargumenten.md`;
  - de automatische stukken blijven bij: `python3 docs/tools/handleiding.py` (tabellen per leerjaar, denkfouten,
    spiekbrieven, argumenten); `tests/test_handleiding.py` wordt rood als iets ontbreekt.
  - De schermafdrukken (`python3 docs/tools/schermafdrukken.py [naam…]`, tmux nodig; de beelden staan in
    `docs/tools/scenarios.py`) tonen nog de menu's van 0.19 en worden in het handleidingproject opnieuw gemaakt.
- Na een nieuwe versie doorloopt de vader `docs/testlijst.md`; opmerkingen van het kind staan in `feedback.txt`
  (ouderdeel → Opmerkingen).

## Plan
Taal heeft een eigen plan: `docs/taal.md` (de keuzes van de vader, de domeinen, de kleuren per zinsdeel en woordsoort).
De richting en de volgorde staan op één pagina: `docs/koers.md` (het doel, de vaste datum 1 september 2027, de
periodes en de regel voor nieuwe ideeën: een fout die het kind merkt = meteen, past in de periode = in de rij, al de
rest = geparkeerd in `docs/todo.md`). De details en alle fasen staan in `docs/plan.md`.
