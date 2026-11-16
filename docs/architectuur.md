# Architectuur in detail

De details bij `CLAUDE.md` (daar staan de lagen, de gouden regels en de werkwijze). Lees het stuk over het deel
waaraan je werkt. Uit CLAUDE.md gehaald op 16/11/2026, woord voor woord, zodat CLAUDE.md kort blijft.

## Lagen
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

## Gegevens, opslag en stabiliteit
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

## De vaste werkwijze
- **De vaste werkwijze** (elke oefening dezelfde, zodat het kind niet verloren loopt): lees, klad (`Tab`), antwoord;
  **F1** (`scherm.HULP`; niet `?`: dat typt het kind in zijn klad als vraag aan zichzelf, `KladRegel.vraag`) =
  getrapte tips (`Onderwerp.tips`), na de laatste tip de spiekbrief bij het kopje van de vraag
  (`Onderwerp.spiek_kop`/`kop_op_spiekbrief`; een test kijkt na dat elk kopje bestaat; Esc = terug naar de vraag),
  daarna weer tip 1; fout = één tweede kans (niet bij janee/vergelijk/keuze en objecten met een
  eigen stappenlogica: `GEEN_TWEEDE_KANS` in `terminal/oefenaar.py`), daarna "Zo kan het:" in klad-regels, met het
  eigen klad ernaast (`Kladblad.teken_kader`: ✔ ✘ en ! waar `analyseer` een denkfout ziet). Het klad
  is één onderdeel voor alles: `terminal/kladblad.py` (ook in het vraagstuk). **Elk nieuw rekenonderwerp** zet
  `klad = "ja"` (of `"verplicht"`, met `klad_klaar`) en geeft `oplossing(v)` in klad-regels (`kern/klad.stap`,
  `oplossing_van`, `fout_pad`); `tests/test_werkwijze.py` kijkt na dat elke regel klopt en op het antwoord eindigt.
  De terminal vraagt de oplossing altijd via `oplossing_of_niets` (een fout komt in het logboek, nooit bij het kind).
  Het klad-nakijken tegenover een oplossing is `kern/klad.analyseer` (ook voor vraagstukken). In een vraagstuk
  geldt ook de **herkomstregel** (`bekend`, via `analyseer_klad`): een regel die op een stap uitkomt, mag alleen
  getallen gebruiken uit het verhaal, de stappen, een regel erboven of `OMREKENEN`; anders `vs_herkomst` ("waar
  komt 20 vandaan?"). Splitsen mag (verzonnen getallen die samen een bekend getal maken). Een andere juiste weg
  met eigen tussenuitkomsten zet een structuur in `Bouw.ook_juist` (geen fout pad).
  Weggaan midden in een vraag (nog niet nagekeken) of een snelrekenronde: een oefenscherm zet `with s.bewaak(actief,
  ses)`; dan vragen **Esc en de broodkruimel** (ook vanuit de spiekbrief) vanzelf eerst "Wil je stoppen?"
  (`Scherm.bevestig`, "Nee" gekozen; Nee = `KEY_RESIZE`, de tijd erin telt niet mee via `Sessie.pauze`). Esc in een
  deelscherm (`@deelscherm`: menu, lezer, invoer, kader) is van dat deelscherm. Een nieuw oefenscherm doet hetzelfde.
  Een gestopte reeks met al minstens één antwoord toont het resultaat van wat gedaan is (`na_reeks(..., gestopt)`:
  "Je stopte na 2 van de 10 vragen."). Esc of Stoppen in het hoofdmenu = het titelscherm (`App.start` is een lus:
  titelscherm → Wie ben jij? → hoofdmenu); Esc op het titelscherm sluit het programma.

## Nieuwe onderwerpen en soorten invoer
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
  `p` zet in het rooster de plaatswaarden aan (`Rooster.plaats_naam`, `PLAATSEN`; niet bij × met een komma), per
  kind bewaard in `Instellingen.plaatswaarden` (de Oefenaar geeft de keuze door en bewaart ze).
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

## Vraagstukken
- **Vraagstukken** (`kern/wiskunde/vraagstukken.py`): een verhaalmachine = rekenstructuur (Python: getallen en
  stappen als `Rekenstap`) × wereld (`inhoud/vraagstukken/werelden.json`) × verwoording (`zinnen.json`, sjablonen
  van `kern/verhaal.py`). De foute paden (denkfouten) volgen automatisch uit de stappen; het klad leest
  `kern/klad.py`. Het onderwerp (voor herhaling) is de structuur, zodat herhalen een andere wereld geeft. `Verhaal.soort`
  (`getal`, `klok`, `duur`) zegt hoe het antwoord gelezen wordt; tijd rekent in minuten, en het klad kent
  tijdstippen (`9.45 u`, `9:45`). Invoer
  `"vraagstuk"` = `terminal/vraagstuk.py` (4 stappen). Haakjes in de Oefenaar voor zo'n invoer-object: `eigen_tekst`
  (tekent zelf de vraag), `eigen_tip` (F1 gaat naar het object), `extra` (bewaard bij het antwoord en gebruikt
  voor de punten) en `uitleg_na`. `tests/test_vraagstukken.py` maakt elke structuur in elk leerjaar en kijkt na
  dat het verhaal klopt, past (4 × 56 tekens) en mooi uitkomt. De Speurneus (invoer `"speur"`, model `Speur`)
  maakt van een fout pad (of een rekenfout) het klad van een ander kind; Schatten (invoer `"keuze"`, model
  `Keuze`) gebruikt de controle-regel van het vraagstuk. Beide bouwen op `VRAAGSTUKKEN.maak_met`.

## Punten, wachtwoorden, rapporten en het slot
- Punten: regels in `kern/punten.py`; een `Sessie` kent de punten per antwoord toe; elk punt staat in het logboek.
- Wachtwoorden en pincodes alleen via `kern/wachtwoord.py` (pbkdf2, formaat met methode en iteraties).
  Rapporten en export zitten in `kern/rapporten.py` (geeft regels met rollen terug; ook het logboek:
  `antwoorden_lijst`, `punten_regels`, `zet_in_herhaalbak` voor Ouders › Antwoorden, #24); het ouderdeel in
  `terminal/schermen/ouder.py` zet `Scherm.slot` (vergrendelen na inactiviteit).
- **Stoppen op slot** (0.23.2, `kern/stopslot.py`): per kind `Instellingen.stoppen_slot`, open te maken met de
  ouderpin (`Opslag.ouder_pin`, 4 cijfers). Zonder ouderpin geldt geen slot (niemand zit vast). `App.start` gaat dan
  meteen naar `vergrendeld_kind` (geen titelscherm, geen "Wie ben jij?"), Esc/Stoppen in het hoofdmenu =
  `App.slotscherm` (Esc of 3× fout = terug), en `zonder_onderbreken` negeert Ctrl-C (ook Ctrl-\ en Ctrl-Z) zolang
  dat kind actief is. Openen: de pin, of `--ouder` › Kinderen › kind › Stoppen op slot.

## Gemengd oefenen (een reeks uit verschillende onderwerpen)
- **Een reeks uit verschillende onderwerpen** (0.24, `kern/reeks.py`; Gemengd oefenen nu, de examens later):
  - thema's = de domeinen van het leerplan (`curriculum.gemengd_themas`, als data aan de kern gegeven; Taal komt er
    vanzelf bij);
  - `kies_onderwerpen` (alleen wat al geoefend werd; gewogen: "fris houden" > bezig > beheerst; hoogstens
    `MAX_NA_ELKAAR` uit hetzelfde thema na elkaar en `MAX_LANG` lange vragen, `Onderwerp.lang`) → `maak_vragen` →
    een `Reeksplan` (vragen + `Hulp`) → de terminal speelt het met `Oefenaar.speel_plan` → `Uitslag` (ook per thema);
  - Maten doet mee als `reeks.MATEN` (dezelfde namen als een Onderwerp); `Oefenaar.stel_vraag` geeft die vraag aan
    het scherm van de eenheden;
  - `Hulp` = de schakelaars (tips, tweede kans, spiekbrief, uitleg na de vraag, herhaalbak, punten via
    `Sessie(punten=False)`); `Hulp.EXAMEN` zet ze uit (getest in `tests/test_gemengd.py`). Een vraagstuk-object heeft
    nog een eigen tweede kans: dat is werk voor de examens;
  - wie de thema's kiest: `Instellingen.gemengd_themas` (het kind) en `gemengd_ouder` (`reeks.ouder_keuze`: kind,
    vast, één keer; "één keer" vervalt met `reeks.na_reeks` als de reeks tot het resultaat kwam);
  - **een examen bouwen** = de ouder kiest thema's/onderwerpen en het aantal, een `Reeksplan` met `Hulp.EXAMEN`,
    dezelfde speler, en de `Uitslag` bewaren (dan pas een migratie). "Fris houden" (`herhaling.FRIS_HOUDEN`, na
    `FRIS_DAGEN`) staat ook in het rapport.

## Taal
- **Taal** (0.25, het plan in `docs/taal.md`; de vader: thuis het katholieke leerplan):
  - `kern/taal/zinnen.py`: `Zin` (woorden met hun woordsoort + `Deel`en; volledig ontleed, de pv hoort bij het
    gezegde) en de **haakjes** (`[o De juf] [pv geeft] [lv een boek].`, `lees_haakjes`/`Zin.haakjes`), met fouten in
    gewone taal;
  - `kern/taal/zinnenmachine.py` + `inhoud/taal/woorden.json`: een zinsbouw × de woordenlijst (werkwoordvormen
    uitgeschreven, nooit geraden), de pv past bij het onderwerp en de tijd, `BREEDTE` past op het scherm;
  - `kern/taal/nagekeken.py` + `inhoud/taal/zinnen.json` (0.25.1): de met de hand geschreven zinnen (`zinnen` per
    leerjaar 4, 5, 6, volledig ontleed; `twee` = zinnen met meer dan één pv). De leerlijn zegt hoe vaak ze komen
    (`nagekeken_op_tien`, `twee_op_tien`); de zinsbouw van zo'n vraag is `nagekeken` of `twee_lijst`;
  - **een zin met meer dan één pv** (`Zin.samengesteld`, alleen waar de leerlijn `twee_pv` geeft: Moeilijk): alleen
    de pv's en hun onderwerp zijn aangeduid, met een `|` tussen de deelzinnen (`zinnen.deelzinnen`: elke pv met zijn
    onderwerp; zonder `|` delen de pv's één onderwerp). De stappen zijn "pv" (alle pv's) en "o1", "o2" …
    (`zinsontleding.soort("o2")` = "o"); de machine maakt ze met `maak_samengesteld` (`SAMENGESTELD`);
  - `kern/taal/zinsontleding.py`: de stappen per leerjaar (leerlijn `taal.zinsontleding`), nakijken (ook "er is er
    geen"), de denkfouten (`zo_…`), de tips (de vraag van school, het proefje zonder het antwoord), de uitleg, vrij
    kleuren, verdelen, de spiekbrief (`SPIEK_KOP` per stap) en het `Onderwerp` (invoer `"zinsdelen"`);
  - `terminal/zinsdelen.py`: het invoer-object (stappen, Tab = vrij kleuren, Makkelijk eerst verdelen, een eigen
    tweede kans die `Hulp.tweede_kans` volgt); de kleuren zijn de rollen `z_pv` … `z_bwb` in `terminal/thema.py`
    (als een markeerstift: zwart op de stiftkleur, pv geel, o blauw, lv groen, mv roze, gezegde oranje, bwb paars; de
    afkorting staat er altijd onder, nooit kleur alleen; de cursor is een streep onder de woorden);
  - `terminal/curriculum/taal.py`: een domein zonder onderwerpen = nog niet gebouwd, grijs in het menu.

## Werkwoordspelling
- **Werkwoordspelling** (0.26, T3):
  - `inhoud/taal/werkwoorden.json`: de werkwoorden met elke vorm uitgeschreven (stam, tt = [ik, jij, hij, meervoud],
    vt, vd, hulp, `vt_soort`/`vd_soort` zwak of sterk, `ge`, `niveau` 1–3, `rest` = wat na het werkwoord kan staan,
    `o` = eigen onderwerpen, `ook` = ik-vormen die ook goed zijn). `tests/test_taal_werkwoorden.py` rekent elke
    zwakke vorm na met de regels (`regel_tt`, `regel_vt`, `regel_vd`): een tikfout in de lijst wordt rood;
  - `kern/taal/werkwoorden.py`: de zin met een gat (`WwZin`, `maak_zin`: onderwerp eerst, een tijdwoord eerst, of
    een vraag; geen zij/ze, want dat kan één of meer zijn), het denkschema als data (`stappen` → `Stap`: een keuze
    of een woord typen, de laatste stap is altijd de vorm), `nakijken`, de denkfouten (`ws_…`), de uitleg en de
    spiekbrieven (`KOP` per stap). Eén `Onderwerp` per menu-item (`Werkwoordspelling` met `vorm` en `past`); het
    groepje voor herhaling is "persoon/stamsoort" (bv. `jij_inv/d`); de leerlijn kiest `niveaus`, `stammen`
    (gewoon, d, t, vz), `personen`, `patronen` en `stap_voor_stap`;
  - `terminal/werkwoord.py`: het invoer-object `"werkwoord"` (speelt de stappen: cijfer, ↑↓ + Enter of een klik;
    Tab = meteen typen; 't kofschip met de letter die oplicht; een eigen tweede kans die `Hulp.tweede_kans` volgt).
    Het antwoord van de vraag is de getypte vorm; een fout in een stap ervoor telt als "met een tweede kans";
  - 0.26.1: `VerledenTijdSterk` (geen regel: `rijtje`, de stappen zijn "één of meer" en de vorm; het groepje voor
    herhaling is het werkwoord, bv. `ev/lopen`) en `VoltooidDeelwoord` (`vorm = "vd"`: het gat staat achteraan, na
    heeft of is; zwak = stam → 't kofschip (t of d) → vorm, sterk = meteen typen; de leerlijn heeft `sterk` = de
    niveaus van de sterke werkwoorden en `zonder_ge`). `sterk(zin)` zegt of de gevraagde vorm een sterke vorm is.
    Tegenwoordige tijd op Heel moeilijk (`homofoon` in de leerlijn m1): `homofoon(w)` = verhuist/verhuisd; dan
    vraagt dat onderwerp ook zinnen met `vorm = "vd"`. Een kopje dat niet op de spiekbrief van het onderwerp staat,
    wordt `kop_anders`. Wat na het werkwoord staat (`rest`) mag geen deel van een scheidbaar werkwoord zijn
    ("de deur open" → opengehouden): een test bewaakt dat;
  - 0.26.2: `ZetInDeVerledenTijd` (`omzetten = True`): de `WwZin` heeft dan `omzetten`, `bron` (de zin in de
    tegenwoordige tijd, zonder tijdwoord dat maar in één tijd past: `BEGIN`) en `pv_plek`. De stappen: "pv" (soort
    `"woord"`: een woord aanduiden in de zin), "soort" (zwak of sterk) en de vorm. `lijst_voor` kiest eerst zwak of
    sterk (even vaak); het groepje is `zwak/stamsoort` of `sterk/werkwoord`. Het scherm tekent de bron
    (`teken_bron`, de gevonden pv in de rol `z_pv`) en eronder de zin van toen met het vak.


## Menu's (Vak › Domein › Onderwerp)
- Alle oefenmenu's komen uit één leerplan: `terminal/curriculum/` (`Vak` › `Domein` › `Onderwerp`, volgorde =
  volgorde in het menu; `wiskunde.py`, `taal.py`, later `frans.py`). Een `Onderwerp` heeft `modi` (reeks, vrij,
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
- Hoogstens **10 items per menu** (cijfertoetsen 1–9 en 0; test). Het hoofdmenu (0.23, de vader) staat in groepen
  met kopjes (`Scherm.menu(koppen=, grijs=)`): ▶ Verder, Herhalen · VAKKEN (Wiskunde, Taal; grijs wat `CU.BINNENKORT`
  is; Leerstof = de spiekbrieven, met eerst "Welk vak?" als meer vakken spiekbrieven hebben) · JIJ (Mijn avatar,
  Winkel) · FEEDBACK (Zeg het ons) · Stoppen: 9 keuzes. Er is nog plaats voor één (Frans); vóór er meer bijkomt
  (Examens, Avontuur) eerst met de vader een oplossing kiezen.
  Verder: een reeks die tot het resultaat komt, is "af" (`App.oefening_af`); dan stelt Verder eerst herhalen voor.
  Herhalen is een menu (0.24): Mijn herhaalvragen (`App.herhaalvragen`) en Gemengd oefenen (`schermen/gemengd.py`).
- Spiekbrieven met dezelfde titel binnen een domein worden één keer getoond, dus dezelfde titel = dezelfde
  spiekbrief (test).
- Instellingen: het kind kiest in Mijn avatar › **Schermkleuren** (L); de rest staat per kind bij de ouder
  (Ouders › Kinderen › kind › **Weergave**). Er is geen menu Opties meer.
- Over de indeling van de menu's beslist de vader: eerst een voorstel, dan bouwen.
