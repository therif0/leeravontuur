# Plan: "Leeravontuur": rekenen en taal leren en oefenen in de terminal (Windows, macOS, Linux)

## Context
Het huidige programma (`oefeningen.py`, ±900 regels, één bestand, curses) oefent lengte en massa.
Imrane (**5de leerjaar**, Vlaanderen) vindt het superleuk. De vader wil het uitbreiden tot een volwaardig leerprogramma:
- rekenen in de volle breedte, met een echt leerproces per onderwerp
- vraagstukken met een kladblad en grondige uitleg waarom iets juist of fout is
- hoofdrekenen en snelrekenen
- examens die de ouder samenstelt
- kindaccounts
- ouderrapporten op datum achter een wachtwoord
- herhaling van fouten
- **taal** (Nederlands) in dezelfde stijl, en **Frans** (woordenschat, vervoegen, korte zinnetjes, uit het hoofd leren)
- dictees die **afgedrukt** worden en die de ouder voorleest (geen computerstem)
- geen vragen die hij na een tijd van buiten kent
- een **avatar** (blokje à la Geometry Dash) die hij met verdiende punten aankleedt in een **winkel**,
  waar elke aankoop een kleine rekenchallenge is; de avatar is ook zijn oefenmaatje
- beveiliging die nu eenvoudig is, maar later kan meegroeien

Alles in de terminal, licht, op Windows, macOS en alle Linuxen, met een requirements-lijst.
Later moeten er een GUI en andere vakken (aardrijkskunde, geschiedenis) bij kunnen.
Het doel: dieper en slimmer dan de typische oefenwebsites (bv. Computermeester), die er mooi uitzien maar beperkt zijn.

Niveaus zijn **relatief tegenover het leerjaar van het kind** (zie sectie M):
**Makkelijk** = leerjaar − 1 · **Normaal** = eigen leerjaar · **Moeilijk** = + 1 · **Heel moeilijk** = + 2.
Nu (5de leerjaar) betekent dat: 4de lj · 5de lj · 6de lj · 1ste middelbaar. In de tabellen hieronder staat de inhoud per
**leerjaar**, zodat ze volgend jaar gewoon één kolom opschuift.

Op het startscherm: **"Leeravontuur, een gratis leerprogramma van Solve It Now. Iedereen moet kunnen leren."**

---

## Eerlijke inschatting (ook wat minder goed is)
- **De omvang is groot.** Alles samen is dit gerust 10× het huidige programma. Daarom bouw ik in fasen waarbij
  **na elke fase iets bruikbaars werkt**. Ik start met het fundament (accounts, opslag, rapport, geschiedenis)
  en zet daar onderwerp per onderwerp bovenop. Wat Imrane op school nodig heeft, kan voorgaan.
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

## F. Herhaling na een reeks
- Na **elke** reeks, en ook bij het stoppen in vrij oefenen: "**Fouten opnieuw**" (dezelfde vragen, direct).
- Daarna: "**Gelijkaardige vragen**" (dezelfde vaardigheid, nieuwe parameters) om te controleren of de regel nu zit.
- Fouten gaan ook automatisch in de herhaalbak voor volgende dagen (zie A.7).
  Het hoofdmenu toont "Je hebt 7 vragen om te herhalen".

## G. Accounts, ouderdeel, rapporten en examens
- **Kindaccounts:** bij de start kiest hij zijn naam (met een optionele kind-pincode). Elk kind heeft eigen vooruitgang,
  sterren, herhaalbak en instellingen.
- **Ouderdeel:** via `python3 oefeningen.py --ouder` of het menu-item "Ouders" + wachtwoord.
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

## L. Architectuur, menu's en opties

### Lagen
```
 ┌───────────────────────────────────────────────────────────────────┐
 │  terminal/  (curses)                 later: gui/ (tkinter of web)  │  ← alleen tekenen + toetsen
 │  schermen · rooster · modellen · avatar · kladblad                 │
 └───────────────▲──────────────────────────────────▲─────────────────┘
                 │ vraagt: "geef volgende vraag",    │ krijgt: Vraag, Model, Feedback,
                 │ "controleer dit antwoord"         │ Rapport (gewone Python-objecten)
 ┌───────────────┴──────────────────────────────────┴─────────────────┐
 │  kern/                                                             │
 │  sessie ── selectie ── vaardigheden ──► wiskunde/ taal/ frans/     │
 │     │          │            │              (generator, controle,  │
 │     │          │            └── leerlijnen  diagnose, uitleg)      │
 │     │          └── herhaling (herhaalbak)                          │
 │     └── punten · avatar · winkel · avontuur · rapporten · afdrukken│
 └───────────────────────────────▲────────────────────────────────────┘
                                 │ één opslag-interface
 ┌───────────────────────────────┴────────────────────────────────────┐
 │  opslag: SQLite (nu)  ·  later: versleuteld of server              │
 └────────────────────────────────────────────────────────────────────┘
 inhoud/ (JSON): leerlijnen, woordenlijsten, vraagstuk-sjablonen, avatar-onderdelen, thema's
```
**De vaste lus voor elke oefening (in elk vak hetzelfde):**
1. `sessie` vraagt aan `selectie` welke vaardigheid nu komt (adaptief, herhaalbak, niet binnen 30 dagen).
2. De vaardigheid maakt een `Vraag` met het niveau uit de **leerlijn** van het juiste leerjaar.
3. De terminal toont de vraag en het model, en geeft het antwoord terug.
4. `controle()` → juist? Zo niet: `diagnose()` → denkfoutcode → uitleg.
5. `sessie` bewaart het antwoord, `punten` en `avatar` reageren en `herhaling` werkt de herhaalbak bij.
6. Na de reeks: rapport, fouten opnieuw, gelijkaardige vragen.

Een nieuw onderwerp maken betekent dus: **één vaardigheidsbestand** (generator, controle, diagnose, uitleg) +
**leerlijn-data**. Menu's, opslag, rapporten, herhaling, punten en examens werken dan automatisch mee.

### Menu's (boom)
```
Startscherm  (logo Leeravontuur · "een gratis leerprogramma van Solve It Now" · "Iedereen moet kunnen leren")
└─ Wie ben jij?  [Imrane] [+ nieuw kind] [Ouders 🔒]
   └─ Hoofdmenu van het kind  (avatar groot links, punten ★ rechts, meldingen: "7 vragen te herhalen", "Examen klaar")
      ├─ ▶ Verder waar je was          (voorstel: volgende stap in de leerladder)
      ├─ Avontuur                       → kaart → wereld → opdracht
      ├─ Leren & oefenen
      │   ├─ Wiskunde → domein (Getallen, Hoofdrekenen, Cijferen, Breuken, Procenten, Eenheden, Meetkunde, Vraagstukken)
      │   ├─ Taal     → domein (Werkwoordspelling, Spelling, Zinsontleding, Woordenschat, Lezen)
      │   └─ Frans    → domein (Woordenschat, Vervoegen, Zinnetjes, Uit het hoofd)
      │        └─ vaardigheid → [Ontdekken] [Oefenen met hulp] [Oefenen alleen] [Reeks van 10] [Vrij oefenen]
      │                          → niveau (Makkelijk/Normaal/Moeilijk/Heel moeilijk)
      ├─ Snelrekenen                    (60 seconden / 20 sommen, records)
      ├─ Herhalen  (n)                  (herhaalbak van vandaag)
      ├─ Examen    (als de ouder er een klaarzette)
      ├─ Mijn avatar                    → Paskamer · Winkel · Badges
      ├─ Spiekbrieven                   (per domein)
      ├─ Opties
      └─ Wissel van kind / Stoppen
Ouders 🔒 (wachtwoord, of --ouder)
├─ Rapporten       → kind → periode (dag/week/maand/eigen) → overzicht · kalender · per vaardigheid · denkfouten · export
├─ Examens         → nieuw · sjablonen · toewijzen · resultaten
├─ Kinderen        → toevoegen · leerjaar · instellingen (timer zichtbaar, open vakken, avatar, penaliteit winkel)
├─ Eigen inhoud    → woordenlijsten (NL/FR) · teksten om uit het hoofd te leren · leesteksten
├─ Dictee afdrukken→ kies inhoud → ouderblad + kindblad (browser) → achteraf overtypen
├─ Punten          → bonus geven · factoren
├─ Schooljaar      → leerjaren bevestigen bij de schooljaarwissel
└─ Wachtwoord · gegevens exporteren · alles wissen per kind
```
### Muis (alles kan ook met het toetsenbord)
Wie snel naar de muis grijpt, kan **overal klikken**, net als in btop:
- **Menu's:** klik op een keuze. De knoppen in de voettekst (`[Enter ok]`, `[Esc terug]`, `[? hulp]`) zijn klikbaar.
  Klik op de broodkruimel om terug te springen naar een hoger niveau.
- **Rooster** (eenhedentabel, cijferen, vervoegingstabel): klik op een vakje om het te selecteren en typ dan.
  Klik tussen twee vakjes om de **komma** daar te zetten.
- **Breukbalk:** klik op een stuk om het te **arceren**. Klik op `[−]`/`[+]` bij de noemer.
- **Getallenlijn:** klik op een plek om de pijl daar te zetten. Het scrollwiel zoomt in en uit.
- **Zinsontleder:** klik een woord aan (sleep over meerdere woorden voor een groep) en klik daarna het label.
- **Meerkeuze, winkel en paskamer:** klik op een antwoord, item of kledingstuk.
- **Lange teksten en rapporten:** scrollen met het wiel.

**Techniek:**
- Elk scherm registreert tijdens het tekenen zijn **klikzones** (rechthoek → actie). Eén centrale verdeler zet een klik om
  in dezelfde actie als de bijhorende toets. Muis en toetsenbord delen dus dezelfde logica, en er is maar één pad
  om te testen.
- **Optie "Muis aan/uit"** (`--geen-muis`). Als de muis aan staat, kun je tekst niet meer gewoon selecteren om te kopiëren.
  In de meeste terminals werkt dat dan nog met Shift ingedrukt; dat staat in de hulp.
- Geen "hover"-effecten: die werken niet betrouwbaar in alle terminals. Wel licht een vakje kort op als je erop klikt.

**Navigatie overal hetzelfde:**
- ↑/↓ + Enter om te kiezen, of het cijfer van de keuze
- Esc = terug, `?` = hulp bij dit scherm
- de voettekst toont altijd de toetsen
- een broodkruimel bovenaan: `Leren › Wiskunde › Breuken › Vereenvoudigen`

### Schetsen (80×24)
```
┌ Leeravontuur ─────────────────────────────── Imrane · 340 punten · ★ 12 ┐
│  ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄     Hallo Imrane!                                     │
│  █ (pixel-avatar) █   ▶ Verder: Breuken vereenvoudigen (oefenen alleen) │
│  █   16×8 tekens  █     Avontuur                                        │
│  █                █     Leren & oefenen                                 │
│  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀      Snelrekenen                                     │
│                         Herhalen (7)                                    │
│  "Nog 3 juiste         Examen ● klaar                                   │
│   antwoorden voor je   Mijn avatar                                      │
│   pakje!"              Spiekbrieven · Opties                            │
│                                                                         │
│  Solve It Now · gratis · iedereen moet kunnen leren                     │
└ ↑/↓ kiezen · Enter ok · Esc terug · ? hulp ─────────────────────────────┘
```
```
┌ Leren › Wiskunde › Breuken › Vereenvoudigen ─────── vraag 4/10 · 2:13 ─┐
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
(De echte schermen worden gebouwd en als afbeelding gecontroleerd; dit zijn schetsen van de indeling.)

### Opties (menu Opties, of argumenten bij het starten)
| Optie | Argument | Uitleg |
|---|---|---|
| **Kleurenblind** | `--kleurenblind` | een palet dat veilig is bij rood-groen-kleurenblindheid: **blauw = juist, oranje = fout**. Daarnaast **altijd** symbolen (✔ ✘, `+`/`!` in vakjes), zodat kleur nooit de enige aanwijzing is. Varianten voor deuteranopie/protanopie en voor tritanopie |
| Hoog contrast | `--contrast` | alleen zwart/wit + vet/omgekeerd, geen kleurvlakken |
| Geen kleur | `--geen-kleur` | voor oude terminals |
| ASCII | `--ascii` | geen Unicode (kaders, pixel-avatar → tekstgezichtje) |
| Muis | `--geen-muis` | klikken en scrollen aan/uit (uit = tekst selecteren werkt gewoon) |
| Avatar | – | aan/uit, mini of zijpaneel |
| Animaties | – | aan/uit (bv. het vereenvoudigen van de breukbalk, juichende avatar) |
| Accent-snelcodes | – | aan/uit (`e'` → é) |
| Standaard typrichting | – | ← of → in roosters |
| Taal van de menu's | – | nu Nederlands; de teksten staan apart, zodat een vertaling later kan |

- De opties worden **per kind** bewaard. Het argument bij het starten gaat voor (handig op een andere computer).
- Het kleurenpalet zit op **één plek** (`terminal/thema.py`). Alle schermen vragen "kleur voor *juist*" in plaats van "groen",
  zodat elk thema overal werkt. Ook de avatar-paletten hebben een kleurenblind-variant.

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

## O. Geparkeerd: het leerkrachtdeel

*Nog niet inplannen. Een idee om later uit te werken, na fase 23 (Examens), waarop het verder bouwt.*

Een leerkracht (of de sponsor-coach) ziet wat een ouder ziet, maar dan voor **een groep leerlingen**, en kan zelf
**opdrachten en toetsen** maken.

**Rollen**
- Er komt een rol **Leerkracht** naast Ouder, met een eigen wachtwoord (via `kern/wachtwoord.py`).
- De leerkracht ziet niets van de avatar, de winkel of de instellingen van het kind. Wel: de antwoorden, de rapporten
  en de denkfouten.

**Groepen**
- Een groep is een klas of een niveaugroep, met leerlingen (naam of schuilnaam) en hun leerjaar.
- Eén leerling kan in meer groepen zitten.

**Opdrachten maken**, in `kern/opdrachten.py` (data, geen curses). Een opdracht is een lijstje van:
- **onderwerpen uit de catalogus**: de leerkracht kiest de vaardigheid, het leerjaar of niveau, het aantal vragen,
  en eventueel een paar parameters van de leerlijn ("alleen tafel 7 en 8", "alleen oppervlakte");
- **eigen vragen**: een vraag, een antwoord en een uitleg. Bijvoorbeeld een woordpakket voor Frans of een vraagstuk
  van de klas.

Er zijn twee soorten:
- een **oefenopdracht**: met tip en uitleg, en met een deadline;
- een **toets** (de motor van fase 23): geen tip of uitleg tot het einde, één poging, optioneel met een tijdslimiet,
  en verse vragen per leerling, zodat afkijken niet helpt.

Een opdracht kan bewaard worden als sjabloon en volgend jaar opnieuw gebruikt.

**Uitwisselen zonder server**
- Alles blijft offline en zonder account in de cloud: kinderen zijn minderjarig (GDPR) en het programma gebruikt
  alleen de standaardbibliotheek.
- De leerkracht **exporteert een opdrachtpakket**, een bestand `.leeravontuur` (JSON). Dat gaat via Smartschool,
  e-mail of een USB-stick.
- Bij het kind: **"Opdracht van de juf/meester"** in het hoofdmenu. Het kind importeert het pakket en maakt de
  opdracht.
- Na afloop maakt het kind een **resultatenbestand** met een controlecode, zodat geknoei opvalt. Dat bestand gaat
  terug naar de leerkracht.
- Later kan er een **gedeelde map** bij (schoolnetwerk, OneDrive) die pakketten en resultaten vanzelf oppikt.
  Nog steeds zonder eigen server.

**Klasrapport** (`kern/rapporten.py` uitbreiden)
- Per opdracht: wie klaar is, de scores en de tijd.
- Per leerling: hetzelfde rapport als bij de ouder.
- **Per denkfout over de hele groep** ("8 van de 22 leerlingen rekenen met 100 in plaats van 60"). Daarmee weet de
  leerkracht wat ze morgen opnieuw uitlegt.
- Export als CSV of tekst, en afdrukbaar.

**Volgorde (later)**
1. Fase 23 (Examens) afwerken: de toetsmotor die ouder en leerkracht delen.
2. Het pakketformaat voor opdrachten en resultaten, met versies en tests.
3. Het leerkrachtdeel in de terminal (groepen, opdrachten maken, importeren, klasrapport).
4. Eigen vragen invoeren (met een controle op het formaat), en dan een gedeelde map.

**Open vragen voor later**
- Op welke computer werkt de leerkracht: een eigen installatie, of op de pc van de klas met meer leerlingen?
- Welke kanalen gebruikt de school (Smartschool)?
- Moeten de ouders toestemming geven, en mogen schuilnamen?

## Structuur
```
oefeningen.py                 starter: python3 oefeningen.py [--ouder] [--ascii]
requirements.txt              windows-curses (alleen Windows)
CLAUDE.md                     architectuurregels: kern zonder UI, GUI later, vak→domein→vaardigheid
leeravontuur/
  kern/
    leerjaren.py              leerjaar van het kind + schooljaarwissel; niveau = leerjaar + verschuiving
    leerlijnen.py             laadt en valideert de leerlijn-data per vaardigheid (bereiken per leerjaar)
    vaardigheden.py           register: vak → domein → vaardigheid (id, niveau, leerplanomschrijving)
    vraag.py                  Vraag: tekst, invoertype, vraagsleutel, juist, controle(), diagnose(), uitleg[], model
    diagnose.py               gedeelde denkfout-detectie (factor 10, eenheid, afronding …)
    modellen.py               data: Breukbalk, Getallenlijn, Rooster, Honderdveld, Figuur, Zinsblokken, Kofschip
    selectie.py               adaptieve keuze + "niet herhalen binnen 30 dagen" + verse examenvragen
    herhaling.py              herhaalbak (Leitner)
    sessie.py                 modi + tijdmeting + opslaan van antwoorden
    opslag.py                 SQLite, migraties, profielen, wachtwoord
    rapporten.py              overzichten per periode, export CSV/TXT
    avontuur.py               werelden, sterren, badges (data)
    punten.py                 verdienen (factoren, anti-farm), puntenlogboek
    avatar.py                 lagen samenstellen tot een pixelraster (data) + uitdrukkingen
    winkel.py                 catalogus, kopen, aankoop-challenge, levering ("pakje onderweg")
    klad.py                   parser voor kladregels (getallen, komma's, eenheden, breuken, %, =)
    afdrukken.py              HTML-bladen (dictee ouder/kind, oefenblad, rapport) → openen in de browser om af te drukken
    wiskunde/                 eenheden, getallen, hoofdrekenen, cijferen, breuken, procenten, meetkunde
    wiskunde/vraagstukken/    sjablonen per thema met stappen, foute paden en verwoordingen
    taal/                     werkwoorden.py (regelmotor), spelling.py, zinsontleding.py, woordenschat.py, lezen.py, dictee.py
    frans/                    woordenschat.py (met lidwoord/geslacht), vervoegen.py (regelmotor + onregelmatige ww),
                              zinnen.py (zinsbouw, vertalen), accenten.py (invoer + "bijna juist"), uitHetHoofd.py
  inhoud/                     JSON: werkwoorden, naamwoorden, zinnen, uitdrukkingen, leesteksten
  inhoud/leerlijnen/          JSON per vaardigheid: parameters per leerjaar (3 … m2) + code van het officiële doel
  inhoud/avatar/              JSON: palet, vormen + ankerpunten, onderdelen per laag (pixelpatronen), winkelcatalogus
  terminal/
    thema.py                  kleurenpaletten: standaard, kleurenblind (2 varianten), hoog contrast, geen kleur
    scherm.py                 put, kader, menu, broodkruimel, lezer, tekstvak, ASCII-terugval (uit de huidige App)
    klikzones.py              klikzones per scherm + verdeler muis → actie (dezelfde acties als de toetsen)
    rooster.py                invoer per vakje: Tab, typrichting r, komma ,, groen/rood (uit tabel_vraag)
    modellen.py               tekent de modellen en maakt ze interactief (breukbalk, getallenlijn, zinsontleder …)
    kladblad.py               vraagstuk-scherm
    avatar.py                 pixelraster tekenen met ▀ (256/8 kleuren, tekstterugval), mini-avatar, zijpaneel
    schermen/winkel.py        winkel, kast/paskamer, aankoop-challenge
    schermen/                 kind kiezen, hoofdmenu, leren, oefenen, snel, examen, ouder, rapporten, avontuurkaart
tests/                        unittest (stdlib)
.github/workflows/test.yml    ubuntu/macos/windows × Python 3.10 en 3.14
```

## Fasen (elk apart getest, gedemonstreerd en gepusht; na elke fase werkt alles)
Kleine fasen, zodat Imrane snel nieuwe dingen krijgt en jij tussendoor kunt bijsturen.

| # | Fase | Wat er daarna werkt |
|---|---|---|
| 1 | **Fundament** | kern/terminal-scheiding, `CLAUDE.md`, starter + requirements, leerlijnen + relatieve niveaus, startscherm met Solve It Now, ASCII-terugval, **muis/klikzones**, NepScherm, CI op 3 systemen; eenheden (lengte/massa) werken zoals nu |
| 2 | **Opslag + kindaccounts** | SQLite met migraties en UUID's; kind kiezen bij de start; elk antwoord met tijd, vraagsleutel en diagnosecode; vaardighedenregister; diagnoses voor eenheden |
| 3 | **Ouderdeel + rapporten** | wachtwoord (versioned hash), kinderen beheren, instellingen (timer zichtbaar, avatar aan/uit), rapporten per periode met kalender, export, alles wissen per kind |
| 4 | **Opties + thema's** | menu Opties en argumenten: kleurenblind (2 varianten), hoog contrast, geen kleur, ASCII, avatar, animaties, typrichting; alle schermen via `thema.py` |
| 5 | **Herhaling + slimme selectie** | fouten opnieuw, gelijkaardige vragen, herhaalbak (Leitner), "niet binnen 30 dagen", adaptieve keuze, status per vaardigheid in het rapport |
| 6 | **Punten + avatar (basis)** | puntenlogboek met anti-farm; pixel-avatar-motor (lagen, ankers, uitdrukkingen, ▀-weergave, terugval); standaardblokje; mini-avatar als oefenmaatje met reacties |
| 7 | **Winkel** | catalogus (±40 items om te starten), kopen, aankoop-challenge met "ben je zeker?", mini-lesje, pakje onderweg, kast/paskamer |
| 8 | **Hoofdrekenen + snelrekenen** | strategieën met uitleg, timer zichtbaar/verborgen, records + grafiekje |
| 9 | **Getallen + getallenlijn** | plaatswaarde, afronden, deelbaarheid, getallenlijn met zoom, negatieve getallen, thermometer, sprongen |
| 10 | **Cijferen** | +, −, × onder elkaar in het rooster met onthouden-rij; staartdeling stap voor stap |
| 11 | **Breuken** | breukbalk (noemer, arceren, vereenvoudigen, vergelijken, gelijknamig), breuk van een getal |
| 12 | **Procenten** | honderdveld, procentstrook, korting/btw |
| 13 | **Taal 1: werkwoordspelling** | werkwoordmachine (tt, vt met 't kofschip, vd, bijvoeglijk vd), d/t-flitsrondes, foutenjager |
| 14 | **Taal 2: spelling** | meervoud, verkleinwoord, lettergrepen, ei/ij-au/ou, tussen-s, trema/koppelteken/apostrof, snel-spellen |
| 15 | **Meer eenheden** | inhoud, oppervlakte (2 vakjes/kolom), dm³ ↔ l, tijd, geld, snelheid |
| 16a | **Vraagstukken met kladblad** (0.16.0) | 4 stappen met Gegeven/Gevraagd/Oplossing/Antwoord, kladparser, verhaalmachine (13 structuren × 16 werelden), foute paden automatisch, getrapte tips, tweede kans |
| 16b | **Vraagstukken 2** (0.17.0) | meer structuren en werelden (gemiddelde, tijdsduur, snelheid, tegels, schaal, lint), Speurneus (zoek de fout), Schatten & controleren |
| 17 | **Taal 3: zinsontleding** | zinsontleder (pv, onderwerp, gezegde, LV, MV, bijw. bep.), woordsoorten, proefjes |
| 18 | **Taal 4: woordenschat + lezen** | synoniemen, uitdrukkingen, spreekwoorden; leesteksten met vragen; eigen teksten van de ouder |
| 19 | **Dictee (afdrukken)** | afdrukbaar ouder- en kindblad, woordpakket van de week, overtypen + diagnose achteraf, flitsdictee |
| 20 | **Frans 1** | woordenschat FR↔NL met lidwoordkleuren, accentinvoer en "bijna juist"; eigen thema's invoeren; basispakketten; *être*/*avoir* in de vervoegingstabel |
| 21 | **Frans 2** | -er-werkwoorden en andere tijden per niveau, zinnen bouwen, vertalen, vraag-antwoord, uit het hoofd leren + luistermodus voor de ouder |
| 22 | **Meetkunde & rooster** | figuren met cm²-rooster, omtrek/oppervlakte, hoeken, coördinaten-schatzoeken, schaal |
| 23 | **Examens** | ouder stelt samen (ook als sjabloon), kind start zonder hulp, verse vragen, resultaten in het rapport |
| 24 | **Avontuur** | kaart, 7 werelden die rekenen, taal en Frans mengen, sterren, eindbazen, badges (+ zeldzame winkelitems) |
| 25 | **Afwerking** | README per systeem, handleiding voor ouders, prestatie op trage pc's, toegankelijkheid (kleurenblind-palet) |
| 26 | **Leerjaar 2de middelbaar + schooljaarwissel** | leerlijnen tot m2, letterrekenen, vergelijkingen, uitbreiding taal en Frans; de vraag bij de wissel op 1 september (klaar vóór september) |
| 27 | **Publicatie** | licentie (CC BY-NC-SA 4.0), `pipx`-pakket, kant-en-klare programma's via GitHub Actions, dekkingsrapport, inhoudspakketten met versies, "Over"-scherm |

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
