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
  - Speciale tekens worden in ASCII-modus 1-op-1 vervangen (`terminal/tekens.py`); voeg nieuwe tekens daar toe.
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
  Eenheden heeft (nog) een eigen scherm vanwege de tabel.
  Een `Vraag` kan `invoer="janee"` (typ ja/nee) of `invoer="lijn"` (aanduiden op de getallenlijn, met zoom)
  hebben, en een visueel `model` uit `kern/modellen.py` (data) dat `terminal/modellen.py` tekent.
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
- Een echte terminaltest: tmux 80×24. Muisklikken sturen in tmux met X10-codes (`\e[M` + 3 bytes).

## Plan
Het volledige plan in 27 fasen staat in `docs/plan.md`.
