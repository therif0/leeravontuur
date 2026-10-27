# Leeravontuur: afspraken voor wie aan deze code werkt

Gratis leerprogramma van **Solve It Now** ("Iedereen moet kunnen leren"), licentie CC BY-NC-SA 4.0.
Voor kinderen in Vlaanderen (nu een kind in het 5de leerjaar). Alle teksten in het programma zijn
Nederlands (Vlaams), met komma als decimaalteken.

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

- `leeravontuur/kern/` = alle logica: vragen maken, nakijken, diagnose, uitleg, leerlijnen, instellingen.
  **De kern importeert nooit curses** en weet niets van kleuren. Later moet er een GUI bovenop kunnen.
  Teksten die de kern teruggeeft hebben een *rol* ("accent", "dim", "goed" …), geen kleur.
- `leeravontuur/venster/` = vensters met tkinter, elk in een **eigen proces** (nu het klokvenster): `klokbeeld.py`
  maakt de klok als vormen (data; ook het SVG-beeld voor de handleiding), `klokvenster.py` tekent ze. De terminal
  start het via `terminal/venster.Klokvenster` en praat met JSON-regels; toetsen en klikken in het venster komen in
  `Scherm.toets` binnen alsof ze in de terminal gebeurden. Lukt het niet (geen tkinter of beeldscherm), dan tekent de
  terminal de klok. Het venster mag nooit in de weg zitten: bovenop zolang er een klok in beeld is, geen focus
  (Windows WS_EX_NOACTIVATE, X11 focusmodel active), plek via `klokvenster.kies_plek` (naast de terminal of
  rechtsboven, hoogstens een kwart breed; de Oefenaar houdt de tekst dan links van `LINKS`), versleepte plek bewaard
  (`klokvenster_plek` in de databank); F2 = de klok in de terminal. Tests gebruiken `NepKlokvenster`;
  `LEERAVONTUUR_KLOKVENSTER=0` zet het uit (schermafdrukken).
- `leeravontuur/terminal/` = alleen weergave en invoer (curses).
  - Kleuren uitsluitend via rollen uit `terminal/thema.py`. Geen `color_pair`/`COLOR_` elders
    (een test bewaakt dit). Juist/fout krijgt altijd ook een symbool (✔ ✘ !), want er is een
    kleurenblind-thema.
  - Elk klikbaar element registreert een klikzone (`scherm.zones.voeg`) met dezelfde actie als de toets.
    Muis en toetsenbord delen zo één codepad.
  - Speciale tekens worden in ASCII-modus 1-op-1 vervangen (`terminal/tekens.py`); voeg nieuwe tekens daar toe
    (een test controleert elk teken in de code en de inhoud; letters met een accent worden de gewone letter).
  - Alles moet passen in 80×24.
- Hiërarchie **Vak → Domein → Vaardigheid** (`kern/vaardigheden.py`). Elke vaardigheid heeft een
  **leerlijn** in `leeravontuur/inhoud/leerlijnen/<id>.json` met parameters per leerjaar.
- **Niveaus zijn relatief** tegenover het leerjaar van het kind: Makkelijk −1, Normaal 0, Moeilijk +1,
  Heel moeilijk +2 (`kern/leerjaren.py`). Een nieuw leerjaar = vooral leerlijn-data aanvullen.
- Exact rekenen met `Decimal`/`Fraction`, nooit met float.
- **Opslag:** alles wat bewaard wordt, gaat via `kern/opslag.py` (SQLite, bestand `leeravontuur.db` in de datamap).
  Schemawijzigingen = een nieuw script achteraan in `MIGRATIES` (nooit een oud script aanpassen).
  Antwoorden worden alleen toegevoegd, nooit aangepast (een trigger bewaakt dat). Elk record heeft een UUID.
  Elke oefening loopt via een `kern/sessie.py`-`Sessie` (`vraag_getoond()` → `antwoord(...)`), zodat tijd,
  vraagsleutel en diagnose altijd bewaard worden.
- **Stabiliteit** (een kind mag nooit een crash of verloren werk zien):
  - Lezen uit de databank via `Opslag._lees`/`_een` (geven bij een fout een standaardwaarde), schrijven via
    `_schrijf`. JSON uit de databank via `_json`. Reservekopieën in `reserve/` (per dag, vóór elke migratie);
    een beschadigd bestand wordt automatisch hersteld uit de nieuwste goede kopie.
  - `Onderwerp.maak` gebruikt `jaar_voor` (nooit parameters `None`); `maak_herhaling` mag nooit crashen.
    `onderwerp_van_sleutel` moet elke eigen sleutel aankunnen (let op ':' in de sleutel).
  - Toetsen: getypte tekens met een code van een curses-toets (257–511, bv. œ) komen als `("teken", ch)`.
    Gebruik `scherm.teken_van(k)` om een getypt teken te krijgen, nooit `chr(k)` op een toetscode.
  - Vangnet: een fout in een scherm → `App.oeps` (fouten.log via `kern/foutlog.py`, terug naar het hoofdmenu).
    `--debug` of `LEERAVONTUUR_DEBUG=1` zet het vangnet uit. Slotbestand tegen twee keer openen: `kern/slot.py`.
  - `tests/test_stabiliteit.py` (elke generator × elk leerjaar, herhaling over leerjaren, databank, vangnet en de
    aapjestest) moet groen blijven. Langer zoeken: `LEERAVONTUUR_AAP=3000 LEERAVONTUUR_AAP_SEEDS=40` en
    `LEERAVONTUUR_AAP_RONDES=15`.
- Instellingen staan per kind in de databank. Startargumenten (`--kleurenblind` …) gelden voor die sessie
  en worden niet bewaard (`App.voorrang`).
- Tijd altijd via `kern/klok.py` (tests zetten de klok vast).
- Avatar: pixel-art als data in `inhoud/avatar/onderdelen.json`, samengesteld door `kern/avatar.py` (raster van
  '#rrggbb'/None), getekend door `terminal/avatar.py` (▀-halfblokken; kleurparen via `thema.pixel`).
  Het oefenmaatje (`terminal/maatje.py`) gebruikt de pixel-avatar waar plaats is, anders een tekstgezichtje.
  Nieuwe onderdelen: test `test_avatar.py` controleert dat gezicht en ankers op het lijf staan.
- **De vaste werkwijze** (elke oefening dezelfde, zodat het kind niet verloren loopt): lees, klad (`Tab`), antwoord;
  `?` = getrapte tips (`Onderwerp.tips`), fout = één tweede kans (niet bij janee/vergelijk/keuze en objecten met een
  eigen stappenlogica: `GEEN_TWEEDE_KANS` in `terminal/oefenaar.py`), daarna "Zo kan het:" in klad-regels, met het
  eigen klad ernaast (`Kladblad.teken_kader`: ✔ ✘ en ! waar `analyseer` een denkfout ziet). Het klad
  is één onderdeel voor alles: `terminal/kladblad.py` (ook in het vraagstuk). **Elk nieuw rekenonderwerp** zet
  `klad = "ja"` (of `"verplicht"`, met `klad_klaar`) en geeft `oplossing(v)` in klad-regels (`kern/klad.stap`,
  `oplossing_van`, `fout_pad`); `tests/test_werkwijze.py` kijkt na dat elke regel klopt en op het antwoord eindigt.
  De terminal vraagt de oplossing altijd via `oplossing_of_niets` (een fout komt in het logboek, nooit bij het kind).
  Het klad-nakijken tegenover een oplossing is `kern/klad.analyseer` (ook voor vraagstukken).
- **Nieuwe onderwerpen** maak je als subklasse van `kern/onderwerp.Onderwerp` (maak_met, uitleg, tip, diagnose,
  onderwerp_van_sleutel, vast) + een leerlijn-JSON + import in `kern/catalogus.py` + een regel in het leerplan
  (`terminal/curriculum/<vak>.py`, zie "Menu's"). Het scherm is dan
  automatisch `terminal/oefenaar.py` (vrij, reeks, rapport, fouten opnieuw, herhaalbak, punten, maatje).
  Eenheden heeft (nog) een eigen scherm vanwege de tabel. Die tabel is data (`TABELLEN` in `kern/wiskunde/eenheden.py`):
  een eenheid kan meer vakjes hebben (oppervlakte 2, volume 3) en aliassen (ha, l …) via `ALIASSEN`.
  Een `Vraag` kan `invoer="janee"` (typ ja/nee), `"lijn"` (aanduiden op de getallenlijn, met zoom),
  `"rooster"` (cijferen onder elkaar) of `"staart"` (staartdeling stap voor stap) hebben, en een visueel
  `model` uit `kern/modellen.py` (alleen data: Getallenlijn, Rooster, Staartdeling). De terminal tekent het:
  `terminal/modellen.py` (getallenlijn) en `terminal/rooster.py` (invoer-objecten voor rooster en staartdeling).
  Hulp per vakje komt uit `Onderwerp.kolom_hulp`, diagnose uit alle rijen uit `Onderwerp.diagnose_rijen`.
  Verder: `"duur"` (typ `2 u 15 min`) en `"klok"` (typ `11.15`), beide in `kern/wiskunde/grootheden.py`; `"klok"`
  toont het getypte op een digitaal klokje (`terminal/digitaal.py`, wat erop staat komt uit `klok_cijfers`; compact
  naast een hoog model);
  de klok (`kern/wiskunde/klok.py`): model `Wijzerklok` (in het klokvenster, of pixels in
  `terminal/modellen.teken_klok`, in ASCII `#` = uur en `*` = minuten), `"wijzers"` (zet de wijzers: `KlokInvoer` in `terminal/balk.py`) en `"klokwoord"` (typ
  "vijf voor half vier": `klok.woorden`/`lees_woorden`); tijden zijn minuten na middernacht, een wijzerklok kijkt
  modulo 720 na;
  `"woord"` (een soort hoek typen) en `"coord"` (een kruisje op de schatkaart, `terminal/balk.py`); de meetkunde-modellen
  `Figuur` (cm²-rooster), `Kaart` (schatkaart of assenstelsel) en `Hoek`; `"breuk"` (typen: `lees_breuk` geeft een `GetypteBreuk` die de vorm bewaart), `"vergelijk"` (<, >, =),
  `"balk"` (arceren op de breukbalk) en `"veld"` (kleuren in het honderdveld), beide in `terminal/balk.py`. Nakijken gaat via `Onderwerp.nakijken` (standaard
  `==`; een breuk telt op zijn waarde, behalve als `data["vereenvoudigd"]` de eenvoudigste vorm eist).
  `Vraag.model_na` wordt pas na het nakijken getoond (uitleg die het antwoord verklapt). Modellen worden getekend
  via `terminal/modellen.teken_model`; is een model hoger dan 7 rijen, dan komt de feedback ernaast (een
  invoer-object vraagt dat met het attribuut `naast = (rij, kolom)`).
- **Vraagstukken** (`kern/wiskunde/vraagstukken.py`): een verhaalmachine = rekenstructuur (Python: getallen en
  stappen als `Rekenstap`) × wereld (`inhoud/vraagstukken/werelden.json`) × verwoording (`zinnen.json`, sjablonen
  van `kern/verhaal.py`). De foute paden (denkfouten) volgen automatisch uit de stappen; het klad leest
  `kern/klad.py`. Het onderwerp (voor herhaling) is de structuur, zodat herhalen een andere wereld geeft. `Verhaal.soort`
  (`getal`, `klok`, `duur`) zegt hoe het antwoord gelezen wordt; tijd rekent in minuten, en het klad kent
  tijdstippen (`9.45 u`, `9:45`). Invoer
  `"vraagstuk"` = `terminal/vraagstuk.py` (4 stappen). Haakjes in de Oefenaar voor zo'n invoer-object: `eigen_tekst`
  (tekent zelf de vraag), `eigen_tip` (`?` gaat naar het object), `extra` (bewaard bij het antwoord en gebruikt
  voor de punten) en `uitleg_na`. `tests/test_vraagstukken.py` maakt elke structuur in elk leerjaar en kijkt na
  dat het verhaal klopt, past (4 × 56 tekens) en mooi uitkomt. De Speurneus (invoer `"speur"`, model `Speur`)
  maakt van een fout pad (of een rekenfout) het klad van een ander kind; Schatten (invoer `"keuze"`, model
  `Keuze`) gebruikt de controle-regel van het vraagstuk. Beide bouwen op `VRAAGSTUKKEN.maak_met`.
- Punten: regels in `kern/punten.py`; een `Sessie` kent de punten per antwoord toe; elk punt staat in het logboek.
- Wachtwoorden en pincodes alleen via `kern/wachtwoord.py` (pbkdf2, formaat met methode en iteraties).
  Rapporten en export zitten in `kern/rapporten.py` (geeft regels met rollen terug); het ouderdeel in
  `terminal/schermen/ouder.py` zet `Scherm.slot` (vergrendelen na inactiviteit).

## Menu's (Vak › Domein › Onderwerp)
- Alle oefenmenu's komen uit één leerplan: `terminal/curriculum/` (`Vak` › `Domein` › `Onderwerp`, volgorde =
  volgorde in het menu; `wiskunde.py`, later `taal.py` en `frans.py`). Een `Onderwerp` heeft `modi` (reeks, vrij,
  60s, 20sommen, tabel: starters uit `curriculum/modi.py`), een `spiek` (`Spiekbrief`, of `None`) en `opslag`: de
  vaardigheid-ids waaronder de antwoorden bewaard worden. **Bewaarde ids nooit hernoemen** (een test bewaakt
  de lijst); de zeven maten delen `wiskunde.eenheden.omzetten` (`GROEPEN`: "Maten" in het rapport).
- Een nieuw vak = een bestand in `curriculum/` en een plaats in `VAKKEN`; het verschijnt dan vanzelf in het
  hoofdmenu, de Spiekbrieven, het rapport (per vak › domein) en de CSV (kolommen vak en domein). Elke vaardigheid
  uit de kern moet in het leerplan staan, anders wordt `tests/test_menu_architecture.py` rood.
- Navigatie in `terminal/navigatie.py`: hoofdmenu › vak › domein › onderwerp, met toetsen per onderwerp via
  `Scherm.menu(..., toetsen=...)`: **Enter** (of het cijfer, of een klik) = reeks, anders 60 s, anders 20 sommen;
  **V** vrij, **S** spiekbrief, **T** 60 s (alleen als de timer zichtbaar is), **Z** 20 sommen, **H** tabel-oefening;
  ook als kleine letter; een letter die niet geldt, doet niets. De voetregel toont alleen de toetsen van het
  gemarkeerde onderwerp en is klikbaar. Na een oefening of spiekbrief sta je terug op hetzelfde onderwerp.
- Hoogstens **10 items per menu** (cijfertoetsen 1–9 en 0; test). Het hoofdmenu heeft er nu 8: met Taal en Frans
  zit het vol, dus vóór er iets bijkomt (Examens, Avontuur) eerst met de vader een oplossing kiezen.
- Spiekbrieven met dezelfde titel binnen een domein worden één keer getoond, dus dezelfde titel = dezelfde
  spiekbrief (test).
- Instellingen: het kind kiest in Mijn avatar › **Schermkleuren** (L); de rest staat per kind bij de ouder
  (Ouders › Kinderen › kind › **Weergave**). Er is geen menu Opties meer.
- Over de indeling van de menu's beslist de vader: eerst een voorstel, dan bouwen.

## Platformen
Windows, macOS en Linux. Alleen de standaardbibliotheek; op Windows `windows-curses` (requirements.txt).
Python 3.10+.
Starten: `leeravontuur.py` (de Python-versie en curses nakijken, dan `leeravontuur/__main__.py`), met een
dubbelklik-bestand per systeem: `leeravontuur-win.bat`, `leeravontuur-mac.command`, `leeravontuur-linux.sh`
(`.gitattributes` bewaakt CRLF/LF). `oefeningen.py` is de oude naam en start `leeravontuur.py`.

## Testen
- `python3 -m unittest discover -s tests` (of `python3 leeravontuur.py --test`). Draait ook in CI op 3 systemen.
- Schermen testen zonder terminal met `terminal/nepscherm.py` (toetsen, ("klik", y, x), ("wiel", ±1)).
- Een echte terminaltest: tmux 80×24. Muisklikken sturen in tmux met SGR-codes:
  `tmux send-keys -t <sessie> -l $'\e[<0;X;YM'` (X en Y vanaf 1). X10-codes (`\e[M` + 3 bytes) worden als Esc gelezen.

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
Het volledige plan in 27 fasen staat in `docs/plan.md`.
