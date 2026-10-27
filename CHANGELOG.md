# Wat is er nieuw?

In gewone taal: wat er bij elke versie veranderde voor het kind en de ouder.

## 0.21.4 — plaatswaarden boven het rooster
- **Cijferen onder elkaar: druk `p` en de plaatswaarden staan boven de kolommen** (`E T H D TD HD M`, en `t h d`
  na de komma). De kolommen worden iets breder, de letter van de kolom waar je staat licht op, en ernaast staat
  bv. "◂ je staat bij de T (tientallen)". Nog eens `p` = weg. Het programma onthoudt je keuze; de ouder kan het ook
  aanzetten (Ouders › Kinderen › Weergave › Plaatswaarden bij cijferen). Bij optellen, aftrekken en
  vermenigvuldigen; bij vermenigvuldigen met een kommagetal niet (daar staan de getallen niet onder de komma).
- Spiekbrief Getallen: "TM = tienmiljoenen" erbij (dat zie je bij heel grote sommen).

## 0.21.3 — de spiekbrief erbij
- **Na de laatste tip opent `?` (of F1) de spiekbrief**, meteen bij het stukje over je oefening (bv. "Compenseren"
  bij plus en min, "Later en vroeger" bij de klok). De laatste tip zegt het al: "Nog hulp nodig? Druk nog eens ?/F1:
  je spiekbrief.", en onderaan staat dan `[?/F1] spiekbrief`. **Esc brengt je terug naar dezelfde vraag**, met alles
  wat je al typte. Daarna begint `?` weer bij tip 1. Zo ook bij cijferen (nog eens `?` op hetzelfde vakje), bij
  vraagstukken (na de 4 tips), de Speurneus, schatten en Maten.
- **Het menu Spiekbrieven is korter:** geen "Welk vak?" meer (er is nu één vak), meteen de domeinen met wat erin
  staat. Heeft een domein maar één spiekbrief, dan opent die meteen.

## 0.21.2 — Esc vraagt eerst
- **Esc midden in een vraag stopt niet meer meteen.** Er komt eerst een kader "Wil je stoppen met deze vraag?" met
  [Ja, stoppen] en [Nee, verder]; **Nee staat gekozen**. Enter (of nog eens Esc) = gewoon verder, met alles wat je al
  typte en je klad. Echt stoppen: ← en Enter (of klik op "Ja, stoppen"). Na het nakijken stopt Esc meteen, zoals
  vroeger. Zo ook bij Maten (vrij en de tabel), vraagstukken en snelrekenen; bij 60 seconden en 20 sommen staat de
  klok stil zolang het kader openstaat. De tijd in het kader telt ook niet mee voor de vraag.

## 0.21.1 — je klad blijft staan
- **Na het nakijken blijft je klad staan** in een kader "Jouw klad" rechtsonder, naast "Zo kan het:" (je laatste
  3 regels, met hun nummer). Elke regel krijgt ✔ of ✘, en een **!** op de regel waar je redenering afweek, ook als
  de som zelf klopt. Zie je dezelfde fout als in je antwoord, dan zegt de uitleg kort "Dat zie je in je klad,
  regel 2 (!)." Staat de wijzerklok in de terminal, dan komt het kader onder de uitleg (of niet, als er geen plaats
  is).
- Hoofdrekenen, compenseren: het klad herkent nu ook "omgekeerd gecompenseerd" (bv. 147 + 1 in plaats van 147 − 1).

## 0.21.0 — een digitaal klokje
- **Een tijdstip typ je nu op een digitaal klokje** met grote cijfers: bij de 24-urennotatie, "Hoe laat is het
  … later?", "kwart over tien in cijfers", "Hoe laat kom je aan?" … Je typt zoals altijd (`16.10`, `16:10` of
  `1610`); de cijfers verschijnen meteen, de `:` komt vanzelf en Backspace wist het laatste cijfer. Een letter
  komt er niet in. Staat de wijzerklok in de terminal (zonder klokvenster), dan is het klokje kleiner en staat het
  ernaast.
- In een vraagstuk met een tijdstip staat je antwoord in het vakje ook als `14:55` (de `:` komt vanzelf).

## 0.20.4 — starten met een dubbelklik
- De starter heet nu **leeravontuur.py** (`py leeravontuur.py` of `python3 leeravontuur.py`). De oude naam
  `oefeningen.py` werkt nog altijd: hij start gewoon `leeravontuur.py`.
- **Dubbelklikken om te starten:** `leeravontuur-win.bat` (Windows), `leeravontuur-mac.command` (macOS) en
  `leeravontuur-linux.sh` (Linux). Op Windows blijft het venster open als er iets misloopt (bv. Python ontbreekt),
  zodat je de melding kan lezen.

## 0.20.3 — "Hoe moeilijk?" bij onderwerpen van een hoger leerjaar
- Snelheid, Schaal en Korting en btw bestaan pas vanaf het 6de leerjaar (Procenten vanaf het 5de). Voor een kind
  van een lager leerjaar deed Makkelijk of Normaal daar niets: de keuze sprong terug naar Normaal. Nu staat de
  keuze meteen op het eerste niveau dat wel kan (Enter werkt dus meteen), en bij een niveau dat nog niet kan
  staat "(pas vanaf het 6de leerjaar)"; kies je het toch, dan zegt het programma waarom en welk niveau wel kan.

## 0.20.2 — kleine verbeteringen uit de tests
- **Tips draaien rond:** `?` geeft telkens de volgende tip ("Tip 1 van 3", "Tip 2 van 3" …) en na de laatste
  opnieuw de eerste. Vroeger bleef het hangen op "schrijf je eerste stap in het klad". `?` werkt nu ook midden in
  een klad-regel.
- **F1 geeft ook een tip.** Op een AZERTY-klavier is `?` Shift + komma; F1 is één toets. De knop heet `[?/F1]`.
- **Cijferen, onthouden:** een cijfer in de onthouden-rij blijft in zijn kolom staan. Met ↓ ga je terug naar de rij
  waarin je typte, recht eronder. Vroeger schoof de cursor een vakje naar links.
- **De klok:** "Hoe laat is het in 24 uur?" was verwarrend (over 24 uur is het hetzelfde uur). Nu: "Het is tien
  over vier 's middags. Schrijf dat zoals op een digitale klok (24-urennotatie)."
- **Het klad:** een regel die je typt zonder Enter, verdwijnt niet meer als je met Tab naar je antwoord gaat (of
  in een vraagstuk naar een andere stap). Hij wordt nagekeken zoals met Enter.
- **Kleinigheden:** in het hoofdmenu loopt de uitleg niet meer onder de avatar door; in de moestuin is het zomer
  (er werden tomaten geoogst in juli en augustus, terwijl het "lente" was). Op de getallenlijn heten de knoppen
  "zoom in" en "zoom uit".

## 0.20.1 — het numeriek klavier
- De toetsen **/ * - +** en de kleine **Enter** van het numeriek klavier werken nu overal: in de menu's, in het
  antwoord en in het klad. Op Windows deden ze niets; op Linux kwamen / * - + niet aan in sommige terminals.

## 0.20.0 — nieuwe menu's
- **Alles zit nu op één manier in de menu's:** Wiskunde › een domein › een onderwerp. Zo is er straks plaats
  voor Taal en Frans. Wiskunde heeft 8 domeinen: Getallen, Hoofdrekenen, Cijferen, Breuken en procenten, Meten,
  Tijd, geld en snelheid, Meetkunde en Vraagstukken.
- **Bij elk onderwerp kies je met één toets wat je wil doen:** Enter = een reeks van 10, **V** = vrij oefenen,
  **S** = spiekbrief, en waar het kan **T** = 60 seconden, **Z** = 20 sommen en **H** = tabel-oefening. Een kleine
  letter werkt ook. Onderaan staan alleen de toetsen van het onderwerp waar je op staat, en je kunt erop klikken.
  Na een oefening sta je terug op hetzelfde onderwerp.
- **Snelrekenen zit nu in Hoofdrekenen:** bij Tafels en bij Optellen en aftrekken met T (60 seconden) of Z
  (20 sommen), en het nieuwe onderwerp **Gemengd**. De records van vroeger blijven. Staat de timer uit, dan is er
  geen T en start Enter bij Gemengd 20 sommen.
- **Meten:** eerst kies je de maat (Lengte, Massa, Inhoud, Oppervlakte, Volume, Maten gemengd, Maten zelf kiezen),
  dan de toets. Oppervlakte en omtrek en Formules staan nu ook bij Meten, met hun eigen spiekbrief
  **Oppervlakte en formules**. De spiekbrief Meetkunde gaat nu over hoeken, de schatkaart en schaal.
- **Het hoofdmenu is korter:** ▶ Verder, Herhalen, Wiskunde, Spiekbrieven, Mijn avatar, Zeg het ons, Wissel van
  kind, Stoppen. "Leren & oefenen", "Snelrekenen" en "Opties" zijn weg.
- **Opties is verhuisd:** de kleuren kiest het kind in **Mijn avatar › Schermkleuren** (toets L). Eenvoudige
  tekens, muis, typrichting, avatar, animaties en het klokvenster zet de ouder per kind in
  **Ouders › Kinderen › Weergave**.
- **Rapport voor de ouder:** per vak en domein, met de namen uit het menu (de maten samen onder "Maten").
  Snelrekenen staat apart onder zijn onderwerp ("Tafels, snelrekenen: … sommen"), ook in de status: een snelle
  ronde verandert de gewone status niet meer. De CSV-export heeft achteraan twee kolommen erbij: vak en domein.
- ▶ Verder en Herhalen werken zoals vroeger, ook met wat je in een vorige versie oefende.
- De handleiding toont nog de menu's van 0.19. Ze wordt later in één keer herschreven.

## 0.19.0 — één vaste werkwijze, met klad
- **Elke oefening werkt nu op dezelfde manier**, zodat je het maar één keer moet leren:
  1. lees de vraag;
  2. reken in het **klad** (`Tab`): typ rekenregels zoals op papier, bv. `70 : 7 = 10`; elke regel krijgt meteen ✔
     of ✘, met een hint die het antwoord niet verklapt;
  3. typ je antwoord en Enter.
- **`?` geeft telkens een volgende tip:** eerst de aanpak, dan het begin van het klad, dan hulp bij de regel in je
  klad die niet klopt. Nooit het antwoord.
- **Fout? Een tweede kans**, met een hulpje als het programma de denkfout herkent, en de vraag om klad te maken.
  Pas juist na een tweede kans = de helft van de punten, en de vraag komt in de herhaalbak. (Niet bij ja/nee en
  <, >, =.)
- Na het nakijken staat **"Zo kan het:"**: de oplossing in klad-regels, zoals je ze zelf kunt typen.
- Klad bij alle rekenoefeningen: hoofdrekenen, procenten, breuk van een getal, breuken optellen, tijd, geld,
  snelheid, rekenen met de klok, formules en schaal. Een tip kost 2 punten, een juist klad geeft er 2 bij.
- Nieuw onderwerp **Slim × en : (splitsen)** (Hoofdrekenen → 5): `91 : 7 = 70 : 7 + 21 : 7 = 10 + 3 = 13`,
  `14 × 7 = 10 × 7 + 4 × 7`, en compenseren: `99 × 6 = 100 × 6 − 6`. Hier is het klad verplicht: het gaat om de
  aanpak. Elke juiste splitsing telt.
- Het klad leest een breuk zonder spaties als één getal: `3/4 : 2/5` klopt nu.
- Het klokvenster komt op de monitor waar je werkt (met meer schermen).
- Opgelost: een klik op "Wie ben jij?" bovenaan, terwijl je je naam typte, gaf een foutmelding.

## 0.18.0 — de klok
- Nieuw onderwerp **De klok** (Tijd, geld en snelheid → 4), met een echte **wijzerklok in een eigen venster**
  (alle cijfers, de minuten klein erbuiten, een korte blauwe uurwijzer en een lange oranje minutenwijzer):
  - lees de klok (typ `3.25`, in de terminal of in het klokvenster) of **zet de wijzers** zelf: klik of sleep de
    lange wijzer in het klokvenster, of gebruik de pijltjes, `+` en `−` voor een uur; de uurwijzer draait mee, zoals
    bij een echte klok. Was het fout, dan tonen groene wijzers hoe het moest;
  - het klokvenster zit nooit in de weg: het blijft bovenop zolang er een klok in beeld is (en verdwijnt daarna),
    komt naast de terminal of rechtsboven (hoogstens een kwart van het scherm), neemt de toetsen niet over, en
    onthoudt waar je het naartoe sleept. De terminal houdt zijn tekst dan links;
  - zie je het venster niet (een terminal op volledig scherm)? `F2` zet de klok in de terminal. Kan er geen venster
    (Linux zonder `python3-tk`, via ssh), dan tekent de terminal de klok ook; of met Opties → Klok in een eigen
    venster → uit, of `--zonder-klokvenster`;
  - tijden **in woorden**, zoals we ze in Vlaanderen zeggen: "kwart over drie", "vijf voor half vier",
    "tien over half vier". Half vier is 3.30!;
  - de **24 uur** (3.15 's middags = 15.15 u) en **later of vroeger** ("Hoe laat is het 35 minuten later?"), in het
    6de ook over middernacht heen;
  - het programma herkent o.a. "uurwijzer en minutenwijzer verwisseld", "half vier gelezen als 4.30" en
    "gerekend alsof een uur 100 minuten heeft".
- **Tijd in de vraagstukken** (vanaf het 4de): hoe lang duurt de film, hoe laat komt de trein aan, hoe laat moet je
  vertrekken? In het 6de ook een rit in twee stukken. 2 nieuwe werelden: de bioscoop en de trein (nu 22).
- Het **klad** kent nu kloktijden: `9.45 u + 35 min = 10.20 u` klopt, en wie met 100 minuten rekent, hoort dat
  een uur 60 minuten heeft.
- De spiekbrief van Tijd, geld en snelheid heeft nu ook een stuk over de klok.
- Winkel: een wekker.

## 0.17.0 — vraagstukken 2: Speurneus en schatten
- **Speurneus** (Vraagstukken → 2): een ander kind loste een vraagstuk op. Zit er een fout in? Kies de regel waar het
  misloopt (of "Alles is juist!") en dan waarom: een rekenfout, de verkeerde bewerking, gestopt na een tussenstap,
  niet omgezet, een overbodig gegeven gebruikt …
- **Schatten en controleren** (Vraagstukken → 3): "ongeveer hoeveel?" (300, 3000 of 30?) en "kan dat kloppen?"
  bij het antwoord van een ander kind. Zonder uit te rekenen.
- **Meer soorten vraagstukken:** gemiddelde, snelheid (km per uur, ook met minuten), tegels (oppervlakte), schaal
  op een kaart, lint in stukken knippen (m en cm) en de regel van drie (6 kosten € 7,20, wat kosten er 10?).
  Het programma herkent o.a. "met de omtrek gerekend in plaats van de oppervlakte" en "gedeeld door het verkeerde
  aantal".
- 4 nieuwe werelden: het pretpark, het zwembad, de kust en de knutselklas (nu 20).
- In het klad mag je een groot getal ook met een spatie schrijven: `300 000`.
- Winkel: een vergrootglas.

## 0.16.0 — vraagstukken
- Nieuw domein **Vraagstukken**: verhaaltjes oplossen in **4 stappen**, met het schema Gegeven · Gevraagd ·
  Oplossing · Antwoord erin:
  1. **Lees:** duid de getallen aan die je nodig hebt (pijltjes en spatie, of klik) en kies wat er gevraagd wordt.
  2. **Plan:** welke bewerking eerst, welke daarna? (mag je overslaan)
  3. **Reken** in je **klad**: typ rekenregels zoals `0,75 x 3,20 = 2,40` of `750 g = 0,75 kg`. Je typt `x` voor
     maal en `:` voor delen. Elke regel krijgt meteen ✔ of ✘, met een hint die het antwoord niet verklapt.
  4. **Controle:** vul de antwoordzin in; het programma kijkt ook of je antwoord kan kloppen.
- **Meteen antwoorden mag.** Juist? Extra punten. Fout? Eén tweede kans, met een hulpje als de denkfout te
  herkennen is (bv. "dat is de prijs van alle bloemkolen, maar gevraagd is het wisselgeld") en de vraag om klad
  te maken.
- **Tips met `?`**, telkens een beetje meer: eerst lichten de belangrijke woorden en getallen op, dan wat er
  gevraagd wordt, dan welke bewerkingen, en dan hulp bij de regel waar het misloopt. Nooit het antwoord zelf.
  Een tip kost wat punten, zonder tip zijn er extra punten. Een juist klad geeft ook extra punten.
- Een **verhaalmachine** mengt rekenstructuren (samen, verschil, groepjes, delen met rest, wisselgeld, prijs per kg,
  korting, sparen, recept, breuk van, omtrek …) met 16 werelden (bakkerij, bouwwerf, boerderij, dierentuin …):
  zo zijn er duizenden verschillende verhalen, soms met een **overbodig gegeven** of een **omgekeerde vraag**.
  Herhalen = hetzelfde soort vraagstuk in een andere wereld.
- De denkfouten (een andere bewerking, gestopt na een tussenstap, een stap vergeten, niet omgezet, een overbodig
  gegeven gebruikt, de komma …) komen automatisch uit de oplossing, en worden ook in het klad herkend.
- **Rapport:** per vraagstuk het aantal tips, hoeveel er meteen juist waren en hoeveel met (een juist) klad.
- Winkel: een kladblok.

## 0.15.0 — meetkunde
- Nieuw domein **Meetkunde**:
  - **Oppervlakte en omtrek** op een rooster met echt vierkante vakjes van 1 cm²: tel de vakjes en de randjes. Na
    het nakijken is de omtrek aangeduid. Ook L-vormen, trappen en driehoeken met halve vakjes.
  - **Formules**: rechthoek, vierkant, driehoek, parallellogram, trapezium, cirkel (π = 3,14) en het volume van
    een balk en een kubus. De uitleg vult de formule in met de getallen.
  - **Hoeken**: scherp, recht, stomp, gestrekt of vol bij een tekening of een aantal graden; vanaf het 6de de
    derde hoek van een driehoek, in het 1ste middelbaar nevenhoeken.
  - **Schatkaart**: waar ligt de schat (typ bv. `C4`), of zet zelf een kruisje met de pijltjes of een klik.
    In het 1ste middelbaar een assenstelsel met negatieve getallen.
  - **Schaal** (vanaf het 6de): van de kaart naar het echt en terug; in het 1ste middelbaar ook de schaal zoeken.
- Het programma herkent o.a.: omtrek en oppervlakte verwisseld, de randjes binnenin meegeteld, vergeten te delen
  door 2, straal en diameter verwisseld, kolom en rij omgewisseld, cm niet omgezet naar m.
- Winkel: een potlood achter het oor.
- Een volledige **handleiding** met schermafdrukken: [docs/handleiding](docs/handleiding/README.md). Elk onderdeel,
  elke optie, wat er per leerjaar aan bod komt, welke denkfouten het programma herkent, en alle startargumenten.

## 0.14.0 — meer eenheden
- **Eenheden:** naast lengte en massa nu ook **inhoud** (hl … ml), **oppervlakte** (km² … mm², met ha, a en ca;
  vanaf het 5de leerjaar) en **volume** (m³, dm³, cm³, samen met de liter; vanaf het 6de).
- De eenhedentabel heeft bij oppervlakte 2 vakjes en bij volume 3 vakjes per eenheid. Wie per eenheid maar
  1 plaats opschuift, krijgt daar uitleg over.
- Nieuwe keuze **Door elkaar**: alle soorten eenheden die bij je leerjaar horen.
- Nieuw domein **Tijd, geld en snelheid**:
  - tijd: uren, minuten en seconden omrekenen, "135 min = 2 u 15 min" (je typt `2 u 15 min`), tijdsduur en
    hoe laat je aankomt (je typt `11.15` of `11:15`). Wie met 100 rekent in plaats van 60, krijgt uitleg.
  - geld: euro en cent, wisselgeld en wat je samen betaalt;
  - snelheid (vanaf het 6de): afstand, tijd en snelheid; km/u ↔ m/s in het 1ste middelbaar.
- Winkel: een zakhorloge.

## 0.13.0 — eerste bèta (oktober 2026)
- Alles hieronder komt nu samen in de gewone versie (`main`). Dit is de eerste versie om dagelijks te gebruiken.
- **Zeg het ons** in het hoofdmenu: het kind (of de ouder) schrijft wat leuk, moeilijk of kapot is. Het blijft op
  de computer; de ouder leest het in het ouderdeel bij **Opmerkingen**.
- In het hoofdmenu kies je de 10de keuze (Stoppen) met de toets 0.
- Een testlijst voor de ouder: `docs/testlijst.md`.

## 0.12.1 — stabiliteit
- Pijltjes en een venster dat groter of kleiner wordt, typen geen rare tekens meer in een antwoord of wachtwoord.
- Herhalen crasht niet meer na oefenen op een moeilijker niveau; ook "× en : met 10" in een tweede reeks niet.
- Gaat er toch iets mis: een vriendelijke melding, terug naar het menu, en de fout in `fouten.log`.
- Elke dag een reservekopie; een beschadigde databank wordt vanzelf hersteld.
- Een waarschuwing als het programma al openstaat.

## 0.12 — procenten
- Honderdveld (aflezen en kleuren), procent ↔ breuk ↔ kommagetal, procent van een getal met de procentstrook.
- Korting en btw (6de leerjaar), stijging en daling (1ste middelbaar). Winkel: stropdas.

## 0.11 — breuken
- De breukbalk: noemer kiezen, arceren, vereenvoudigen. Herkennen, gelijkwaardig, vergelijken, optellen en
  aftrekken, breuk van een getal, × en :, breuk ↔ kommagetal. Winkel: koksmuts.

## 0.10 — cijferen
- Optellen, aftrekken en vermenigvuldigen onder elkaar met een onthouden-rij en hulp per vakje.
- De staartdeling stap voor stap. Het scrollwiel zoomt op de getallenlijn. Winkel: rekenbril.

## 0.9 — getallen
- Plaatswaarde, afronden, deelbaarheid (ggd, kgv, priem vanaf het 6de) en de getallenlijn met inzoomen,
  sprongen en een thermometer met negatieve getallen.

## 0.8 — hoofdrekenen
- Tafels, plus en min, × en : met 10/100/1000, dubbel en helft, telkens met een slimme strategie.
- Snelrekenen: 60 seconden of 20 sommen, met records.

## 0.7 — winkel
- Avatar-items kopen met een rekenvraag, "Ben je zeker?", een mini-lesje en een pakje dat later komt.

## 0.6 — punten en avatar
- Punten voor juiste antwoorden, een pixel-avatar die meekijkt en reageert.

## 0.5 — herhalen
- Fouten komen terug na 1, 3 en 7 dagen; vragen van de laatste 30 dagen worden vermeden.

## 0.4 — opties
- Kleurenblind (2 soorten), hoog contrast, geen kleur, ASCII, muis aan of uit, typrichting.

## 0.3 — ouderdeel
- Wachtwoord, rapporten per dag/week/maand met kalender, export, kinderen beheren.

## 0.2 — kinderen en opslag
- Meerdere kinderen, elk antwoord wordt bewaard (met datum en tijd).

## 0.1 — het fundament
- Het nieuwe programma "Leeravontuur" met eenheden omzetten, de tabel-oefening, menu's en de muis.
