# Plan: "Leeravontuur": rekenen en taal leren en oefenen in de terminal (Windows, macOS, Linux)

## Context

### Waar het begon
Het eerste programma (`oefeningen.py`, ±900 regels, één bestand, curses) oefende lengte en massa. Imrane
(**5de leerjaar**, Vlaanderen) vond het superleuk. De vader wilde er een volwaardig leerprogramma van maken:
- rekenen in de volle breedte, met een echt leerproces per onderwerp, hoofdrekenen en snelrekenen
- vraagstukken met een kladblad en grondige uitleg waarom iets juist of fout is
- kindaccounts, herhaling van fouten, en geen vragen die hij na een tijd van buiten kent
- een ouderdeel achter een wachtwoord, met rapporten op datum en examens die de ouder samenstelt
- **taal** (Nederlands) in dezelfde stijl, en **Frans** (woordenschat, vervoegen, korte zinnetjes, uit het hoofd leren)
- dictees die **afgedrukt** worden en die de ouder voorleest (geen computerstem)
- een **avatar** (blokje à la Geometry Dash) die hij met verdiende punten aankleedt in een **winkel**, waar elke
  aankoop een kleine rekenchallenge is; de avatar is ook zijn oefenmaatje
- beveiliging die nu eenvoudig is, maar later kan meegroeien

Alles in de terminal, licht, op Windows, macOS en alle Linuxen, met een requirements-lijst.
Later moeten er een GUI en andere vakken (aardrijkskunde, geschiedenis) bij kunnen.
Het doel: dieper en slimmer dan de typische oefenwebsites (bv. Computermeester), die er mooi uitzien maar beperkt zijn.

Niveaus zijn **relatief tegenover het leerjaar van het kind** (zie sectie M):
**Makkelijk** = leerjaar − 1 · **Normaal** = eigen leerjaar · **Moeilijk** = + 1 · **Heel moeilijk** = + 2.
Nu (5de leerjaar) betekent dat: 4de lj · 5de lj · 6de lj · 1ste middelbaar. In de tabellen hieronder staat de inhoud per
**leerjaar**, zodat ze volgend jaar gewoon één kolom opschuift.

Op het startscherm: **"Leeravontuur, een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren."**

### Stand van zaken (versie 0.20.1, oktober 2026)
Van één bestand naar ±16 000 regels Python in 22 versies (zie `CHANGELOG.md`), telkens getest. Wat er nu werkt:
- **Wiskunde: 8 domeinen, 43 onderwerpen** (Getallen, Hoofdrekenen, Cijferen, Breuken en procenten, Meten,
  Tijd, geld en snelheid, Meetkunde, Vraagstukken), elk met een leerlijn per leerjaar (3de leerjaar tot 1ste middelbaar),
  denkfouten die het programma herkent, uitleg en een spiekbrief.
- **De vaste werkwijze** in elke oefening: lees, klad (`Tab`, elke regel meteen nagekeken), antwoord; getrapte tips
  met `?`, een tweede kans, en "Zo kan het:" in klad-regels.
- **Interactieve modellen:** eenhedentabel, getallenlijn met zoom, cijferen in een rooster, staartdeling stap voor
  stap, breukbalk, honderdveld, cm²-rooster, schatkaart, en een **wijzerklok in een eigen venster**.
- **Vraagstukken** met een verhaalmachine (20 rekenstructuren × 22 werelden), 4 stappen, foute paden als denkfouten,
  de **Speurneus** (zoek de fout in het klad van een ander kind) en **schatten en controleren**.
- **Snelrekenen** (60 seconden, 20 sommen, records) in Hoofdrekenen.
- **Herhalen:** fouten opnieuw, gelijkaardige vragen, een herhaalbak (1, 3, 7 dagen), "niet binnen 30 dagen",
  en ▶ Verder.
- **Punten, pixel-avatar en winkel** (aankoop = rekenvraag, "ben je zeker?", mini-lesje, pakje onderweg, kast).
- **Ouderdeel:** kinderen beheren (leerjaar, timer, pincode, weergave), rapporten per periode en per vak › domein ›
  onderwerp met kalender, denkfouten en status, export naar CSV, TXT en JSON, puntenlogboek, opmerkingen van het
  kind ("Zeg het ons").
- **Toegankelijk:** schermkleuren (ook kleurenblind en hoog contrast), eenvoudige tekens (ASCII), muis overal,
  alles in 80 × 24.
- **Stevig:** 371 automatische tests (CI op Windows, macOS en Linux), een aapjestest met duizenden willekeurige
  toetsen, reservekopieën van de databank en een vangnet dat een fout nooit aan het kind toont.
- **Handleiding** (`docs/handleiding/`, met schermafdrukken; nog van de menu's van 0.19, zie "Wat er nu komt").
- **Een plan voor coaches en leerkrachten** (`docs/leerkracht-coach.md`, geparkeerd).

Hoe we werken staat in `CLAUDE.md` ("Werkwijze met Claude"): de vader beslist over wat het kind ziet, grote
veranderingen gaan in fasen met een stop na elke fase, en elke fout die hij vindt wordt een GitHub-issue met een
eigen branch en pull request.

### Wat er nu komt (voorstel; de vader beslist)
1. **De issues uit de tests van de vader** (lopend). Taal wacht tot hij klaar is met testen.
2. **Taal 1: werkwoordspelling** (fase 13), als stap B in fasen: B0 inventaris en beslissingen, B1 tekstantwoorden
   nakijken, B2 werkwoord-regelmotor en een nagekeken woordenlijst, B3 de eerste onderwerpen (Taal staat dan in het
   hoofdmenu), B4 't kofschip, B5 de werkwoordmachine en de foutenjager, B6 uitbrengen.
3. De rest van **Taal** (spelling, zinsontleding, woordenschat en lezen, dictee), dan **Frans**.
   Vóór Frans: beslissen hoe het hoofdmenu verder groeit (het zit dan vol, zie sectie L).
4. **Examens** (fase 23), en de eerste stappen voor de **coach** (C1–C4 kunnen al eerder).
5. **Leerjaar 2de middelbaar en de schooljaarwissel** (fase 26), klaar vóór september 2027.
6. Het **handleidingproject**: een volledige test van alle functies en de handleiding voor kind, ouder en coach.
7. **Avontuur** en **publicatie**.

---

## Eerlijke inschatting (ook wat minder goed is)
- **De omvang is groot.** Het werd ruim 15× het eerste programma, gebouwd in 20+ kleine versies waarbij
  **na elke versie iets bruikbaars werkt**: eerst het fundament (accounts, opslag, rapport, geschiedenis), dan
  onderwerp per onderwerp. Dat blijft zo voor Taal en Frans. Wat Imrane op school nodig heeft, kan voorgaan.
- **De terminal is een sterkte én een grens.** Rekenen, spelling, grammatica en woordenschat werken er uitstekend
  (snel, geen afleiding, toetsenbord). Zonder afbeeldingen en geluid zijn sommige dingen wel beperkt:
  - **Geen computerstem.** Robotstemmen zijn niet leuk voor een kind. **Dictees worden afgedrukt** en de ouder leest
    ze voor, net zoals de leerkracht in de klas.
  - **Luisteren en spreken** (belangrijk bij Frans) gebeuren dus met de ouder: het programma toont wat er voorgelezen
    of opgezegd moet worden, en de ouder duidt aan hoe het ging.
  - Kaarten voor aardrijkskunde (later) worden eenvoudige ASCII-kaarten of gewoon vraag-antwoord.
- **De kwaliteit van de taalinhoud** (woordenlijsten, zinnen, regels) moet echt correct Vlaams-Nederlands zijn.
  Ik werk daarom met **regelmotoren + handmatig gecontroleerde lijsten**, met tests die de regels nakijken
  (bv. elke werkwoordsvorm in de lijst tegen de spellingregel). Toch raad ik aan dat jij de lijsten één keer doorkijkt.
  Ze staan in eenvoudige JSON-bestanden.
- **Het ouderwachtwoord** is een slot tegen nieuwsgierige kinderen, geen echte beveiliging:
  wie het databasebestand verwijdert of aanpast, omzeilt het. Dat staat zo in de README.
- **De nieuwe Vlaamse minimumdoelen** worden ingevoerd in 2026–2027. De leerinhoud hieronder volgt de gangbare
  leerplannen en de eindtermen van de 1ste graad. Ze staat als **data** in het programma, zodat ze makkelijk aan
  te passen is aan de methode van zijn school.

---

## Technische keuzes
- **Python 3.10+, alleen standaardbibliotheek:**
  - `curses` voor het scherm
  - `sqlite3` voor de opslag
  - `decimal`/`fractions` om exact te rekenen
  - `hashlib` (pbkdf2) voor het wachtwoord
  - `json` voor de inhoud
  - `webbrowser` + HTML om af te drukken (dictees, toetsjes, rapporten): de browser opent het blad en drukt af,
    op elk systeem

  Op Windows komt er één pakket bij: `requirements.txt` bevat `windows-curses>=2.4; sys_platform == "win32"`
  (2.4.2 heeft wheels voor Python 3.13 en 3.14). Op Linux en macOS installeert dat niets.
- **Een package in plaats van één bestand.** Dat is beter te onderhouden en te testen.
  `oefeningen.py` blijft de starter (`python3 oefeningen.py [--ouder] [--ascii]`). Die controleert de Python-versie
  en curses, en geeft anders een duidelijke Nederlandstalige melding.
- **GUI later mogelijk** (vastgelegd in `CLAUDE.md` in de repo, zodat elke volgende sessie het weet):
  - `kern/` importeert **nooit** curses. Daar zitten de vragen, de controle, de diagnose, de uitleg, de sessies,
    de opslag en de rapporten.
  - Visuele modellen (breukbalk, getallenlijn, rooster, honderdveld, zinsontleding) zijn **data**.
    `terminal/` tekent ze in tekst. Een latere GUI (bv. tkinter of web) tekent dezelfde data.
- **Hiërarchie die nieuwe vakken toelaat:** **Vak → Domein → Vaardigheid**.
  Bijvoorbeeld *Wiskunde → Breuken → Vereenvoudigen* of *Taal → Werkwoordspelling → Verleden tijd zwakke ww*.
  Elke vaardigheid heeft een id, een niveau (leerjaar), een leerplanomschrijving, een generator, een diagnose en een uitleg.
- **Opslag:** één SQLite-bestand op de juiste plek per systeem
  (`%APPDATA%\Leeravontuur`, `~/Library/Application Support/Leeravontuur`, `~/.local/share/leeravontuur`).
- **Platformdetails:**
  - Invoer als Unicode (`get_wch`), zodat é, è, ç en ë werken (Frans en Nederlands).
  - **Muis** (zoals in btop): curses ondersteunt klikken en het scrollwiel (`mousemask`, `KEY_MOUSE`) op Linux, op macOS
    (Terminal en iTerm2) en op Windows (Windows Terminal, via windows-curses). Zie L "Muis".
  - Op Windows: `resize_term` bij `KEY_RESIZE`.
  - Een ASCII-terugval (`--ascii`, of automatisch zonder UTF-8).
  - Een `NepScherm` voor schermtests zonder terminal.
  - CI op Windows, macOS en Linux.

### Databank (tabellen)
| Tabel | Inhoud |
|---|---|
| `kinderen` | naam, optionele pincode, aangemaakt |
| `instellingen` | per kind: standaardniveau, timer zichtbaar, open vakken/domeinen, avatar aan/uit |
| `ouder` | wachtwoord-hash + salt |
| `sessies` | kind, modus (leren/oefenen/reeks/snel/examen/herhaling/avontuur), start, einde |
| `antwoorden` | sessie, tijdstip, vaardigheid, niveau, **vraagsleutel**, vraagtekst, gegeven antwoord, juist, **diagnosecode**, tijd in ms, hulp/tip gebruikt, kladregels (JSON) |
| `beheersing` | per kind × vaardigheid: status (nieuw/ontdekt/geoefend/beheerst), laatst gezien, laatst getoetst, juist-% van de laatste 20 |
| `herhaalbak` | kind, vraagsleutel + parameters, bak 1–5, volgende datum |
| `examens` | samenstelling (vaardigheden, niveau, aantal, tijdslimiet, score tonen), toegewezen kind, status, resultaat |
| `badges`, `sterren` | avontuur |
| `punten_log` | kind, tijdstip, +/− punten, reden (juist antwoord, bonus, aankoop, ouderbonus) |
| `bezit` | kind, item, gekocht op, **geleverd** (ja / na N juiste antwoorden / na tijd), challenge juist? |
| `avatar` | kind, gekozen onderdelen per laag, opgeslagen outfits |
| `schema` | schemaversie voor migraties (alle records hebben een UUID + tijdstempels) |
| `eigen_inhoud` | woordpakketten en lijsten die de ouder zelf toevoegt (bv. de dicteewoorden van de week) |

---

## A. Randomisatie, geschiedenis en "niet van buiten leren"
**Ja, alles wordt willekeurig gemaakt, en wat aangeboden en getoetst werd, wordt bijgehouden.**
1. **Vragen zijn sjablonen met parameters, geen vaste lijst.** Bij rekenen zijn de getallen, eenheden, namen,
   voorwerpen en contexten willekeurig. Bij taal komt een werkwoord, onderwerp, tijd en zinssjabloon uit een woordenschat
   van honderden woorden. Het aantal combinaties is per vaardigheid duizenden tot miljoenen.
2. **Elke vraag krijgt een vraagsleutel** (sjabloon + parameters), die met datum in `antwoorden` komt.
   De generator weigert sleutels die het kind in de laatste **30 dagen** al zag. Bij kleine lijsten (bv. sterke
   werkwoorden) kiest hij eerst het item dat het langst niet gezien werd.
3. **Vraagstukken variëren ook in de structuur**, niet alleen in de getallen:
   - **Omgekeerde vragen** bij hetzelfde verhaal: de ene keer is de totaalprijs gevraagd, de andere keer de prijs per kg
     of het aantal.
   - Een andere **volgorde van de gegevens** in de tekst.
   - **Overbodige gegevens** die af en toe opduiken.
   - Meerdere verwoordingen per sjabloon ("hoeveel betaalt…", "wat kost…", "hoeveel geld heeft ze nodig…").
   - Zo leert hij **lezen en redeneren** in plaats van een patroon herkennen.
4. **Slimme keuze van wat er komt (adaptief):**
   - Vaardigheden krijgen een gewicht volgens zwakte (laag juist-%), hoe lang geleden ze gezien zijn
     en of er herhaalbak-vragen klaarstaan.
   - Een vaardigheid die beheerst is, komt nog af en toe terug (onderhoud).
5. **Examens gebruiken altijd verse vragen**, met een vraagsleutel die nooit eerder getoond werd. Zo meet een examen echt
   begrip en geen geheugen.
6. **In het ouderrapport** staat een overzicht per vaardigheid: *aangeboden op …*, *getoetst op …*,
   *status: beheerst / bezig / nog niet gezien*. Je ziet dus precies wat al aan bod kwam.
7. **Herhaalbak (Leitner):** een foute vraag komt in bak 1. Elke keer juist schuift hij een bak op
   (1 dag → 3 → 7 → 14 dagen), bij een fout gaat hij terug naar bak 1. Dit is **bewust** herhalen van dezelfde
   vaardigheid, maar met **nieuwe parameters** waar mogelijk, zodat hij de regel leert en niet het antwoord.

## B. Juist of fout? Altijd met motivering (diagnose)
Elke vaardigheid heeft naast een generator ook een **diagnose**. Die vergelijkt het foute antwoord met **typische
denkfouten** en geeft een gerichte uitleg in plaats van alleen "fout":
- **Eenheden:**
  - Komma de verkeerde kant op verschoven ("je deed ×1000 in plaats van :1000").
  - Een factor 10 te weinig of te veel ("je telde de kolommen verkeerd").
  - Bij oppervlakte maar 1 vakje per kolom gebruikt.
- **Breuken:**
  - Tellers en noemers samen opgeteld (1/2 + 1/3 = 2/5).
  - Niet volledig vereenvoudigd ("4/6 is juist, maar kan nog eenvoudiger: deel teller en noemer door 2").
- **Cijferen:**
  - Onthouden vergeten.
  - Kleinste van grootste afgetrokken per kolom.
  - Komma niet uitgelijnd.
- **Taal:**
  - d/t-fout ("de stam van *worden* is *word*; bij *hij* komt er een t bij → *wordt*").
  - Verkeerde regel 't kofschip.
  - Meervoud met f/v of s/z vergeten.

**Bij vraagstukken** is de feedback het meest uitgebreid. Elk sjabloon beschrijft de **oplossing als stappen**
(bewerking + getallen + *waarom* deze bewerking), en daarnaast een lijst **bekende foute paden**:
1. Het antwoord wordt vergeleken met:
   - de juiste uitkomst
   - elke tussenuitkomst ("je stopte na stap 2: dat is de prijs van 1 zak, maar er waren er 4")
   - elk fout pad ("je vergat 750 g om te zetten naar kg: 750 × 3,20 = 2400")
   - het gebruik van een overbodig gegeven ("de 12 kinderen in de klas heb je niet nodig")
   - de eenheid ("getal juist, eenheid fout: het moest € zijn")
   - een afrondingsfout
2. Het **kladblad wordt nagekeken per regel**. De feedback zegt **waar het eerst misliep** ("regel 2: 0,75 × 3,20 is 2,40,
   niet 24 → de komma"), ook als het eindantwoord toevallig juist is.
3. **Ook bij een juist antwoord** volgt een korte motivering ("Juist! Je zette eerst gram om naar kg, en vermenigvuldigde dan
   met de prijs per kg."). Is het antwoord juist maar is het klad onvolledig of fout, dan zegt het programma dat ook
   ("juist antwoord, maar laat je tussenstappen zien").
4. Daarna kan hij de **volledige uitgewerkte oplossing** openen, met het schema Gegeven/Gevraagd/Oplossing/Antwoord ingevuld.
5. In de **examenmodus** worden diagnoses alleen bewaard en niet getoond. De ouder ziet ze in het rapport
   ("3× eenheden vergeten om te zetten").

---

## C. Leerproces per domein (vier stappen)
**Ontdekken** (uitleg + interactief model, nieuw leren) → **Oefenen met hulp** (tips, directe feedback met diagnose) →
**Oefenen alleen** (feedback na de reeks) → **Toets/examen** (geen hulp).
Per vaardigheid houdt het programma bij hoe ver hij staat. Het menu stelt de volgende stap voor ("Breuken
vereenvoudigen: je bent klaar om te oefenen zonder hulp").

### Rekenen: interactieve modellen
- **Breukbalk:**
  - Een blok met vaste breedte. **De noemer bepaalt in hoeveel stukken het blok verdeeld wordt** (↑/↓ = noemer).
  - Met ←/→ + spatie **arceert** hij stukken (`███░░░`), en de breuk ernaast past zich live aan.
  - **Vereenvoudigen:** met `v` worden 2 (of 3 …) stukken samengevoegd. 4/8 → 2/4 → 1/2 blijft hetzelfde gearceerde deel.
  - Twee balken onder elkaar om **gelijkwaardigheid en vergelijken** te tonen.
  - **Gelijknamig maken** door beide balken fijner te verdelen.
  - Een **breuk van een getal**: 12 bolletjes verdeeld in 3 groepen.
- **Getallenlijn:**
  - Een lijn met streepjes. Met ←/→ beweegt de pijl, met `+`/`-` **zoomt** hij (eenheden → tienden → honderdsten).
  - **Negatieve getallen** links van 0, met een **thermometer**-variant.
  - Rekenen als **sprongen** (−3 + 5).
  - Oefeningen:
    - "Zet 0,35 op de lijn."
    - "Welk getal staat bij de pijl?"
    - "Rond af: naar welk streepje ligt het dichtst?"
- **Honderdveld** (10×10) voor procenten en honderdsten, plus een procentstrook naast een prijs.
- **Cijferen in het rooster:**
  - De typrichting staat standaard ← en er is een **onthouden-rij**.
  - "Met hulp": de kolom waar hij moet rekenen licht op, met een uitleg per stap.
  - **Staartdeling** stap voor stap (deel, vermenigvuldig, trek af, haal neer).
- **Eenhedentabel** zoals nu. Oppervlakte heeft 2 vakjes per kolom (×100), inhoud in dm³ 3 vakjes (×1000),
  en er is een tijdtabel (u/min/s).
- **Meetkunde:**
  - Figuren in tekst met afmetingen en een cm²-rooster om te tellen.
  - Hoeken (scherp/recht/stomp/gestrekt).
  - **Coördinaten-schatzoeken** op een tekstkaart.
  - Schaal (kaart 1:1000).
- **Hoofdrekenen** met strategieën die stap voor stap getoond worden:
  - **Compenseren:** 99 + 47 = 100 + 47 − 1.
  - **Splitsen.**
  - **Verdubbelen/halveren.**
  - × en : met 10/100/1000 als een komma die verschuift.

### Vraagstukken met kladblad
Het scherm volgt het Vlaamse schema **Gegeven · Gevraagd · Oplossing · Antwoord**:
- **Gegeven:** hij haalt de gegevens uit de tekst als `naam = getal eenheid` (`prijs per kg = 3,20 €`).
  - In de oefenmodus volgt per gegeven een check: nodig / niet nodig / ontbreekt nog.
  - Gegevens die hij **niet** overnam terwijl ze nodig zijn, worden aan het einde benoemd.
- **Gevraagd:** wat er gezocht wordt (kiezen uit opties bij Makkelijk/Normaal, zelf schrijven bij Moeilijk) + de eenheid.
- **Oplossing (klad):** vrije rekenregels (`750 g = 0,75 kg`, `0,75 × 3,20 = 2,40`).
  - Een kleine parser leest getallen met komma, eenheden, `+ − × : =` (ook `x`, `*`, `/`), breuken en procenten.
  - Elke regel krijgt ✔ of ✘ in oefenen met hulp.
- **Antwoord:** getal + eenheid, eventueel een antwoordzin. Daarna een **schatting-check** ("klopt dit ongeveer?").
- Aantal stappen: Makkelijk 1 · Normaal 2 · Moeilijk 3 · Heel moeilijk 3–4 met afleiders.
- **Sjablonen** per thema: winkel (prijs per kg, korting, wisselgeld), recept (verhoudingen, breuken),
  reizen (afstand, tijd, snelheid, dienstregeling), bouwen (omtrek, oppervlakte, tegels), sparen (procenten),
  sport (gemiddelde, tijden).
  - Doel bij de start: **±40 sjablonen** met elk 3–5 verwoordingen en omgekeerde varianten.

---

## D. Taal (Nederlands): in dezelfde stijl, volgens het leerplan
Dezelfde aanpak: vaardigheden met een generator en een diagnose, vier leerstappen, herhaalbak, rapporten en examens.
De inhoud zit in JSON-bestanden: werkwoorden (infinitief, stam, vt, vd, sterk/zwak), zelfstandige naamwoorden (de/het,
meervoud, verkleinwoord), bijvoeglijke naamwoorden en zinssjablonen. Een **regelmotor** maakt de vormen,
en tests controleren ze tegen gecontroleerde lijsten.

### Domeinen en ideeën
1. **Werkwoordspelling: de "werkwoordmachine"** (interactief, stap voor stap).
   - Het denkschema op het scherm:
     **1) welke tijd? → 2) zoek de persoonsvorm → 3) zoek de stam (ik-vorm) → 4) regel toepassen → 5) controleer**.
     Elke stap licht op en hij beantwoordt ze één voor één (in de stap "met hulp").
   - Tegenwoordige tijd: stam + t (*hij wordt*, *word jij?*, *jij wordt*).
   - Verleden tijd zwak: **'t kofschip** (de laatste letter van de stam in "'t kofschip"? → -te/-ten, anders -de/-den).
     Er is een kofschip-tekening in ASCII waarin de letter oplicht.
   - Voltooid deelwoord: ge- + stam + t/d; het bijvoeglijk gebruikte voltooid deelwoord (6de lj).
   - Sterke en onregelmatige werkwoorden (lijst + herhaalbak).
   - **Oefenvormen:** de gatenzin (`Gisteren ___ (fietsen) ik naar school.`), kiezen tussen d/t/dt,
     een **foutenjager** (zoek de fout in de zin) en een tijd omzetten (zet de zin in de verleden tijd).
2. **Spelling (niet-werkwoorden):**
   - meervoud (-s/-en, f→v, s→z, *'s* bij *auto's*)
   - verkleinwoorden (-je/-tje/-pje/-etje/-kje)
   - open en gesloten lettergreep (*bomen*/*bommen*: klinker verdubbelen of medeklinker verdubbelen)
   - ei/ij, au/ou, g/ch (met een woordenlijst)
   - tussen-s en tussen-(e)n bij samenstellingen
   - trema, koppelteken, apostrof
   - hoofdletters en leestekens
3. **Taalbeschouwing: de "zinsontleder"** (interactief).
   - De zin staat als woordblokjes op het scherm. Met ←/→ kiest hij een woord of een groep (shift+pijl maakt een groep),
     en met een toets geeft hij een kleur of label:
     - `p` = persoonsvorm
     - `o` = onderwerp
     - `g` = gezegde (werkwoordelijk gezegde)
     - `l` = lijdend voorwerp
     - `m` = meewerkend voorwerp
     - `b` = bijwoordelijke bepaling
   - **Woordsoorten** werken op dezelfde manier (zn, lidwoord, bn, ww, vnw, telwoord, voorzetsel).
   - Feedback per blokje (groen/rood) met een motivering ("*de hond* is het onderwerp: wie of wat + persoonsvorm?").
   - Proefjes als hulp: de **vraagproef** (zet de zin om in een vraag → de persoonsvorm komt vooraan),
     de **tijdproef** en de **getalproef**.
4. **Woordenschat:**
   - synoniemen, tegenstellingen
   - **spreekwoorden en uitdrukkingen** (de betekenis kiezen of de uitdrukking aanvullen)
   - de betekenis uit de context, voorvoegsels/achtervoegsels
   - trappen van vergelijking
5. **Begrijpend lezen:**
   - Korte teksten met vragen (feit, woordbetekenis, hoofdgedachte, verwijswoorden: "waar verwijst *hij* naar?").
   - De teksten schrijf ik vooraf, en de **ouder kan eigen teksten toevoegen**. Hier zit minder randomisatie in;
     de vraagvolgorde en de meerkeuzeopties worden wel geschud.
6. **Dictee, afgedrukt en voorgelezen door de ouder** (voor Nederlands én Frans):
   - Het programma stelt een dictee samen: uit het **woordpakket van de week** dat de ouder invoerde, uit de
     vaardigheden die hij nog moeilijk vindt, of uit de herhaalbak. Het **opent een afdrukbaar blad in de browser**:
     - een **ouderblad** met de woorden en zinnen om voor te lezen, plus waar je op let (bv. "d/t in *wordt*")
     - een **kindblad** met genummerde lijnen
   - **Achteraf (optioneel)** typt het kind of de ouder over wat er geschreven werd. Het programma vergelijkt dat
     **letter per letter**, geeft de diagnose ("d/t-fout", "verkleinwoord") en zet de fouten in de herhaalbak.
     Zo telt het dictee mee in het rapport.
   - Een **flitsdictee** voor alleen oefenen blijft mogelijk: het woord verschijnt 2 seconden en verdwijnt, daarna typt hij het.
     Dat is geen voorlezen, wel een goede oefening om woordbeelden te onthouden.

### Taal per niveau
| Domein | Makkelijk (4de) | Normaal (5de) | Moeilijk (6de) | Heel moeilijk (1ste mid.) |
|---|---|---|---|---|
| Werkwoordspelling | tt (stam + t), ik/jij/hij | + vt zwak ('t kofschip), vd | + bijvoeglijk vd, sterke ww, alle tijden | + gebiedende wijs, twijfelgevallen (*verhuisd/verhuist*) |
| Spelling | meervoud, verkleinwoord, hoofdletters | open/gesloten lettergreep, ei/ij, au/ou, f/v s/z | tussen-s/-(e)n, trema, koppelteken, apostrof | leenwoorden, samengestelde woorden |
| Zinsontleding | persoonsvorm, onderwerp | + gezegde, woordsoorten | + lijdend en meewerkend voorwerp | + bijwoordelijke bepaling, naamwoordelijk gezegde, bijzinnen |
| Woordenschat | tegenstellingen, synoniemen | uitdrukkingen, betekenis uit context | spreekwoorden, voor- en achtervoegsels | figuurlijk taalgebruik |
| Lezen | korte tekst, feitvragen | + hoofdgedachte, verwijswoorden | + mening/feit, tekstsoort | langere teksten, conclusies |

## D2. Frans: zelfde aanpak als rekenen en taal
Frans is een gewoon vak in hetzelfde systeem: vaardigheden met generator en diagnose, de vier leerstappen,
herhaalbak, "niet van buiten leren", rapporten, examens, punten en avatar. Niets apart.
In Vlaanderen begint Frans in het **5de leerjaar**. De einddoelen moeten **op het einde van het 6de** bereikt zijn,
op elke school (ook de steinerschool). Bij Frans liggen de niveaus daarom anders dan bij rekenen en taal:
**Makkelijk** = begin 5de · **Normaal** = einde 5de · **Moeilijk** = 6de (einddoelen lager) ·
**Heel moeilijk** = 1ste middelbaar. De leerinhoud is als bij alle vakken data en aan te passen.

Er zijn ingebouwde woordenschatpakketten per thema. Net als bij Nederlands kan de ouder via **eigen inhoud**
(zie G) woordenlijsten toevoegen.

### Wat erin komt
1. **Woordenschat Frans ↔ Nederlands** (met herhaalbak):
   - In beide richtingen. Zelfstandige naamwoorden altijd **met lidwoord**, met een kleur voor *le* (blauw) en *la* (rood),
     zodat het geslacht mee onthouden wordt. *l'* en *les* krijgen een eigen kleur.
   - Oefenvormen: intypen, meerkeuze (makkelijk), memory-paren, **woordslang** (letters in de juiste volgorde),
     en een "vul aan"-zin.
   - **Bijna juist:** een accent of lidwoord vergeten wordt niet zomaar fout gerekend, maar
     "bijna! let op het accent: *frère*" (in oefenen half juist, in een examen volgens de instelling van de ouder).
2. **Vervoegen: de vervoegingstabel** (dezelfde rooster-widget als de eenhedentabel):
   - Rijen *je / tu / il, elle, on / nous / vous / ils, elles*. Hij vult de vormen in met Tab.
     Daarna kleurt het rooster groen of rood, met een diagnose ("bij *nous* hoort de uitgang *-ons*").
   - De **werkwoordmachine** zoals bij Nederlands: stam zoeken → uitgang kiezen. Bij onregelmatige werkwoorden
     is het gewoon van buiten leren met de herhaalbak.
   - **Je → j'** voor een klinker (*j'ai*, *j'habite*) wordt apart geoefend.
3. **Korte zinnetjes:**
   - **Zinnen bouwen** met woordblokjes in de juiste volgorde (*Je / m'appelle / Imrane*).
   - Korte zinnen **vertalen** (NL → FR en FR → NL), met flexibele controle (meerdere juiste antwoorden mogelijk).
   - Een **gatenzin**: het juiste werkwoord of woord invullen.
   - **Vragen en antwoorden** (*Comment tu t'appelles ? → Je m'appelle …*), een eerste stap naar gesprekjes.
4. **Uit het hoofd leren** (tekstjes, versjes, een verhaal); dezelfde vaardigheid bestaat bij Nederlands:
   - De ouder plakt het tekstje in het programma. Dat laat **steeds meer woorden weg** (eerst elk 5de woord, dan meer,
     tot alleen de eerste letters overblijven). Hij vult de gaten in of zegt het op.
   - Een **luistermodus voor de ouder**: het programma toont de tekst groot. Het kind zegt het op en de ouder duidt per zin
     aan *goed / bijna / nog oefenen*. Dat komt in het rapport.
5. **Dictee Frans:** hetzelfde afdrukbare ouder- en kindblad als bij Nederlands (zie D.6).

### Accenten typen
Op een Belgisch AZERTY-toetsenbord kun je `é è à ç ù` rechtstreeks typen. Het programma leest daarom invoer
**als Unicode** (`get_wch` in plaats van `getch`, nodig op alle systemen). Voor andere toetsenborden komen er
**snelcodes**: `e'` → é, `` e` `` → è, `e^` → ê, `c,` → ç, `e"` → ë. Onderaan het scherm staat een hulpje.

### Ingebouwde basispakketten (de ouder kan ze aanvullen of verbergen)
- *Se présenter*: je m'appelle, j'ai … ans, j'habite à, mon anniversaire, ma famille, j'aime / je n'aime pas
- getallen 0–20 → 0–100, kleuren, dagen en maanden, de klas en de schoolspullen, het lichaam, eten en drinken, dieren
- begroetingen en beleefdheid

### Werkwoorden en tijden per niveau
| Makkelijk (begin 5de) | Normaal (einde 5de) | Moeilijk (6de) | Heel moeilijk (1ste mid.) |
|---|---|---|---|
| *être*, *avoir* (présent) | + werkwoorden op -er (présent), *s'appeler*, *aller* | + *faire*, *prendre*, *vouloir*, *pouvoir*; ontkenning *ne … pas*; vragen | + *passé composé* (met *avoir*/*être*), *futur proche*, werkwoorden op -ir/-re |

**Eerlijk:** luisteren en spreken zijn bij Frans belangrijke einddoelen. Een terminal zonder geluid kan die niet zelf
oefenen. Dat gebeurt dus met de ouder (luistermodus), en natuurlijk in de klas.

---

## E. Hoofdrekenen, snelrekenen en timer
- **Elke vraag wordt altijd getimed** en bewaard.
- **Timer zichtbaar of verborgen** is een instelling per kind (de ouder kiest). Verborgen = alleen in het ouderrapport.
- **Snelrekenen:** 60 seconden zoveel mogelijk, of 20 sommen om het snelst. Per type een **persoonlijk record**,
  en een grafiekje over de dagen in het rapport.
- Dit kan ook voor taal: **snel-spellen** met de tijd en d/t-flitsrondes.
- *Gebouwd (0.8, sinds 0.20 in Hoofdrekenen): Tafels en Optellen en aftrekken met T (60 s) en Z (20 sommen),
  Gemengd, records en een overzicht van de laatste rondes. Nog niet: het grafiekje in het rapport.*

## F. Herhaling na een reeks
- Na **elke** reeks, en ook bij het stoppen in vrij oefenen: "**Fouten opnieuw**" (dezelfde vragen, direct).
- Daarna: "**Gelijkaardige vragen**" (dezelfde vaardigheid, nieuwe parameters) om te controleren of de regel nu zit.
- Fouten gaan ook automatisch in de herhaalbak voor volgende dagen (zie A.7).
  Het hoofdmenu toont "Herhalen (7)".

## G. Accounts, ouderdeel, rapporten en examens
*Gebouwd (0.3 → 0.20): kindaccounts met pincode, het ouderdeel, kinderen beheren, rapporten met kalender, status
en denkfouten, export. Nog niet: examens, eigen inhoud, het trendgrafiekje en open vakken per kind.*

- **Kindaccounts:** bij de start kiest hij zijn naam (met een optionele kind-pincode). Elk kind heeft eigen vooruitgang,
  sterren, herhaalbak en instellingen.
- **Ouderdeel:** via `python3 oefeningen.py --ouder` of "Ouders" bij "Wie ben jij?" + wachtwoord.
  Bij de eerste keer stel je een wachtwoord in. Na 10 minuten zonder toets wordt het ouderdeel automatisch afgesloten.
  - **Kinderen beheren.** Instellingen per kind: niveau, timer zichtbaar, open vakken/domeinen, avatar.
  - **Rapporten per dag, week of maand, of een zelf gekozen periode:**
    - een samenvatting (oefentijd, aantal vragen, % juist)
    - een **kalender** met de oefendagen
    - per vak/domein/vaardigheid: % juist, gemiddelde tijd, de trend als tekstgrafiekje
    - **status per vaardigheid** (nooit gezien / aangeboden / geoefend / beheerst, met data)
    - de **meest voorkomende denkfouten** (uit de diagnosecodes)
    - examenresultaten
    - records bij snelrekenen
    - export naar **CSV en TXT** (in de map Documenten)
  - **Examen samenstellen:**
    - vakken, domeinen en vaardigheden aanvinken
    - niveau en aantal vragen (of een verdeling, bv. 5 breuken + 5 vraagstukken)
    - optioneel een tijdslimiet en "score tonen aan kind"
    - een examen kan **opgeslagen en hergebruikt** worden, met telkens verse vragen
  - **Eigen inhoud:** woordpakketten (dictee), eigen leesteksten en later begrippenlijsten voor andere vakken.
- **Examen voor het kind:** in het menu verschijnt "Examen klaar → Start".
  **Geen hulp, geen tips, geen diagnose, geen kladcontrole.** Een timer is zichtbaar als er een limiet is.
  Na afloop ziet hij alleen de score (als dat toegelaten is). Alle details gaan naar het ouderrapport.

## H. Avontuur (licht, in tekst)
- Een tekstkaart met werelden die **rekenen en taal mengen**:
  - **Markt:** geld, massa, korting; prijskaartjes met spelfouten verbeteren.
  - **Keuken:** inhoud, breuken, tijd; een recept lezen.
  - **Bouwwerf:** omtrek, oppervlakte, schaal.
  - **Bibliotheek:** werkwoordspelling, zinsontleding, uitdrukkingen.
  - **Schatteneiland:** coördinaten, hoeken, raadsels.
  - **Ruimtereis:** grote getallen, negatieve temperaturen, snelheid.
  - **Parijs:** Frans (bestellen op een terras, de weg vragen) gemengd met geld en tijd.
- Elke opdracht levert 1–3 ★ op. Sterren openen nieuwe werelden. Op het einde van een wereld wacht een gemengde "eindbaas".
- **Badges:** "Kommakoning", "Breukenbaas", "'t Kofschip-kapitein", "Zinsontleder", "Snelle rekenaar", "Herhaalheld".
- Alles blijft licht: korte teksten, een beetje ASCII-kunst, kleuren. Geen zware graphics.

## I. Punten, avatar en winkel (ludiek, maar met rekenen erin)

### Punten: verdienen en uitgeven
- **Sterren** = vooruitgang (werelden openen). **Puntjes** = munten om uit te geven. Die twee blijven gescheiden,
  zodat iets kopen geen vooruitgang kost.
- **Verdienen:**
  - per juist antwoord, met een factor per niveau (Heel moeilijk = meer)
  - een bonus voor reeksen (5 juist op rij), voor een lege herhaalbak, een examen, een record en een eerste keer "beheerst"
- **Tegen "punten farmen":** een te makkelijk niveau (onder zijn eigen niveau) levert minder op.
  "Fouten opnieuw" geeft maar een halve beloning. Een vraag die je al juist had, geeft niets extra.
- De **ouder** kan in het ouderdeel bonuspunten geven ("goed rapport!") of de factoren aanpassen.
- Alles staat in een **puntenlogboek** (waarom, wanneer), ook zichtbaar in het ouderrapport.

### De avatar: een blokje à la Geometry Dash
**Over het tekenen:** ik teken de avatar **niet** met losse ASCII-tekens (dat was inderdaad lelijk bij oudere AI's),
maar als **pixel-art**:
- Elke avatar is een raster van **16×16 pixels**. Elke terminalcel toont 2 pixels boven elkaar met het teken `▀`
  (voorgrondkleur = bovenste pixel, achtergrondkleur = onderste pixel). Zo krijg je een scherp, kleurrijk blokje
  van 16 tekens breed en 8 regels hoog.
- **Lagen** worden over elkaar gelegd: **vorm** (vierkant, rond, ovaal, trapezium, ruit, ster) → **kleur/patroon** →
  **oren** → **ogen** → **neus** → **mond** → **haar** → **hoed/accessoire** (bril, koptelefoon, kroon, pet).
- Elk onderdeel is een klein pixelpatroon in een JSON-bestand (letters = kleuren uit een palet), met ankerpunten
  (waar de ogen, mond en hoed komen per vorm). Ik ontwerp elk onderdeel met de hand op het raster.
  Een test controleert dat elke combinatie binnen het raster blijft en dat niets overlapt waar dat niet mag.
- **Uitdrukkingen**: blij, denken, verrast, aanmoedigend, trots, oeps. Dat zijn varianten van ogen en mond,
  zodat de avatar reageert op wat er gebeurt.
- **Mini-versie** (8×8 pixels = 8 tekens × 4 regels) voor op het oefenscherm.
- **Terugval:**
  - met 256 kleuren: het volledige palet
  - met 8 kleuren: een benadering
  - zonder kleur of UTF-8: een eenvoudig tekstgezichtje `[o_o]`
- Standaard: een **vierkant met ogen, neus, mond en oren**, zoals je beschreef.

### De avatar als oefenmaatje
- Op het oefenscherm staat de mini-avatar in een hoek. Is het venster breed genoeg (≥ 100 tekens),
  dan staat hij in een zijpaneel. Bij 80 tekens staat hij klein naast de feedbackregel, zodat hij de tabel nooit in de weg zit.
- Hij **reageert**:
  - blij bij juist, aanmoedigend bij fout, trots bij een reeks
  - een **tipje** gekoppeld aan de diagnose ("Psst… kijk eens naar de komma!")
  - een **lesje** na herhaalde dezelfde fout
- Hij geeft **geen hulp in het examen**. Daar kijkt hij alleen "geconcentreerd".
- Uitschakelbaar per kind (instelling).

### De winkel
- Een catalogus met items per categorie: vormen, kleuren, ogen, monden, haar, hoeden, accessoires, achtergronden.
  Prijzen lopen van 20 tot 500 punten, en zeldzame items komen pas vrij met een badge of wereld
  ("Kroon: alleen voor wie Breukenbaas is").
- **Kopen kan alleen met genoeg punten.** Anders zegt het programma vriendelijk hoeveel er nog ontbreken (met een rekensommetje).
- **Bij elke aankoop volgt een kleine rekenchallenge**, aangepast aan zijn niveau:
  - *Je hebt 200 punten en de hoed kost 70. Hoeveel punten heb je over?*
  - Op hogere niveaus: een korting ("vandaag 20 % korting"), twee items samen, of "hoeveel moet je nog sparen voor …".
- **Juist** → de avatar juicht, er volgt een korte motivering ("200 − 70 = 130, goed gerekend!") en het item zit meteen
  in zijn kast.
- **Fout** → eerst een speels **"Ben je zeker? 🤔"** met nog één kans.
  - Nog eens fout → een **mini-lesje** (de aftrekking op de getallenlijn of onder elkaar), daarna een ludieke penaliteit.
    Het item krijgt hij toch, want hij heeft de punten.
  - Mijn voorstel voor de penaliteit: **"De koerier is verdwaald 📦: je pakje komt na 10 juiste antwoorden"**,
    in plaats van 15 minuten wachten op de klok. Wachten op de klok nodigt uit om niets te doen; zo moet hij oefenen
    om het pakje te krijgen. Een balkje toont "pakje onderweg: 6/10".
  - Alternatieven die de ouder kan kiezen: X minuten oefentijd, of 5 punten "verzendkosten".
- Een **kast/paskamer**: items passen, combinaties bewaren, de avatar bekijken in groot formaat.

## J. Beveiliging: nu eenvoudig, later uit te breiden
**Het is niet vast: ik ontwerp het zo dat het later kan groeien.**
- **Nu (lokaal, één gezin):**
  - Het ouderwachtwoord wordt opgeslagen als **pbkdf2-sha256-hash met salt** (600 000 iteraties).
    Het algoritme en de parameters worden mee bewaard (bv. `pbkdf2$600000$salt$hash`), zodat een sterkere methode
    later kan zonder dat iemand opnieuw moet beginnen.
  - Het ouderdeel sluit automatisch af na inactiviteit.
  - De beperking blijft: wie aan het bestand kan, kan het omzeilen. Wil je dat echt afschermen, dan geef je het kind
    een **eigen gebruikersaccount op de computer**. Het besturingssysteem beschermt dan de map van de ouder.
    Dat staat in de README.
- **Voorbereid voor later (als het tractie krijgt):**
  - Alle opslag gaat via één laag (`kern/opslag.py`, een interface). Die kan later vervangen worden door:
    1. een **versleutelde databank** (bv. SQLCipher of het `cryptography`-pakket), of
    2. een **server met accounts**: ouders en kinderen loggen in, met tokens, HTTPS, rapporten via een website,
       en synchronisatie tussen toestellen.
  - Daarom krijgt elk record nu al een **UUID**, tijdstempels, en een **schemaversie met migraties**.
    Antwoorden worden enkel toegevoegd en nooit aangepast. Dat maakt synchroniseren later eenvoudig.
  - **Privacy/AVG (GDPR):** bij een servervariant gaat het om gegevens van kinderen. Dat vraagt om toestemming van de
    ouders, zo weinig mogelijk gegevens (geen achternaam of school nodig), hosting in de EU, een privacyverklaring
    en het recht om alles te wissen of te exporteren. In de lokale versie verlaat niets de computer.
    De **export en "alles wissen per kind"** bouw ik nu al in.

## K. Later (de architectuur houdt er nu al rekening mee)
- **Andere vakken** (aardrijkskunde, geschiedenis, WO): een algemene **kennismotor** die werkt met kennispakketten in JSON:
  - begrippen ↔ uitleg, vraag ↔ antwoord
  - sorteren en **tijdlijn** (geschiedenis)
  - ASCII-kaartjes en meerkeuze
- **"Activeren"** door de ouder: in het ouderdeel vink je aan welke lessen in de klas gezien werden. Die worden oefenbaar.
  Daarnaast biedt de **leermodus** nieuwe stof aan.
- **GUI** bovenop dezelfde `kern/`.

---

## L. Architectuur, menu's en instellingen

### Lagen
```
 ┌────────────────────────────────────────────────────────────────────┐
 │  terminal/curriculum/  het leerplan: Vak › Domein › Onderwerp      │  ← de menu's (registry), wijst naar
 │                        (modi, spiekbrieven, bewaarde ids)          │    kern-ids en schermen
 ├────────────────────────────────────────────────────────────────────┤
 │  terminal/  (curses)                 later: gui/ (tkinter of web)  │  ← alleen tekenen + toetsen
 │  navigatie · oefenaar · kladblad · rooster · balk · vraagstuk ·    │
 │  modellen · avatar · maatje · schermen/ (ouder, winkel, …)         │
 │  venster/   klokvenster in een eigen proces (tkinter)              │
 └───────────────▲──────────────────────────────────▲─────────────────┘
                 │ vraagt: "geef volgende vraag",    │ krijgt: Vraag, Model, Feedback,
                 │ "controleer dit antwoord"         │ Rapport (gewone Python-objecten)
 ┌───────────────┴──────────────────────────────────┴─────────────────┐
 │  kern/                                                             │
 │  sessie ── selectie ── onderwerpen (catalogus) ──► wiskunde/       │
 │     │          │            │        later: taal/ frans/           │
 │     │          │            └── leerlijnen (generator, nakijken,   │
 │     │          │                 diagnose, uitleg, klad-oplossing) │
 │     │          └── herhaling (herhaalbak)                          │
 │     └── punten · avatar · winkel · rapporten · klad · verhaal      │
 └───────────────────────────────▲────────────────────────────────────┘
                                 │ één opslag-interface (kern/opslag.py)
 ┌───────────────────────────────┴────────────────────────────────────┐
 │  opslag: SQLite met migraties en reservekopieën · later: server    │
 └────────────────────────────────────────────────────────────────────┘
 inhoud/ (JSON): leerlijnen, vraagstukwerelden en zinnen, avatar-onderdelen en winkel
```
**De vaste lus voor elke oefening (in elk vak hetzelfde):**
1. `sessie` vraagt aan `selectie` welke vraag nu komt (adaptief, herhaalbak, niet binnen 30 dagen).
2. Het onderwerp maakt een `Vraag` met de parameters uit de **leerlijn** van het juiste leerjaar.
3. De terminal toont de vraag en het model; het kind leest, maakt klad en antwoordt.
4. Nakijken → juist? Zo niet: `diagnose()` → denkfoutcode → hulpje, tweede kans, "Zo kan het:".
5. `sessie` bewaart het antwoord, `punten` en de avatar reageren en `herhaling` werkt de herhaalbak bij.
6. Na de reeks: score, fouten opnieuw, gelijkaardige vragen.

Een nieuw onderwerp maken betekent dus: **één onderwerp in de kern** (generator, nakijken, diagnose, uitleg,
oplossing) + **leerlijn-data** + **één regel in het leerplan** (`terminal/curriculum/`). Menu's, opslag, rapporten,
herhaling en punten werken dan automatisch mee. De regels staan in `CLAUDE.md`.

### Menu's (boom, zoals in 0.20)
```
Startscherm  (Leeravontuur · "een gratis leerprogramma van Solve It Now" · "Iedereen moet kunnen leren")
└─ Wie ben jij?  [Imrane] [+ Nieuw kind] [Ouders]
   └─ Hoofdmenu van het kind  (avatar en punten rechts)
      ├─ 1 ▶ Verder                     (eerst de herhaalvragen, anders de vorige oefening)
      ├─ 2 Herhalen (n)                 (de herhaalbak van vandaag)
      ├─ 3 Wiskunde → domein → onderwerp, met toetsen per onderwerp:
      │       Enter reeks · V vrij · S spiekbrief · T 60 s · Z 20 sommen · H tabel-oefening
      │       (alleen de toetsen die gelden; daarna terug op hetzelfde onderwerp)
      │     Getallen · Hoofdrekenen · Cijferen · Breuken en procenten · Meten ·
      │     Tijd, geld en snelheid · Meetkunde · Vraagstukken
      ├─   Taal  (later) → Werkwoordspelling · Spelling · Zinsontleding · Woordenschat · Lezen
      ├─   Frans (later) → Woordenschat · Vervoegen · Zinnetjes · Uit het hoofd
      ├─ 4 Spiekbrieven → vak → domein → spiekbrief
      ├─ 5 Mijn avatar                  → W winkel · K kast · L schermkleuren
      ├─ 6 Zeg het ons                  (opmerking voor de ouder)
      ├─ 7 Wissel van kind
      └─ 8 Stoppen
Ouders (wachtwoord, of --ouder)
├─ Rapporten       → kind → periode → overzicht per vak › domein › onderwerp · kalender · denkfouten · status · export
├─ Kinderen        → naam · leerjaar · Weergave · timer zichtbaar · pincode · winkel-straf · gegevens exporteren · wissen
├─ Punten          → logboek · bonus geven
├─ Wachtwoord wijzigen
└─ Opmerkingen     (uit "Zeg het ons")
Later in het ouderdeel: Examens · Eigen inhoud · Dictee afdrukken · Schooljaar (de wissel op 1 september)
```
- **Hoogstens 10 items per menu** (de cijfertoetsen 1–9 en 0). Het hoofdmenu heeft er nu 8: met Taal en Frans zit
  het vol. Vóór er nog iets bijkomt (Examen, Avontuur), kiest de vader een oplossing.
- Weg sinds 0.20: "Leren & oefenen", het menu Snelrekenen (nu T/Z in Hoofdrekenen) en het menu Opties.

### Muis (alles kan ook met het toetsenbord)
Wie snel naar de muis grijpt, kan **overal klikken**, net als in btop:
- **Menu's:** klik op een keuze. De knoppen in de voetregel (`[Enter] reeks`, `[V] vrij`, `[Esc] terug` …) zijn
  klikbaar. Klik op de broodkruimel om terug te springen naar een hoger niveau.
- **Rooster** (eenhedentabel, cijferen): klik op een vakje om het te selecteren en typ dan.
  Klik tussen twee vakjes om de **komma** daar te zetten.
- **Breukbalk en honderdveld:** klik op een stuk of vakje om het te kleuren.
- **Getallenlijn:** klik op een plek om de pijl daar te zetten. Het scrollwiel zoomt in en uit.
- **Schatkaart en klok:** klik waar het kruisje moet; in het klokvenster sleep je de wijzer.
- **Klad en antwoord:** klik om te wisselen. **Meerkeuze, winkel en kast:** klik op een antwoord of item.
- **Lange teksten en rapporten:** scrollen met het wiel.
- Later: de **zinsontleder** (klik een woord of sleep over een groep, klik dan het label).

**Techniek:**
- Elk scherm registreert tijdens het tekenen zijn **klikzones** (rechthoek → actie). Eén centrale verdeler zet een klik om
  in dezelfde actie als de bijhorende toets. Muis en toetsenbord delen dus dezelfde logica, en er is maar één pad
  om te testen.
- **Muis aan/uit** per kind (Ouders › Kinderen › Weergave, of `--geen-muis`). Als de muis aan staat, kun je tekst niet
  meer gewoon selecteren; in de meeste terminals lukt dat dan met Shift ingedrukt.
- Geen "hover"-effecten: die werken niet betrouwbaar in alle terminals.

**Navigatie overal hetzelfde:**
- ↑/↓ + Enter om te kiezen, of het cijfer van de keuze (ook het numeriek klavier)
- Esc = terug; in een oefening: `Tab` = klad, `?` = een volgende tip
- de voetregel toont altijd de toetsen die gelden
- een broodkruimel bovenaan: `Leeravontuur › Wiskunde › Breuken en procenten › Vereenvoudigen`

### Schetsen (80×24)
```
 Leeravontuur

    Hallo Imrane! Wat wil je doen?

       1. ▶ Verder          breuken vereenvoudigen               ▄▄▄▄▄▄▄▄▄▄
       2. Herhalen (7)      wat je moeilijk vond                ▀▀▀▀▀▀▀▀▀▀▀▀
       3. Wiskunde          rekenen, meten, meetkunde, vraagst▄▀▀▀▀▀▀▀▀▀▀▀▀▀▀▄
       4. Spiekbrieven      uitleg om terug te kijken         ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
       5. Mijn avatar       winkel, kast, punten en schermkleure▀▀▀▀▀▀▀▀▀▀▀▀
       6. Zeg het ons       wat vind je leuk of moeilijk?       ▀▀▀▀▀▀▀▀▀▀▀▀
       7. Wissel van kind   iemand anders wil oefenen            ▀▀▀▀▀▀▀▀▀▀
       8. Stoppen
                                                              ★ 340 punten

    Solve It Now · gratis · iedereen moet kunnen leren
 [↑↓] kiezen  [Enter] ok  [Esc] terug
```
```
┌ Leeravontuur › Wiskunde › Breuken en procenten › Vereenvoudigen ── 4/10 ┐
│  Vereenvoudig zo ver als je kan:   6/8                                  │
│                                                                         │
│   ┌──┬──┬──┬──┬──┬──┬──┬──┐                                             │
│   │██│██│██│██│██│██│  │  │   6/8     (v = stukken samenvoegen)         │
│   └──┴──┴──┴──┴──┴──┴──┴──┘                                             │
│                                                                         │
│  Antwoord:  [ 3/4    ]                                     ▄▄▄▄         │
│                                                            █^‿^█  Top!  │
│  ✔ Juist! 6/8 → deel teller en noemer door 2 → 3/4         ▀▀▀▀         │
└ Enter volgende · Esc stoppen ───────────────────────────────────────────┘
```
(De eerste schets is het echte hoofdmenu van 0.20; de tweede is een schets van de indeling.)

### Instellingen (waar ze nu staan)
| Instelling | Waar | Argument bij het starten |
|---|---|---|
| **Schermkleuren**: standaard, kleurenblind (rood-groen, blauw-geel), hoog contrast, geen kleur | het kind: Mijn avatar › L | `--kleurenblind [blauw-geel]`, `--contrast`, `--geen-kleur` |
| Eenvoudige tekens (ASCII) | de ouder: Kinderen › Weergave | `--ascii` |
| Muis | de ouder: Kinderen › Weergave | `--geen-muis` |
| Typrichting in tabellen | de ouder: Kinderen › Weergave | – |
| Avatar, animaties | de ouder: Kinderen › Weergave | – |
| Klok in een eigen venster | de ouder: Kinderen › Weergave | `--zonder-klokvenster` |
| Leerjaar, timer zichtbaar, pincode, winkel-straf | de ouder: Kinderen | – |
| Accent-snelcodes (`e'` → é) | later (Frans) | – |
| Taal van de menu's | nu Nederlands; de teksten staan apart, zodat een vertaling later kan | – |

- De instellingen worden **per kind** bewaard. Een argument bij het starten gaat voor zolang het programma loopt en
  wordt niet bewaard (handig op een andere computer).
- **Kleurenblind:** blauw = juist, oranje = fout, en **altijd** ook een symbool (✔ ✘ !), zodat kleur nooit de enige
  aanwijzing is. Het palet zit op **één plek** (`terminal/thema.py`): schermen vragen "kleur voor *juist*", niet
  "groen". Ook de avatar heeft kleurenblind-paletten.

## M. Volgend schooljaar: niveaus schuiven mee
**Ja: als Imrane in het 6de zit, wordt Heel moeilijk het 2de middelbaar.**
- Het **leerjaar** staat in het profiel van het kind, niet in de code. De niveaus zijn een **verschuiving**
  tegenover dat leerjaar (−1, 0, +1, +2).
- **Schooljaarwissel:** vanaf 1 september vraagt het programma (in het ouderdeel en bij de eerste start):
  "*Zit Imrane nu in het 6de leerjaar?* [Ja] [Aanpassen]". Dubbelen of een sprong kan dus ook.
- **Wat blijft:** alle geschiedenis, de beheersing per vaardigheid, de herhaalbak, de punten en de avatar.
  Wat hij al beheerst, gaat naar onderhoud. Wat nieuw is in het 6de, krijgt de status "nog niet gezien".
- **Rapporten per schooljaar**, met een vergelijking: "*5de lj: breuken 78 % → 6de lj: 85 %*".
- **Bijsturen per vak is mogelijk** (bv. sterk in rekenen, minder in Frans): de ouder kan het leerjaar per vak
  afwijkend zetten.

### Hoe het technisch kan: leerlijnen in plaats van niveaus
Elke vaardigheid heeft een **leerlijn** in JSON: per leerjaar de bereiken en wat wel en niet mag. Een voorbeeld:
```json
{ "vaardigheid": "wiskunde.breuken.vereenvoudigen",
  "leerlijn": {
    "4": null,
    "5": {"noemer_max": 12,  "factor_max": 4, "uitleg": "deel teller en noemer door hetzelfde getal"},
    "6": {"noemer_max": 60,  "factor_max": 12, "ggd": true},
    "m1": {"noemer_max": 144, "negatief": true},
    "m2": {"letters": true} } }
```
De generator leest alleen de parameters van het gevraagde leerjaar. **Een nieuw leerjaar is dus vooral nieuwe data,
geen nieuwe code.** Alleen echt nieuwe onderwerpen (bv. vergelijkingen in het 2de middelbaar) vragen een nieuw
vaardigheidsbestand.

### Wat er moet bijkomen voor volgend schooljaar (6de lj → Heel moeilijk = 2de middelbaar)
- **Wiskunde 2de middelbaar:** letterrekenen, vergelijkingen van de eerste graad, machten, wetenschappelijke notatie,
  meer meetkunde (driehoeken, vierhoeken, symmetrie) en statistiek.
- **Taal en Frans 2de middelbaar:** extra tijden en grammatica, en uitgebreidere woordenschat.
- Ik plan dat als **een eigen fase rond de zomer**, zodat het klaar is voor september.

## N. Publiceren en het werk per nieuw "jaar" klein houden
**Niet per jaar publiceren, maar één app met inhoud die meegroeit.**
- **De app** (de motor) krijgt gewone versies (1.0, 1.1, …) via GitHub Releases. Iedereen gebruikt dezelfde app.
- **De inhoud** (leerlijnen, woordenlijsten, sjablonen) zit in **inhoudspakketten** met een eigen versie
  (bv. `vlaanderen-2026.2`). Een nieuw schooljaar of een aanpassing aan de nieuwe minimumdoelen is meestal alleen een
  inhoudsupdate.
- **Elk leerjaar zit er gewoon in** (van het 3de lj tot het 2de middelbaar, en later verder). Elk kind kiest zijn
  eigen leerjaar. Er bestaat dus nooit een aparte "versie 5de leerjaar".

### Hoe we het werk per nieuw leerjaar verminderen
1. **Generieke oefenvormen** die overal hergebruikt worden: rooster, getallenlijn, breukbalk, meerkeuze, invullen,
   sorteren/zinsbouw, kladblad, vervoegingstabel. Een nieuw onderwerp kiest meestal een bestaande vorm.
2. **Generatoren met parameters uit de leerlijn**: een nieuw leerjaar = een kolom data invullen.
3. **Sjabloontaal voor vraagstukken** (stappen, foute paden, verwoordingen in JSON). Nieuwe vraagstukken schrijven
   zonder te programmeren.
4. **Koppeling met de officiële doelen:** elke vaardigheid verwijst naar de code van het minimumdoel of de eindterm.
   Een **dekkingsrapport** (`python -m leeravontuur.dekking`) toont per leerjaar welke doelen nog geen oefeningen
   hebben. Zo zie je meteen wat er voor een nieuw jaar ontbreekt.
5. **Automatische tests per leerlijn:** voor elk leerjaar maakt elke vaardigheid 500 vragen zonder fouten.
   Een tikfout in de data valt meteen op.
6. **Validatie van de inhoud** (schema-controle van de JSON), zodat ook niet-programmeurs veilig inhoud kunnen toevoegen.
7. Later is een **eenvoudige inhoudseditor in het ouderdeel** mogelijk. Leerkrachten of andere ouders kunnen dan
   pakketten maken en delen.
8. De structuur laat ook **andere regio's** toe (bv. een pakket `nederland` met groep 7/8), zonder dat de app verandert.

### Gratis voor iedereen
- **Startscherm en "Over":** *Leeravontuur, een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren.*
  Ook in de README en in `--versie`.
- **Licentie: CC BY-NC-SA 4.0** (jouw keuze): gratis gebruiken, delen en aanpassen mag, met vermelding van
  Solve It Now, **niet commercieel**, en aanpassingen onder dezelfde licentie. Scholen en ouders mogen het dus vrij
  gebruiken; een bedrijf mag het niet verkopen of in een betalend product steken.
  - Ter info (het verandert je keuze niet): Creative Commons raadt zelf CC-licenties af voor *code*, omdat ze niets regelen
    over broncode en patenten. Door "NC" geldt het ook niet officieel als "open source". Dat is geen probleem voor GitHub of
    `pipx`, wel als je het ooit in een Linux-distributie wil laten opnemen.
  - Wil je de code juridisch steviger afdekken met dezelfde bedoeling, dan kan de code onder **PolyForm Noncommercial 1.0**
    en de inhoud (leerlijnen, woordenlijsten, teksten, avatar) onder **CC BY-NC-SA 4.0**. Anders gebruik ik overal
    CC BY-NC-SA 4.0, zoals je vroeg.
  - Een `LICENSE`-bestand + een vermelding in de README en in het "Over"-scherm.
- **Makkelijk installeren voor gewone ouders** (eigen fase bij de publicatie):
  - `pipx install leeravontuur` voor wie Python heeft.
  - Daarnaast **kant-en-klare programma's per systeem** (Windows .exe, macOS, Linux), gebouwd door GitHub Actions
    met PyInstaller. Dan hoeft niemand Python te installeren.
- **Privacy bij publicatie:** alles blijft lokaal op de computer, er worden geen gegevens verstuurd. Dat staat expliciet
  in de README. Zo is er geen AVG-probleem zolang er geen server is (zie J).

## O. Geparkeerd: het deel voor coaches en leerkrachten

*Nog niet ingepland.* De volledige brainstorm (coach eerst, deelpakket van de ouder, focusplan, klad terugzien,
opdrachten en toetsen, klasschaal, en de vragen voor de sponsor) staat in [leerkracht-coach.md](leerkracht-coach.md).

## Beslissingen van de vader (logboek)
Wat beslist is, staat hier op één plek; de uitwerking staat in de code, `CLAUDE.md` en de CHANGELOG.
- **Werkwijze:** de vader beslist over alles wat het kind of de ouder ziet; grote veranderingen eerst als inventaris
  en plan in fasen, met een stop na elke fase; samenvoegen pas na groene CI en zijn akkoord (merge-commit). Elke fout
  die hij vindt, wordt een GitHub-issue.
- **Licentie:** CC BY-NC-SA 4.0, "Solve It Now · Iedereen moet kunnen leren" (zie N).
- **Dictee:** afgedrukt en voorgelezen door de ouder, geen computerstem.
- **Menu's (0.20):** één leerplan Vak › Domein › Onderwerp; toetsen per onderwerp (ook kleine letters, klikbaar);
  hoogstens 10 items per menu; Tijd, geld en snelheid is een eigen domein na Meten; snelrekenen zit in Hoofdrekenen
  (T/Z, Gemengd); Opties is verhuisd (Schermkleuren bij het kind, Weergave per kind bij de ouder); de spiekbrief bij
  Meten heet "Oppervlakte en formules".
- **Rapport:** per vak › domein; snelrekenen staat apart onder zijn onderwerp, niets samengeteld, ook in de status
  (twee regels); de export houdt alle oude kolommen en krijgt vak en domein erbij.
- **Handleiding:** niet meer per versie; één handleidingproject op het einde (volledige test + handleiding voor kind,
  ouder en coach). Tot dan houdt `NOG_TE_BESCHRIJVEN` bij wat er nog in moet.
- **Coach en leerkracht:** eerst de coach, offline, de ouder blijft eigenaar van de gegevens
  (`docs/leerkracht-coach.md`); nog niet ingepland.
- **Taal** begint pas als de vader klaar is met testen en de issues opgelost zijn.

## Structuur (zoals in 0.20)
```
oefeningen.py                 starter: python3 oefeningen.py [--ouder] [--ascii] … (zie --help)
requirements.txt              windows-curses (alleen Windows)
CLAUDE.md                     afspraken: architectuur, menu's, werkwijze met Claude, uitbrengen
CHANGELOG.md · README.md      wat er nieuw is (gewone taal) · installeren en starten
leeravontuur/
  __main__.py                 startargumenten
  kern/                       alle logica en opslag, zonder curses
    onderwerp.py              Onderwerp en Vraag: maken, nakijken, diagnose, uitleg, tips, klad-oplossing
    catalogus.py              alle onderwerpen en denkfouten (namen voor rapporten)
    vaardigheden.py           register: vak → domein → vaardigheid
    leerjaren.py · leerlijnen.py   leerjaar van het kind, relatieve niveaus · leerlijnen laden per leerjaar
    selectie.py · herhaling.py     slimme keuze, niet binnen 30 dagen · herhaalbak en status per vaardigheid
    sessie.py                 elke oefening: tijd, vraagsleutel, diagnose, punten
    opslag.py                 SQLite, migraties, reservekopieën; het enige dat bewaart
    rapporten.py              rapport per periode en per vak › domein, export CSV/TXT/JSON
    klad.py · verhaal.py      kladregels lezen en nakijken · sjablonen voor de verhaalmachine
    getal.py · modellen.py    getallen met komma · modellen als data (getallenlijn, rooster, breukbalk, klok …)
    punten.py · avatar.py · winkel.py   punten met anti-farm · pixel-avatar · winkel en aankoop-challenge
    snelrekenen.py            60 seconden, 20 sommen, records
    instellingen.py · wachtwoord.py · paden.py · klok.py · slot.py · foutlog.py · feedback.py
    wiskunde/                 getallen, hoofdrekenen, cijferen, breuken, procenten, eenheden, grootheden
                              (tijd, geld, snelheid), klok, meetkunde, vraagstukken
  terminal/                   alleen weergave en invoer (curses)
    curriculum/               het leerplan: __init__ (Vak, Domein, Onderwerp), modi, wiskunde
    app.py · navigatie.py     hoofdmenu, Verder, Herhalen · Vak › Domein › Onderwerp + toetsen
    scherm.py · klikzones.py  tekenen, menu, voetregel, broodkruimel, toetsen (ook het numeriek klavier) · muis
    thema.py · tekens.py      kleurrollen en thema's · ASCII-vervanging
    oefenaar.py               het scherm voor elke oefening (vrij, reeks, tips, tweede kans, punten)
    kladblad.py · rooster.py · balk.py · vraagstuk.py · modellen.py   klad · cijferen en staartdeling ·
                              breukbalk, honderdveld, schatkaart, klok zetten · vraagstuk in 4 stappen · tekenen
    avatar.py · maatje.py     pixel-avatar · het oefenmaatje
    venster.py                praat met het klokvenster
    nepscherm.py              een scherm zonder terminal, voor de tests
    schermen/                 eenheden (tabel), kinderen (Wie ben jij?), ouder, snelrekenen, winkel (avatar, kast)
  venster/                    klokbeeld.py (de klok als vormen) · klokvenster.py (tkinter, eigen proces)
  inhoud/
    leerlijnen/               JSON per vaardigheid: parameters per leerjaar
    vraagstukken/             werelden.json · zinnen.json
    avatar/                   onderdelen.json · winkel.json
tests/                        unittest (stdlib), ook de aapjestest
docs/                         plan.md · testlijst.md · leerkracht-coach.md · menu-inventaris.md ·
                              handleiding/ · tools/ (handleiding.py, schermafdrukken.py, scenarios.py)
.github/workflows/            tests op ubuntu/macos/windows × Python 3.10 en 3.14
```
**Later** (gepland, nog niet gebouwd): `kern/taal/` (werkwoorden met regelmotor, spelling, zinsontleding,
woordenschat, lezen, dictee), `kern/frans/` (woordenschat, vervoegen, zinnen, accenten, uit het hoofd),
`terminal/curriculum/taal.py` en `frans.py`, `kern/afdrukken.py` (dictee- en oefenbladen als HTML),
`kern/avontuur.py`, examens, en `inhoud/` met woordenlijsten en leesteksten.

## Fasen (elk apart getest, gedemonstreerd en gepusht; na elke fase werkt alles)
Kleine fasen, zodat Imrane snel nieuwe dingen krijgt en de vader tussendoor kan bijsturen. De volgorde schoof
onderweg (wat hij op school nodig had, ging voor). Status: **✔** klaar (met versie) · **▶** nu of volgende ·
**·** gepland · **◐** deels.

### Klaar (in de volgorde waarin het uitkwam)
| Versie | # | Fase | Wat er daarna werkt |
|---|---|---|---|
| ✔ 0.1 | 1 | **Fundament** | kern/terminal-scheiding, `CLAUDE.md`, starter + requirements, leerlijnen + relatieve niveaus, startscherm met Solve It Now, ASCII-terugval, **muis/klikzones**, NepScherm, CI op 3 systemen; eenheden (lengte/massa) |
| ✔ 0.2 | 2 | **Opslag + kindaccounts** | SQLite met migraties en UUID's; kind kiezen bij de start; elk antwoord met tijd, vraagsleutel en diagnosecode; vaardighedenregister |
| ✔ 0.3 | 3 | **Ouderdeel + rapporten** | wachtwoord (versioned hash), kinderen beheren, rapporten per periode met kalender, export, alles wissen per kind |
| ✔ 0.4 | 4 | **Opties + thema's** | kleurenblind (2 varianten), hoog contrast, geen kleur, ASCII, avatar, animaties, typrichting; alle schermen via `thema.py` (in 0.20 verhuisd naar Schermkleuren en Weergave) |
| ✔ 0.5 | 5 | **Herhaling + slimme selectie** | fouten opnieuw, gelijkaardige vragen, herhaalbak (Leitner), "niet binnen 30 dagen", adaptieve keuze, status per vaardigheid in het rapport |
| ✔ 0.6 | 6 | **Punten + avatar (basis)** | puntenlogboek met anti-farm; pixel-avatar (lagen, ankers, uitdrukkingen, ▀-weergave, terugval); oefenmaatje met reacties |
| ✔ 0.7 | 7 | **Winkel** | een 30-tal items, kopen, aankoop-challenge met "ben je zeker?", mini-lesje, pakje onderweg, kast |
| ✔ 0.8 | 8 | **Hoofdrekenen + snelrekenen** | strategieën met uitleg, timer zichtbaar/verborgen, records |
| ✔ 0.9 | 9 | **Getallen + getallenlijn** | plaatswaarde, afronden, deelbaarheid, getallenlijn met zoom, negatieve getallen, thermometer, sprongen |
| ✔ 0.10 | 10 | **Cijferen** | +, −, × onder elkaar in het rooster met onthouden-rij; staartdeling stap voor stap |
| ✔ 0.11 | 11 | **Breuken** | breukbalk (noemer, arceren, vereenvoudigen, vergelijken, gelijknamig), breuk van een getal |
| ✔ 0.12 | 12 | **Procenten** | honderdveld, procentstrook, korting/btw |
| ✔ 0.12.1 | – | **Stabiliteit** | vangnet met een vriendelijke melding en `fouten.log`, dagelijkse reservekopie en herstel, waarschuwing bij twee keer openen |
| ✔ 0.13 | – | **Eerste bèta** | "Zeg het ons", de testlijst voor de ouder |
| ✔ 0.14 | 15 | **Meer eenheden** | inhoud, oppervlakte (2 vakjes/kolom), volume (3 vakjes), dm³ ↔ l; nieuw domein Tijd, geld en snelheid |
| ✔ 0.15 | 22 | **Meetkunde & rooster** + handleiding | cm²-rooster (omtrek/oppervlakte), formules, hoeken, schatkaart, schaal; de handleiding `docs/handleiding/` (uitleg per onderwerp, tabellen per leerjaar, denkfouten, schermafdrukken) |
| ✔ 0.16 | 16a | **Vraagstukken met kladblad** | 4 stappen met Gegeven/Gevraagd/Oplossing/Antwoord, kladparser, verhaalmachine, foute paden automatisch, getrapte tips, tweede kans |
| ✔ 0.17 | 16b | **Vraagstukken 2** | meer structuren en werelden, Speurneus (zoek de fout), Schatten & controleren |
| ✔ 0.18 | 16c | **De klok + tijd in vraagstukken** | wijzerklok in een eigen venster (tkinter, eigen proces; terugval in de terminal), tijden in Vlaamse woorden, 24 uur; vraagstukken met tijd (20 structuren × 22 werelden) |
| ✔ 0.19 | 16d | **Eén vaste werkwijze** | elke oefening: lees, klad (`Tab`, elke regel nagekeken), antwoord; getrapte tips, tweede kans, "Zo kan het:"; slim × en : met splitsen |
| ✔ 0.20 | A | **Nieuwe menu's** | het leerplan (`terminal/curriculum/`): Vak › Domein › Onderwerp met toetsen per onderwerp; snelrekenen in Hoofdrekenen; Opties verhuisd; rapport per vak › domein, snelrekenen apart; CSV met vak en domein |
| ✔ 0.20.1 | – | **Numeriek klavier** (#11) | / * - + en Enter van het numeriek klavier op Windows en Linux |

### Nog te doen (voorstel voor de volgorde; de vader beslist)
| Status | # | Fase | Wat er daarna werkt |
|---|---|---|---|
| ▶ | – | **Issues uit de tests van de vader** | elke fout een issue, een branch en een PR ("Fixes #n") |
| ▶ | 13 | **Taal 1: werkwoordspelling** (stap B, B0–B6) | werkwoordmachine (tt, vt met 't kofschip, vd, bijvoeglijk vd), d/t-keuze, foutenjager; Taal in het hoofdmenu |
| · | 14 | **Taal 2: spelling** | meervoud, verkleinwoord, lettergrepen, ei/ij-au/ou, tussen-s, trema/koppelteken/apostrof, snel-spellen |
| · | 17 | **Taal 3: zinsontleding** | zinsontleder (pv, onderwerp, gezegde, LV, MV, bijw. bep.), woordsoorten, proefjes |
| · | 18 | **Taal 4: woordenschat + lezen** | synoniemen, uitdrukkingen, spreekwoorden; leesteksten met vragen; eigen teksten van de ouder |
| · | 19 | **Dictee (afdrukken)** | afdrukbaar ouder- en kindblad, woordpakket van de week, overtypen + diagnose achteraf, flitsdictee |
| · | 20 | **Frans 1** | woordenschat FR↔NL met lidwoordkleuren, accentinvoer en "bijna juist"; eigen thema's; basispakketten; *être*/*avoir* |
| · | 21 | **Frans 2** | -er-werkwoorden en andere tijden per niveau, zinnen bouwen, vertalen, vraag-antwoord, uit het hoofd leren + luistermodus voor de ouder |
| · | 23 | **Examens** | ouder stelt samen (ook als sjabloon), kind start zonder hulp, verse vragen, resultaten in het rapport |
| · | C | **Coach** (geparkeerd) | C1–C4 uit `docs/leerkracht-coach.md` (deelpakket, coachmodus, focusplan, klad terugzien); C5+ na fase 23 |
| · | 26 | **Leerjaar 2de middelbaar + schooljaarwissel** | leerlijnen tot m2, letterrekenen, vergelijkingen, uitbreiding taal en Frans; de vraag bij de wissel op 1 september (klaar vóór september 2027) |
| · | H | **Handleidingproject** | een volledige test van alle functies + de handleiding voor kind, ouder en coach; nieuwe schermafdrukken |
| · | 24 | **Avontuur** | kaart, 7 werelden die rekenen, taal en Frans mengen, sterren, eindbazen, badges (+ zeldzame winkelitems) |
| ◐ | 25 | **Afwerking** | README per systeem en de handleiding zijn er; nog: prestatie op trage pc's, toegankelijkheid nakijken |
| ◐ | 27 | **Publicatie** | de licentie (CC BY-NC-SA 4.0) is er; nog: `pipx`-pakket, kant-en-klare programma's via GitHub Actions, dekkingsrapport, inhoudspakketten met versies, "Over"-scherm |

Elke nieuwe fase voegt ook passende **winkelitems en avatar-reacties** toe (bv. een rekenmachine-bril na Cijferen).
De volgorde kan verschuiven als Imrane iets dringend nodig heeft voor school.

## Verificatie
- `python -m unittest`:
  - Per vaardigheid en niveau 500 willekeurige vragen. Het antwoord is exact juist (`Decimal`/`Fraction`),
    de niveaugrenzen gelden en uitleg en diagnose crashen niet.
  - **Diagnosetests:** voor elke bekende denkfout geeft het verwachte foute antwoord de juiste diagnosecode.
  - **Vraagstuk-tests:** de juiste stappen, de tussenuitkomsten en elk fout pad worden herkend.
    De kladparser kent `0,75 × 3,20 = 2,40` als waar en `= 24` als fout.
  - **Taaltests:** de regelmotor geeft dezelfde vormen als de gecontroleerde lijst (tt, vt, vd, meervoud, verkleinwoord).
  - Selectie: geen vraagsleutel herhaald binnen 30 dagen (met een gesimuleerde klok). Examens bevatten alleen nieuwe sleutels.
  - **Leerlijnen:** elke JSON-leerlijn is geldig volgens het schema. Per leerjaar 500 vragen per vaardigheid.
    Een gesimuleerde schooljaarwissel (5de → 6de) behoudt de geschiedenis en verschuift de niveaus.
  - **Muis:** met NepScherm klikken op menu-items, roostervakjes, de plek tussen twee vakjes (komma),
    breukbalkstukken, de getallenlijn en het scrollwiel. Elke klik geeft dezelfde actie als de toets.
    In tmux sturen we echte muis-escapecodes (SGR) naar het programma.
  - **Thema's:** geen enkel scherm gebruikt een kleur rechtstreeks. Elk thema heeft alle rollen
    (juist, fout, actief, accent …). Juist en fout hebben altijd ook een symbool.
  - Opslag/rapporten op een tijdelijke databank, met filteren op datum. Wachtwoord-hash (ook een upgrade van een oude
    hashversie). Herhaalbak-schema. Migraties van schemaversie N naar N+1.
  - **Punten/winkel:** anti-farm-regels, niet kopen zonder genoeg punten, het pad juist / fout → "zeker?" → lesje → pakje
    onderweg, levering na N juiste antwoorden.
  - **Avatar:** elke combinatie van vorm × onderdelen blijft binnen het raster en de ankers kloppen per vorm.
    Snapshot-tests van de tekstweergave.
- NepScherm-flows (ook in CI op Windows, macOS en Linux):
  - kind kiezen → reeks → fouten opnieuw
  - ouder → examen maken → kind maakt het examen → rapport
  - breukbalk arceren/vereenvoudigen, getallenlijn, zinsontleder, kladblad
- Op Linux een echte terminaltest in tmux 80×24 per fase, met schermafdrukken in het verslag.
- **Avatar visueel controleren:** de tmux-uitvoer met kleurcodes (`capture-pane -e`) omzetten naar HTML en met de
  meegeleverde Chromium/Playwright een **echte afbeelding** maken. Die bekijk ik zelf voor ik iets push, en ik stuur
  ze jou als voorbeeld. Zo beoordeel ik de pixel-art op wat je echt ziet, niet blind.
- Afdrukbladen: de HTML-uitvoer via Playwright als PDF/afbeelding renderen en bekijken (het opmaakt goed op A4).
- Accentinvoer: `é` rechtstreeks (AZERTY) én via `e'` werkt in de NepScherm-tests en in tmux.
- README per systeem (Python installeren, `pip install -r requirements.txt`, starten, ouderdeel, afdrukken).
