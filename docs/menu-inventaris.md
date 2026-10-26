# Menu-inventaris (stap A: de menu's verhuizen)

Alles wat er in versie 0.19.0 in de menu's zit, met de plek waar het na stap A komt. Bij de acceptatie wordt elke
regel afgevinkt: zo valt er niets weg. Stap A verplaatst alleen; oefeningen, punten, niveaus, Verder, Herhalen en de
bewaarde gegevens werken zoals nu.

Toetsen in de nieuwe onderwerpenlijst: **Enter** reeks van 10 · **V** vrij oefenen · **S** spiekbrief ·
**T** 60 seconden · **Z** 20 sommen · **H** tabel-oefening. Na de toets komt, zoals nu, de keuze "Hoe moeilijk?"
(waar die er nu is).

## Wie ben jij? (blijft)
- [x] een kind kiezen → Hoofdmenu
- [x] + Nieuw kind (naam, leerjaar)
- [x] pincode bij het starten (als die aan staat)
- [x] Ouders (wachtwoord); startargument `--ouder` gaat er rechtstreeks heen

## Ouders
- [x] Rapporten: kind → periode (of zelf kiezen) → rapport; E exporteren, K kalender (← → maanden).
      Wordt gegroepeerd per Vak › Domein › Onderwerp; de maten samen onder "Maten".
- [x] Kinderen › kind › Naam
- [x] Kinderen › kind › Leerjaar
- [x] Kinderen › kind › Timer zichtbaar voor het kind
- [x] Kinderen › kind › Pincode bij het starten (nieuw / weghalen)
- [x] Kinderen › kind › Winkel: 2x een foute som
- [x] Kinderen › kind › Gegevens exporteren
- [x] Kinderen › kind › Alles van dit kind wissen
- [x] Punten: logboek, B bonus geven
- [x] Wachtwoord wijzigen
- [x] Opmerkingen
- [x] Sluiten; vergrendelen na 10 minuten zonder toets

## Hoofdmenu
- [x] ▶ Verder → ▶ Verder (1ste)
- [x] Leren & oefenen › Welk vak? › Wiskunde → Wiskunde (rechtstreeks, als vak)
- [x] Snelrekenen → in Hoofdrekenen (zie onder)
- [x] Herhalen (n) → Herhalen (n) (2de)
- [x] Mijn avatar → Mijn avatar
- [x] Spiekbrieven → Spiekbrieven (uit de registry)
- [x] Opties → weg: alles verhuist (zie onder)
- [x] Wissel van kind → Wissel van kind
- [x] Zeg het ons → Zeg het ons
- [x] Stoppen → Stoppen

Wiskunde krijgt 8 domeinen: Getallen · Hoofdrekenen · Cijferen · Breuken en procenten · Meten ·
Tijd, geld en snelheid · Meetkunde · Vraagstukken (elk hoogstens 10 onderwerpen: de cijfertoetsen 1–9 en 0).

Nieuwe volgorde van het hoofdmenu: Verder · Herhalen · Wiskunde · Spiekbrieven · Mijn avatar · Zeg het ons · Wissel van kind · Stoppen.

## Wiskunde: de onderwerpen
Nu: domein → onderwerp → Vrij oefenen / Reeks van 10 / Spiekbrief → Hoe moeilijk?
Na: Wiskunde → domein → onderwerp + toets → Hoe moeilijk?

### Getallen
- [x] Plaatswaarde → Getallen › Plaatswaarde (Enter V S)
- [x] Afronden → Getallen › Afronden (Enter V S)
- [x] Deelbaarheid → Getallen › Deelbaarheid (Enter V S)
- [x] Getallenlijn → Getallen › Getallenlijn (Enter V S)

### Hoofdrekenen
- [x] Maal- en deeltafels + Snelrekenen › Tafels → Hoofdrekenen › Tafels (Enter V S T Z)
- [x] Optellen en aftrekken + Snelrekenen › Plus en min → Hoofdrekenen › Optellen en aftrekken (Enter V S T Z)
- [x] × en : met 10, 100, 1000 → Hoofdrekenen (Enter V S)
- [x] Verdubbelen en halveren → Hoofdrekenen (Enter V S)
- [x] Slim × en : (splitsen) → Hoofdrekenen (Enter V S)
- [x] Snelrekenen › Gemengd → Hoofdrekenen › Gemengd (Enter = 60 seconden, T, Z; zonder zichtbare timer
      alleen 20 sommen)
- [x] Snelrekenen: records, dagbonus en het verloop blijven

### Cijferen
- [x] Cijferend optellen → Cijferen › Optellen (Enter V S)
- [x] Cijferend aftrekken → Cijferen › Aftrekken (Enter V S)
- [x] Cijferend vermenigvuldigen → Cijferen › Vermenigvuldigen (Enter V S)
- [x] Staartdeling → Cijferen › Staartdeling (Enter V S)

### Breuken en Procenten → Breuken en procenten
- [x] Breuken herkennen → Herkennen (Enter V S)
- [x] Breuken vergelijken → Vergelijken (Enter V S)
- [x] Gelijkwaardig en vereenvoudigen → Vereenvoudigen (Enter V S)
- [x] Breuk van een getal (Enter V S)
- [x] Optellen en aftrekken (Enter V S)
- [x] Breuk en kommagetal (Enter V S)
- [x] Het honderdveld → Honderdveld (Enter V S)
- [x] Procent, breuk en kommagetal (Enter V S)
- [x] Procent van een getal (Enter V S)
- [x] Korting en btw (Enter V S)

### Eenheden (+ 2 uit Meetkunde) → Meten (9 onderwerpen)
Eenheden kiest nu eerst de vorm (Vrij / Reeks / Tabel-oefening / Spiekbrief) en dan de maat. Na stap A eerst de maat,
dan de toets.
- [x] Eenheden › Lengte → Meten › Lengte (m) (Enter V S H)
- [x] Eenheden › Massa → Meten › Massa (g) (Enter V S H)
- [x] Eenheden › Inhoud → Meten › Inhoud (l) (Enter V S H)
- [x] Eenheden › Oppervlakte (vanaf 5de) → Meten › Oppervlakte (m²) (Enter V S H)
- [x] Eenheden › Volume (vanaf 6de) → Meten › Volume (m³) (Enter V S H)
- [x] Eenheden › Door elkaar → Meten › Maten gemengd (Enter V S H)
- [x] Eenheden › Zelf kiezen → Meten › Maten zelf kiezen (Enter V S H; de eenheden aanduiden blijft een stap)
- [x] Eenheden › Spiekbrief → S op elk van de zeven maten
- [x] Oppervlakte en omtrek (Meetkunde) → Meten › Oppervlakte en omtrek (Enter V S)
- [x] Formules (Meetkunde) → Meten › Formules (Enter V S)

### Tijd, geld en snelheid (blijft een eigen domein, na Meten)
- [x] De klok (Enter V S)
- [x] Tijd (Enter V S)
- [x] Geld (Enter V S)
- [x] Snelheid (Enter V S)

### Meetkunde
- [x] Schatkaart (Enter V S)
- [x] Hoeken (Enter V S)
- [x] Schaal (Enter V S)

### Vraagstukken
- [x] Vraagstukken oplossen → Oplossen (Enter V S)
- [x] Speurneus: zoek de fout → Speurneus (Enter V S)
- [x] Schatten en controleren (Enter V S)

### Rond een oefening (blijft)
- [x] Hoe moeilijk? (Makkelijk / Normaal / Moeilijk / Heel moeilijk), zoals nu
- [x] na een reeks: het rapport, fouten opnieuw (dezelfde of gelijkaardige vragen)
- [x] Eenheden: tabel-oefening en fouten opnieuw
- [x] na de oefening terug in dezelfde onderwerpenlijst, op hetzelfde onderwerp

## Spiekbrieven (hoofdmenu)
- [x] Nu: domein → de spiekbrief van dat domein. Na: Wiskunde → domein → de spiekbrieven van dat domein.
- [x] Elke spiekbrief van nu is nog bereikbaar (hier én met S op het onderwerp).

## Verder en Herhalen
- [x] Verder stelt eerst herhalen voor, anders de vorige oefening (ook een vorige eenheden-oefening), anders kiezen.
- [x] Verder werkt ook met een `laatste_oefening` die nog door 0.19.0 bewaard is.
- [x] Herhalen: eenheden en de andere onderwerpen na elkaar, zoals nu; alleen de broodkruimel verandert.

## Mijn avatar
- [x] W winkel: laag → item → kopen → meteen aantrekken
- [x] K kast: ←→ wisselen, B bewaren, C combinaties (aantrekken, weggooien)
- [x] ←→ gezichtje
- [x] **nieuw hier:** L Schermkleuren (uit Opties)

## Opties (verdwijnt aan de kant van het kind)
- [x] Naam → staat al in Ouders › Kinderen › kind
- [x] Leerjaar (nu alleen tonen) → staat al in Ouders › Kinderen › kind
- [x] Kleuren (standaard, kleurenblind rood-groen, blauw-geel, hoog contrast, geen kleur) → Mijn avatar › L Schermkleuren
- [x] Eenvoudige tekens → Ouders › Kinderen › kind › Weergave
- [x] Muis → Ouders › Kinderen › kind › Weergave
- [x] Typrichting in tabellen → Ouders › Kinderen › kind › Weergave
- [x] Avatar → Ouders › Kinderen › kind › Weergave
- [x] Animaties → Ouders › Kinderen › kind › Weergave
- [x] Klok in een eigen venster → Ouders › Kinderen › kind › Weergave
- [x] startargumenten (`--kleurenblind`, `--ascii`, `--geen-muis`, `--zonder-klokvenster` …) blijven voorrang hebben

## Toetsen die overal blijven
- [x] cijfers 1–9 en 0 kiezen in een menu; ↑↓ (ook j k, Tab) en Enter; Esc of q = terug
- [x] klikken, het muiswiel, een klik op de broodkruimel
- [x] F2 klok in de terminal, `?` tip, Tab klad

## Bewaard (niets aan veranderen)
- [x] de 36 vaardigheid-ids in sessies, antwoorden en de herhaalbak (eenheden: één id voor alle maten)
- [x] snelrekenen: `snelrekenen.tafels`, `.plusmin`, `.gemengd` met `snel60` / `snel20` (records)
- [x] `laatste_oefening` per kind (voor Verder)
- [x] de instellingen per kind en de plek van het klokvenster

## Moet mee veranderen
- [x] tests die met cijfers door de menu's lopen (`test_schermen`, de aap in `test_stabiliteit`, `test_avatar`,
      de onderwerptests)
- [ ] `docs/tools/scenarios.py` en alle schermafdrukken
- [ ] de handleiding (`opties.md` en `snelrekenen.md` gaan op in de nieuwe plekken), README, testlijst, CLAUDE.md

## Bewijs (controle vóór A6)

Per deel: waarmee elke regel hierboven nagekeken is. "0.19.0-vergelijking" = een databank gevuld met de echte schermen
van 0.19.0, daarna een kopie geopend met stap A en alles vergeleken met wat 0.19.0 toont. "tmux" = een echte terminal
van 80×24.

- **Wie ben jij?** `TestStart` (eerste start, tweede start, dubbele naam, wisselen),
  `test_pincode_instellen_en_gebruiken`, `TestToegang`, `test_broodkruimel_bij_een_nieuw_kind`; tmux: `--ouder`
  (met `--ascii`, alles ASCII).
- **Ouders:**
  - Rapporten: `test_rapport_export_en_kalender`, `TestIndeling` (per vak en domein, snelrekenen apart, export),
    0.19.0-vergelijking (samenvatting, dagen, denkfouten, fouten, status en de eerste 11 CSV-kolommen gelijk; de
    JSON-export identiek; totaal 200 = 200 antwoorden).
  - Kinderen: `TestKinderenBeheren` (leerjaar, timer, pincode, wissen, export).
  - Punten (bonus) en Wachtwoord wijzigen: los nagespeeld (bonus bewaard, nieuw wachtwoord werkt).
  - Opmerkingen: `test_opmerking_bewaren_en_lezen`.
  - Vergrendelen: `test_vergrendelen_na_inactiviteit`.
- **Hoofdmenu:** `test_hoofdmenu_vaste_volgorde`; tmux (volgorde, geen Opties, klik op Mijn avatar, het wiel).
- **Wiskunde, alle 43 onderwerpen:**
  - `test_elk_onderwerp_in_drie_keuzes`, `test_elke_modus`, `test_elke_spiekbrief`;
  - tmux met elke toets op elk onderwerp, telkens timer aan (237 toetsen), timer uit (231) en `--ascii`
    `--kleurenblind` (237), zonder fout. Daarbij: de voetregel past, de juiste knoppen, terug op hetzelfde
    onderwerp, een letter die niet geldt doet niets;
  - een eenmalige aap van 936 runs (elk onderwerp × elke toets × timer aan/uit × ASCII), zonder fout.
- **Snelrekenen:** `test_snelrekenen_20_sommen`, `test_snelrekenen_60_seconden_met_klok`,
  `test_zonder_timer_alleen_20_sommen`. Het eindscherm met de laatste rondes (verloop) en de records los nagespeeld.
- **Rond een oefening:** `test_reeks_van_tien_wordt_bewaard`, `test_fouten_opnieuw_na_reeks`, `TestMuis`
  (tabel-oefening), `test_terug_op_hetzelfde_onderwerp`, `test_broodkruimel_uit_elke_soort_oefening`.
- **Spiekbrieven:** `test_gedeelde_spiekbrief_een_keer`; tmux (elk domein, elke spiekbrief).
- **Verder en Herhalen:**
  - `test_verder_met_een_oefening_van_versie_019`, `test_herhalen_en_verder`, `test_verder_hervat_vorige_oefening`;
  - 0.19.0-vergelijking: dezelfde voorstellen, dezelfde 29 herhaalvragen, en dezelfde oefening start.
- **Mijn avatar:** `TestWinkelSchermen` (winkel, kast, combinaties), `test_mijn_avatar`, `test_schermkleuren_*`,
  `test_voetbalk_van_mijn_avatar`; tmux (klik op de L-regel, thema kiezen).
- **Opties → nieuwe plekken:**
  - `TestWeergave` (alleen dat kind, startargument niet bewaard, `--ascii` blijft voorgaan);
  - tmux: muis uit en aan;
  - onder Xvfb: klokvenster uit stopt het venster meteen;
  - 0.19.0-vergelijking: de instellingen van beide kinderen zijn ongewijzigd.
- **Toetsen die overal blijven:**
  - `TestMenuToetsen`, `test_voetregel_klikbaar_in_het_echte_menu`, `test_voetregel_in_eenvoudige_tekens`,
    `test_toetsen_botsen_niet`, `test_f2_klok_in_de_terminal_en_terug`, `test_klad_met_tab_en_dan_antwoorden`;
  - tmux: klik op de voetregel ([H]), de broodkruimel op 3 niveaus, het wiel, een te klein venster en terug;
  - onder Xvfb: De klok via de nieuwe weg, met het klokvenster en F2.
- **Bewaard:** `test_niets_bewaard_zonder_onderwerp`, `test_elke_vaardigheid_staat_in_het_menu`; 0.19.0-vergelijking
  (geen migratie, dezelfde rijen, `laatste_oefening` en instellingen ongewijzigd).
- **Moet mee veranderen:** de tests zijn aangepast en groen. Scenario's, schermafdrukken en de handleiding volgen
  in A6.
