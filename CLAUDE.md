# Leeravontuur: afspraken voor wie aan deze code werkt

Gratis leerprogramma van **Solve It Now** ("Iedereen moet kunnen leren"), licentie CC BY-NC-SA 4.0.
Voor kinderen in Vlaanderen (nu een kind in het 5de leerjaar). Alle teksten in het programma zijn
Nederlands (Vlaams), met komma als decimaalteken.

## Architectuur (niet doorbreken)
- `leeravontuur/kern/` = alle logica: vragen maken, nakijken, diagnose, uitleg, leerlijnen, instellingen.
  **De kern importeert nooit curses** en weet niets van kleuren. Later moet er een GUI bovenop kunnen.
  Teksten die de kern teruggeeft hebben een *rol* ("accent", "dim", "goed" …), geen kleur.
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
- **Nieuwe onderwerpen** maak je als subklasse van `kern/onderwerp.Onderwerp` (maak_met, uitleg, tip, diagnose,
  onderwerp_van_sleutel, vast) + een leerlijn-JSON + import in `kern/catalogus.py`. Het scherm is dan
  automatisch `terminal/oefenaar.py` (vrij, reeks, rapport, fouten opnieuw, herhaalbak, punten, maatje).
  Eenheden heeft (nog) een eigen scherm vanwege de tabel. Die tabel is data (`TABELLEN` in `kern/wiskunde/eenheden.py`):
  een eenheid kan meer vakjes hebben (oppervlakte 2, volume 3) en aliassen (ha, l …) via `ALIASSEN`.
  Een `Vraag` kan `invoer="janee"` (typ ja/nee), `"lijn"` (aanduiden op de getallenlijn, met zoom),
  `"rooster"` (cijferen onder elkaar) of `"staart"` (staartdeling stap voor stap) hebben, en een visueel
  `model` uit `kern/modellen.py` (alleen data: Getallenlijn, Rooster, Staartdeling). De terminal tekent het:
  `terminal/modellen.py` (getallenlijn) en `terminal/rooster.py` (invoer-objecten voor rooster en staartdeling).
  Hulp per vakje komt uit `Onderwerp.kolom_hulp`, diagnose uit alle rijen uit `Onderwerp.diagnose_rijen`.
  Verder: `"duur"` (typ `2 u 15 min`) en `"klok"` (typ `11.15`), beide in `kern/wiskunde/grootheden.py`;
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
  `kern/klad.py`. Het onderwerp (voor herhaling) is de structuur, zodat herhalen een andere wereld geeft. Invoer
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

## Platformen
Windows, macOS en Linux. Alleen de standaardbibliotheek; op Windows `windows-curses` (requirements.txt).
Python 3.10+.

## Testen
- `python3 -m unittest discover -s tests` (of `python3 oefeningen.py --test`). Draait ook in CI op 3 systemen.
- Schermen testen zonder terminal met `terminal/nepscherm.py` (toetsen, ("klik", y, x), ("wiel", ±1)).
- Een echte terminaltest: tmux 80×24. Muisklikken sturen in tmux met SGR-codes:
  `tmux send-keys -t <sessie> -l $'\e[<0;X;YM'` (X en Y vanaf 1). X10-codes (`\e[M` + 3 bytes) worden als Esc gelezen.

## Werkwijze (uitbrengen)
- `main` = de versie die het kind gebruikt. Er wordt nooit rechtstreeks op `main` gewerkt.
- Elke fase of verbetering op een eigen branch vanaf `main` (bv. `fase-13-werkwoorden`), met een pull request
  naar `main`. Samenvoegen pas als de CI groen is én de vader akkoord geeft (merge-commit, geen squash).
- Elke versie: `VERSIE` in `leeravontuur/__init__.py`, een stukje in `CHANGELOG.md` (in gewone taal), README
  bijwerken, na het samenvoegen een tag `vX.Y.Z` en een GitHub-release met de tekst uit de changelog.
- De handleiding (`docs/handleiding/`) volgt mee: nieuwe onderwerpen, opties en startargumenten erin beschrijven,
  daarna `python3 docs/tools/handleiding.py` (tabellen per leerjaar, denkfouten, spiekbrieven, argumenten) en de
  schermafdrukken opnieuw maken met `python3 docs/tools/schermafdrukken.py [naam…]` (tmux nodig; de beelden staan
  in `docs/tools/scenarios.py`). `tests/test_handleiding.py` wordt rood als iets ontbreekt.
- Na een nieuwe versie doorloopt de vader `docs/testlijst.md`; opmerkingen van het kind staan in `feedback.txt`
  (ouderdeel → Opmerkingen).

## Plan
Het volledige plan in 27 fasen staat in `docs/plan.md`.
