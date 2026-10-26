# Brainstorm: het deel voor coaches en leerkrachten

*Nog niet ingepland. Een idee om uit te werken met de sponsor (een coach), na fase 23 (Examens) voor het deel met
toetsen. Niets hiervan zit al in het programma.*

## Waarom en voor wie
Een ouder ziet nu wat één kind doet. Een coach of leerkracht wil hetzelfde, maar voor **meer kinderen**, en wil
**zelf sturen**: wat het kind oefent, op welk niveau, en met eigen opdrachten en toetsen.

Er zijn twee soorten gebruikers, met andere noden:

| | Coach | Klasleerkracht |
|---|---|---|
| Hoeveel kinderen | enkele (bijles, zorg, huiswerkbegeleiding) | 20 of meer |
| Hoe | vaak 1-op-1, soms naast het kind | de hele klas tegelijk, of in niveaugroepen |
| Wil vooral | zien *hoe* het kind denkt, gericht bijsturen | zien wat de klas nog niet kan, opdrachten en toetsen |
| Computer | eigen laptop, het kind werkt thuis | pc's of laptops van de school |

**Voorstel: eerst de coach.** Dat past bij de sponsor, het vraagt geen klasinfrastructuur, en alles wat de coach
nodig heeft (deelpakket, focusplan, eigen inhoud) gebruikt de klasleerkracht later ook.

## Wat er al is (en waarop het bouwt)
- Elk antwoord wordt bewaard met de vraag, het antwoord, juist/fout, de **denkfout**, de tijd, de tips, het eerste
  (foute) antwoord en het **klad** (de regels die het kind typte). Een coach kan dus later de denkweg terugzien
  zonder dat de databank verandert.
- Het ouderdeel heeft rapporten per vak, domein en onderwerp, de denkfouten, een kalender, en export naar CSV en
  JSON (alle gegevens).
- Instellingen per kind: leerjaar, niveau, timer zichtbaar, weergave.
- Fase 23 (Examens) bouwt de toetsmotor: geen hulp, één poging, verse vragen. Die gebruikt de coach ook.

## Uitgangspunten
1. **Privacy eerst.** Kinderen zijn minderjarig (GDPR). Alles blijft offline, zonder account of server. Gegevens
   reizen alleen als bestand dat iemand bewust verstuurt.
2. **De ouder blijft eigenaar.** De coach krijgt nooit vanzelf toegang. De ouder kiest wat gedeeld wordt, en keurt
   goed wat de coach terugstuurt.
3. **Geen vergelijken tussen kinderen voor het kind.** Een kind ziet nooit een ranglijst of de score van een ander.
4. **Alleen de standaardbibliotheek**, zoals de rest van het programma.
5. **Het kind merkt weinig.** Geen nieuwe menu's voor het kind; wat de coach wil, komt via ▶ Verder (het
   hoofdmenu heeft nog maar plaats voor een paar items, zie de cijfertoetsen).

## Ideeën

### 1. Deelpakket: van de ouder naar de coach
- In het ouderdeel: **"Delen met de coach"**. De ouder kiest de periode, de vakken, en of de naam erin staat
  (anders een schuilnaam).
- Het programma maakt één bestand (`.leeravontuur`, JSON, met een versie en een controlecode). Dat gaat via
  e-mail, Smartschool of een USB-stick.
- Daarin: het rapport, de antwoorden met denkfouten en klad, de instellingen die ertoe doen (leerjaar, niveau).
  Geen avatar, winkel, punten of wachtwoorden.

### 2. Coachmodus
- Starten met `--coach` (eigen wachtwoord, via `kern/wachtwoord.py`). Een eigen databank, los van die van de kinderen.
- **Leerlingen** komen binnen door een deelpakket te openen. Een nieuw pakket van hetzelfde kind werkt het bij.
- Per leerling hetzelfde rapport als bij de ouder.
- **Over de leerlingen heen:** welke denkfouten komen bij wie voor ("3 van de 5 tellen met 100 minuten in een
  uur"), en welke onderwerpen niemand nog geoefend heeft.

### 3. Focusplan: van de coach terug naar het kind
De coach maakt een klein bestand voor één kind, met:
- **focusonderwerpen** voor de komende week (die komen eerst in ▶ Verder, vóór de vorige oefening);
- het **niveau** per onderwerp;
- onderwerpen die **nog niet in de klas gezien** zijn (die verbergen, zodat het kind niet vooruitloopt);
- timer aan of uit;
- een **briefje voor het kind** ("Goed bezig met de staartdeling! Deze week: breuken vergelijken."), dat in het
  hoofdmenu verschijnt.

De ouder opent het bestand in het ouderdeel, ziet wat erin staat en **keurt het goed** (of niet). Een focusplan
heeft een einddatum; daarna valt alles terug op de gewone instellingen.

### 4. Samen-modus (de coach zit naast het kind)
- Een sessie van ±20 minuten in vaste stukken: een opwarmer (snelrekenen), het focusonderwerp, herhaling.
- **Klad terugzien:** na de sessie (of later) kan de coach bij elke vraag het klad stap voor stap zien, met de
  eerste foute poging en de gebruikte tips. Zo ziet de coach de denkweg, niet alleen het antwoord.
- Een korte notitie van de coach bij de sessie (komt in het rapport voor de ouder).

### 5. Diagnose voor de coach
- **Intaketoets:** per domein een korte screening op het leerjaar van het kind (verse vragen, geen hulp). Het
  resultaat is een kaart: wat zit goed, waar zitten denkfouten.
- **Denkfouten door de tijd:** verdwijnt een fout echt, of komt ze terug na twee weken?
- **Afdrukbaar verslag** voor de ouders en de school (in gewone taal, met voorbeelden uit het klad).

### 6. Eigen inhoud
- **Eigen vragen:** vraag, antwoord, uitleg (met een controle op het formaat).
- **Woordpakketten** voor Taal en Frans (dictee, woordenschat).
- **Vraagstukken in een eigen wereld:** de coach geeft woorden en voorwerpen uit de leefwereld van het kind
  (voetbal, paarden), de verhaalmachine maakt er vraagstukken mee. De rekenstructuur en de nakijk blijven dezelfde.
- Een **eigen spiekbrief** bij een onderwerp.
- Eigen inhoud gaat mee in het focusplan of in een opdracht.

### 7. Opdrachten en toetsen
Een opdracht is een lijstje van onderwerpen (met leerjaar of niveau, aantal vragen, en eventueel een paar
parameters, bv. "alleen tafel 7 en 8") en eigen vragen. Twee soorten:
- een **oefenopdracht**: met tips en uitleg, en met een deadline;
- een **toets** (de motor van fase 23): geen tip of uitleg tot het einde, één poging, optioneel een tijdslimiet, en
  verse vragen per kind, zodat afkijken niet helpt.

Het kind ziet een opdracht via ▶ Verder. Na afloop maakt het programma een **resultatenbestand** met een
controlecode (zo valt geknoei op). Een opdracht kan bewaard worden als sjabloon en volgend jaar opnieuw gebruikt.

### 8. Klasschaal (later)
- **Groepen:** een klas of een niveaugroep; een kind kan in meer groepen zitten.
- **Klasrapport:** per opdracht wie klaar is, de scores en de tijd; per denkfout over de groep ("8 van de 22").
  Zo weet de leerkracht wat morgen opnieuw uitgelegd moet worden. Export als CSV of tekst, en afdrukbaar.
- **Gedeelde map** (schoolnetwerk, OneDrive) die pakketten en resultaten vanzelf oppikt. Nog steeds zonder eigen
  server.

## Volgorde (voorstel)
| Stap | Wat | Nodig voor |
|---|---|---|
| C1 | Pakketformaat (JSON, versie, controlecode) + deelpakket in het ouderdeel | alles hierna |
| C2 | Coachmodus: leerlingen uit pakketten, rapporten, denkfouten over de leerlingen heen | C3–C8 |
| C3 | Focusplan terug naar het kind, goedkeuren door de ouder, briefje in het hoofdmenu | |
| C4 | Klad terugzien + samen-modus + notitie | |
| C5 | Intaketoets en afdrukbaar verslag | fase 23 |
| C6 | Opdrachten en toetsen met resultatenbestand | fase 23 |
| C7 | Eigen inhoud (vragen, woordpakketten, eigen wereld, spiekbrief) | |
| C8 | Klasschaal: groepen, klasrapport, gedeelde map | |

C1 tot C4 kunnen vóór fase 23. Elke stap is een eigen branch en versie, zoals de andere fasen.

## Vragen voor de sponsor
1. Hoe werk je nu: 1-op-1, in groepjes? Waar: bij jou, bij het kind thuis, op school?
2. Zit je naast het kind als het oefent, of oefent het kind thuis en bespreek je het achteraf?
3. Welke verslagen schrijf je, en voor wie (ouders, school, CLB)? Wat staat erin?
4. Welk leerplan volgen je leerlingen (de netten verschillen)? Wil je de onderwerpen daaraan kunnen koppelen?
5. Wat mis je in de programma's die je nu gebruikt? Wat ergert je eraan?
6. Wat mag het programma nooit doen (punten, vergelijken, tijdsdruk …)?
7. Hoe wissel je nu bestanden uit met ouders en scholen (e-mail, Smartschool)? Wat mag volgens de school?
8. Hoeveel kinderen tegelijk, en hoe lang volg je een kind?

## Open punten
- **Toestemming:** volstaat het dat de ouder het pakket zelf verstuurt, of is een uitdrukkelijke toestemming nodig
  (bv. een vinkje met uitleg in het ouderdeel)?
- **Eén computer voor meer kinderen** (klas-pc): dan zitten meer kinderen in één databank, met elk een pincode. Kan
  al, maar de coach- of leerkrachtmodus moet er dan los van blijven.
- **Handleiding:** het deel voor coaches en leerkrachten komt in het handleidingproject, samen met dat voor kinderen
  en ouders.
