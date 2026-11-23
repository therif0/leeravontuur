# Schermen 1.0: inventaris van wat de beta overal moet veranderen

**Status:** inventaris, alle open vragen beantwoord (22/11/2026), fase 0 van [schermen.md](schermen.md). Geen code: alleen wat er veranderen moet,
waar, en wat nog niet beslist is. Gemaakt op de stand van de beta na commit `35dbcdf`.

**Legende**
- ✔ = beslist en al in de beta (Cijferen)
- ◐ = beslist of geschetst in het voorstel (`schermen.md`), nog niet gebouwd
- ✘ = een klein detail dat bij het bouwen beslist wordt (alle vragen voor de vader zijn beantwoord, 22/11);
  vroeger: nog niet beslist (de nummers verwijzen naar *Open vragen*
  onderaan)

Elke regel is afvinkbaar (`[ ]` → `[x]` als het gebouwd én in tmux bekeken is).

---

## A. Wat de beta al vastlegt (de regels die straks voor elk scherm gelden)
- [ ] ✔ `terminal/vak.py`: een vak met een rand, een titel in de rand, een toets in de onderrand (klikbaar).
- [ ] ✔ De **reeks bovenaan** onder de broodkruimel (een vak vanaf 30 rijen, anders één regel).
- [ ] ✔ De **vraag op een band** (oranje op grijs, rol `b_vraag`/`b_band`), met lucht rond + − × : =.
- [ ] ✔ **Tab = het klad** en terug, zoals overal (geen K). In het rooster deed Tab "volgende rij": dat is nu ↓.
- [ ] ✔ Het **klad is een kolom** van boven tot onder, rechts naast Vraag/Tip/Spiekbrief (24 tot 34 breed), **alleen
      bij onderwerpen die vandaag een klad hebben** (gekozen 22/11, vraag 20).
- [x] **Uit de beta halen:** de klad-kolom bij Cijferen (de vader 22/11: was een test van de indeling, Cijferen
      heeft geen klad nodig; het rooster is het rekenwerk).
- [ ] ✔ De **spiekbrief staat altijd open** waar er plaats is, met het stuk van de vraag in het licht; scrollt
      (PgUp, PgDn, wiel, klik in de rand); niet in een examen.
- [ ] ✔ Het **maatje** heeft de rechterkolom (20 breed).
- [ ] ✔ Na het nakijken wordt het vak Tip "Wat ging er mis?" of "Goed!".
- [ ] ✔ De voetregel: `[Esc] stoppen` past altijd (toetsen die in een rand staan, vallen onderaan weg).
- [ ] ✔ Het klad gaat mee met het antwoord (`extra["klad"]`); elke regel krijgt ✔ ✘ (klopt de rekenregel?).
      **Keuze van Claude, nog te bevestigen** (vraag 11).

**Wat in de beta een noodoplossing is en straks weg moet**
- [ ] `beta.InVak` (verschuiven en afknippen) en `beta.VERSCHUIF`: de objecten tekenen nog op vaste kolommen
      (`X0 = 12`, `X0 = 8`). Straks krijgt elk object een rechthoek (y, x, h, w) en tekent het daarbinnen.
- [ ] `beta.Meter` (een nepscherm om te meten hoe breed een object tekent): straks zegt elk object zelf
      `breedte()`/`hoogte()`.
- [ ] `beta.KORTER` en het wegfilteren van "deel → maal …" in `InVak.put`: tekst die in een rand hoort, moet het
      object als gegeven teruggeven, niet als getekende tekst.
- [ ] `BetaOefenaar` overschrijft een stuk van `Oefenaar._stel_vraag`: straks is er één Oefenaar (gouden regel 3).
- [ ] De rollen `b_vraag`, `b_band`, `b_cursor` (in alle 5 thema's van `thema.py`): straks gewone rollen
      (bv. `vraag`, `band`), ook in de schermkleuren die het kind in de winkel koopt (vraag 19).
- [ ] De vaste getallen bovenaan `beta.py` (`RECHTS`, `MAATJE_H`, `TIP_H`, `KLAD_MIN/MAX`, `SPIEK_MIN`,
      `GROOT_H`): straks in één **indeling** (welk vak waar, volgens de grootte van het scherm).

---

## B. Gedeelde bouwstenen (`terminal/`)
| ☐ | Bestand | Wat er nu is | Wat er moet veranderen | Stand |
|---|---|---|---|---|
| [ ] | `vak.py` | rand, titel, toets onder | ASCII-rand (`+-|`, via `tekens.py`), een vak met focus (andere rand), scrollen als bouwsteen (nu alleen in de spiekbrief van de beta) | ◐ |
| [ ] | *nieuw:* indeling | (in `beta.py`, per scherm) | één module: vakken volgens h × w (80×24 → groter), ook met klokvenster | ◐ |
| [ ] | `scherm.py` `nieuw`/`voet` | titelbalk + voetbalk | blijft; toetsen die in een rand staan niet dubbel onderaan | ✔ (beta) |
| [ ] | `scherm.py` `menu` | lijst op vaste rijen, uitleg tot een kolom | menu in vakken + kaartje (scherm 4 van het voorstel) | ◐ |
| [ ] | `scherm.py` `afvink` | afvinklijst (Gemengd, ouder) | in een vak? | ◐ (vraag 17) |
| [ ] | `scherm.py` `lezer` | scrollbare tekst (spiekbrief, rapport, uitleg) | in een vak met scrollen in de rand (zoals de spiekbrief van de beta) | ◐ |
| [ ] | `scherm.py` `bevestig` | kader midden over het scherm ("stoppen?") | al een kader: in de stijl van `vak.py` zetten | ✘ (klein) |
| [ ] | `scherm.py` `invoer` | één regel tekst (naam, wachtwoord, pin) | in een vak? | ◐ (vraag 17) |
| [ ] | `scherm.py` `te_klein` | "Maak het minstens 80x24" | blijft 80×24 als ondergrens | ✔ |
| [ ] | `maatje.py` | 3 plaatsen volgens de breedte (≥100: groot; ruim; tekstgezicht) | het maatje tekent in het vak dat het krijgt; tekstje in de onderrand | ✔ (beta, alleen Cijferen) |
| [ ] | `voortgang.py` | bolletjes op kolom 4/22/46, rij 2 | wordt het vak/de regel Reeks; Eenheden en Oefenaar gebruiken hem | ✔ (beta) |
| [ ] | `kladblad.py` | `teken` (regels), `teken_kader` (na het antwoord, 38 breed), lege tekst "typ hier je rekenregels" | klad als kolom; na een fout "Jouw klad" naast "Zo kan het" | ✔ kolom / ◐ na een fout |
| [ ] | `stappenhulp.py` | getrapte tips van zinsdelen en werkwoord | de tip in het vak Tip | ◐ (vraag 9) |
| [ ] | `digitaal.py` | digitaal klokje (33 breed, of compact) | past niet naast een klad van 34 in 80 breed | ◐ (vraag 2) |
| [ ] | `avatar.py` | pixel-avatar 16×8, groot in de winkel | blijft; in een vak | ◐ |
| [ ] | `tekens.py` | ronde hoeken ╭╮╰╯ + ASCII | alle nieuwe randtekens; testen op Windows (conhost/Terminal) en macOS Terminal | ✘ (nagaan) |
| [ ] | `thema.py` | 5 thema's, `b_`-rollen | gewone rollen; rand-rol per thema (`dim`) nakijken in elk thema | ◐ |
| [ ] | `klikzones.py` | zones per scherm | elk vak met een toets in de rand krijgt een zone (al zo in `vak.teken`) | ✔ |

---

## C. De Oefenaar (`terminal/oefenaar.py`, `_stel_vraag`): elke weg door het scherm
Nu tekent `_stel_vraag` alles op vaste rijen en kolommen (vraag op rij 6, model op rij 9, feedback vanaf `fb`, breed
70/54/62, klokvenster `LINKS = 60`). Elke weg hieronder moet in de indeling passen.

| ☐ | Soort vraag | Nu | Nieuw | Stand |
|---|---|---|---|---|
| [ ] | Gewoon antwoordvak (getal, breuk, woord, janee, vergelijk, soort …) | vraag + vak op één regel; lange vraag = afbreken op 54 | Vraag-vak + band; klad-kolom; Tip-vak (scherm 1) | ◐ |
| [ ] | Met een eenheid (`v.eenheid`) | eenheid op `vx + 15` | in het Vraag-vak | ◐ |
| [ ] | `klokwoord` (antwoordvak 22 breed) | `VAK = {"klokwoord": 22}` | idem, breder vak | ◐ |
| [ ] | Klad verplicht (`klad_voor == "verplicht"`) | focus begint in het klad | focus begint in de klad-kolom | ◐ |
| [ ] | Geen klad (`klad_voor` leeg) | geen klad | blijft zonder klad (gekozen 22/11); de vrije plaats gaat naar Vraag, Tip en spiekbrief | ◐ |
| [ ] | Rooster, staartdeling | object op rij 8 | ✔ in de beta | ✔ |
| [ ] | Invoer-object met `naast` (veld, coord, wijzers) | feedback rechts van het object | object in het Vraag-vak; feedback in Tip | ◐ (vraag 2) |
| [ ] | `lijn` (aanduiden op de getallenlijn, zoomen) | getallenlijn 72 breed op rij 9 | past niet in een vak van 56 binnenin | ◐ (vraag 2) |
| [ ] | Model onder de vraag (getallenlijn, balk, groepjes, strook, veld, figuur, kaart, hoek, klok) | `teken_model` op rij 9; hoger dan 7 = feedback ernaast | per model een plaats | ◐ (vraag 2) |
| [ ] | Digitaal klokje (`klok`) | onder de vraag of naast een hoog model | idem | ◐ (vraag 2) |
| [ ] | Klokvenster open | tekst links van kolom 60 | de rechterkolom (maatje) valt weg? klad-kolom? | ◐ (vraag 21) |
| [ ] | Eigen tekst (vraagstuk) | object tekent vanaf rij 4 de hele breedte | zie D: vraagstuk | ◐ (vraag 8) |
| [ ] | Tweede kans (`kans_melding`) | melding onder de vraag | in het vak Tip of onder de vraag? voorstel scherm 3 zet het in "Antwoord" | ◐ |
| [ ] | Getrapte tips + "Nog eens F1: spiekbrief" | tekst onder de feedback, 2 à 4 regels | Tip-vak met "Tip 1 van 3 ●○○" in de rand | ◐ (vraag 4) |
| [ ] | Spiekbrief via F1 na de laatste tip | `lezer` over het hele scherm | altijd open waar er plaats is; anders? (80×24: meestal geen plaats) | ✔ groot / ◐ 80×24: volle scherm zoals nu (vraag 13) |
| [ ] | Na het antwoord: juist | lof + (vrij) uitwerking | "Goed!" in Tip | ✔ (beta) |
| [ ] | Na het antwoord: fout | kop + diagnose + "in je klad regel n" + uitwerking; klad-kader 38 breed rechtsonder | "Jouw klad" ✔✘! naast "Zo kan het" + vak "Wat ging er mis?" (scherm 2) | ◐ (vraag 12) |
| [ ] | "De uitkomst klopt, maar onderweg ging het n keer mis" (rooster) | kop in accent | in "Wat ging er mis?" | ✔ (beta) |
| [ ] | Examen (geen tips, geen uitleg: "Je antwoord is bewaard.") | geen F1, geen kader | geen Tip-vak, geen spiekbrief: wat vult de plaats? | ◐ (vraag 13) |
| [ ] | Vrij oefenen (geen reeks) | "Vrij oefenen: 3 van 5 juist" op rij 2 | de regel/het vak Reeks met vrij-teller | ◐ |
| [ ] | `kies_niveau` (Hoe moeilijk?) | `s.menu` | menu in vakken | ◐ |
| [ ] | `spiekbrief` (los, vanuit het menu) | `s.lezer` | lezer in een vak | ◐ |
| [ ] | `na_reeks` / `rapport` (einde van een reeks) | eigen tekst + menu | in vakken: wat staat waar? | ◐ (vraag 22) |
| [ ] | `herhalen` (herhaalbak) | gewone Oefenaar | volgt vanzelf | ◐ |
| [ ] | Sprongetje van het maatje bij juist (`spring`, `pauze(170)`) | maatje één rij hoger | in een vak: mag het buiten zijn vak? | ✘ (klein) |

---

## D. De invoer-objecten (elk tekent nu zelf op vaste rijen en kolommen)
Straks: elk object krijgt een rechthoek, geeft zijn breedte en hoogte, geeft zijn tip-tekst aan het vak Tip en zijn
randtekst (bv. "deel → maal → min → neer", typrichting) als gegeven terug.

| ☐ | Object | Bestand | Waar gebruikt (kern) | Vast nu | Stand / wat niet beslist is |
|---|---|---|---|---|---|
| [ ] | `RoosterInvoer` | `rooster.py` | cijferen | `X0 = 12`, Tab = volgende rij | ✔ beta (via `InVak`); omzetten naar een rechthoek |
| [ ] | `StaartInvoer` | `rooster.py` | cijferen | `X0 = 8`, `VENSTER = 7` | ✔ beta (via `InVak`); idem |
| [ ] | `BalkInvoer` (breukbalk) | `balk.py` | breuken, meetkunde | `X0 = 8`, `BALK_B = 52` | ◐ 52 + rand + klad 34 > 80: volle breedte (vraag 2) |
| [ ] | `VeldInvoer` (cm²-rooster) | `balk.py` | procenten | `X0 = 10`, `naast = (13, X0+23)` | ◐ (vraag 2) |
| [ ] | `CoordInvoer` (schatkaart) | `balk.py` | meetkunde | `X0 = 8`, `naast` | ◐ (vraag 2) |
| [ ] | `KlokInvoer` (wijzers) | `balk.py` | klok | klok 21×11 pixels, `naast`, of in het klokvenster | ◐ (vraag 2, 21) |
| [ ] | `ZinsdelenInvoer` | `zinsdelen.py` | zinsontleding | `OPDRACHT_BREED = 56`, **Tab = vrij kleuren**, eigen getrapte tips | ◐ scherm 3 (Stappen rechts); ◐ Tab blijft (vraag 10), tips in het vak Tip (vraag 9), kleuren per zinsdeel in een vak (`docs/taal.md`) |
| [ ] | `WerkwoordInvoer` | `werkwoord.py` | werkwoorden, zinnen | `OPDRACHT_BREED = 56`, **Tab = wissel**, kofschip, bron, gevonden | ◐ eerst een schets voor de vader (vraag 23); Tab blijft (vraag 10) |
| [ ] | `VraagstukInvoer` | `vraagstuk.py` | vraagstukken | tekent zelf alles (`eigen_tekst`), `X = 2`, `KOP = 15`, eigen klad (`MAX_KLAD = 8`), **Tab/Shift-Tab = stappen** | ◐ gekozen 22/11: stappen rechts, klad-kolom, pijltjes (vraag 8) |
| [ ] | `SpeurInvoer` | `vraagstuk.py` | vraagstukken | eigen tip-vak (`_MetTip.teken_tip`), kader "Het verhaal" | ◐ (vraag 8, 9) |
| [ ] | `KeuzeInvoer` | `vraagstuk.py` | vraagstukken, werkwoorden | eigen tip-vak (`_MetTip`) | ◐ (vraag 9) |
| [ ] | Getallenlijn aanduiden (`lijn`) | in `oefenaar.py` | getallen | 72 breed, zoomstapel | ◐ (vraag 2) |

**De modellen** (`modellen.py`, getekend onder de vraag; alleen tonen, geen invoer)
- [ ] Getallenlijn: `posities(…, breedte=72)` → past niet in een vak van 56 binnenin. ◐ (vraag 2)
- [ ] Breukbalk: `BALK_B = 52`. ◐ (vraag 2)
- [ ] Groepjes: breedte 68. ◐ (vraag 2)
- [ ] Strook: `STROOK_B = 50`. ◐ (vraag 2)
- [ ] cm²-veld: `VAK_B = 4` per vakje. ◐ (vraag 2)
- [ ] Figuur (pixels of tekens), schatkaart (`KAART_B = 3`), hoek (`HOEK_R = 6`): hoogte nakijken. ◐ (vraag 2)
- [ ] Klok: 21×11, met `VENSTER_TEKST` "De klok staat in een eigen venster" + F2. ◐ (vraag 21)

---

## E. Andere oefenschermen
- [x] **Eenheden** (`schermen/eenheden.py`, 678 regels, 48 keer `put`): een **eigen kopie van de Oefenaar** (eigen
      `stel_vraag`, `voortgang`, `reeks`, `rapport`, `vrij_oefenen`, `herhalen`, `spiekbrief`) + de tabelvraag
      (`teken_tabel`, "Antwoord:" op een vaste rij). ◐ Eerst laten opgaan in de Oefenaar (gekozen) (vraag 7)
      **Fase 1 (0.27.0):** opgegaan in de Oefenaar (`terminal/tabel.py`, `MatenOefenaar`); dezelfde schermen en
      antwoorden als vroeger (vergelijking in tmux op een kopie van echte gegevens).
- [ ] **Snelrekenen** (`schermen/snelrekenen.py`): tijd, ronde, uitslag; geen klad, geen tips. ✘ Niet geschetst
      (vraag 16).
- [ ] **Gemengd** (`schermen/gemengd.py`): een afvinklijst en dan de gewone Oefenaar. ◐ (volgt de Oefenaar);
      de afvinklijst: vraag 17.
- [ ] **Herhaalvragen / Herhalen** (`app.herhaalvragen`, `app.herhalen`): de Oefenaar met vragen uit verschillende
      onderwerpen: de broodkruimel en het Tip-vak wisselen per vraag. ◐

---

## F. Menu's en navigatie
- [ ] `navigatie._menu`, `vak`, `domein`: lijst + uitleg. ◐ scherm 4 (lijst, kaartje, Kies).
- [ ] `navigatie.toetsen_voor` / `modi_voor` (Enter = reeks, V = vrij, S = spiekbrief): het vak "Kies". ◐
- [ ] `navigatie.spiekbrieven`, `_spiek_domeinen`, `_spiek_lijst`: menu + lezer. ◐
- [ ] Hoogte: hoogstens 10 items per menu; scherm 4 toont 4 items met een lege regel ertussen. Met 8 à 10 items
      past dat niet samen met een kaartje op 24 rijen. ◐ (vraag 15)
- [ ] Taal: lege domeinen (Woordsoorten, Spelling, Woordenschat, Begrijpend lezen) staan grijs: hoe in een
      kaartje? ✘ (klein; voorstel: "komt nog")
- [ ] `app.hoofdmenu`, `app.startscherm` (titel), `app.kiezen`, `app.voorstel`, `app.herhalen_of_verder`:
      ◐ later, apart beslissen (vraag 6).
- [ ] `app.slotscherm` (het slot), `app.oeps` (een fout opgevangen), `app.zeg_het_ons` (opmerking van het kind):
      ◐ als laatste, alleen een kader (vraag 17).

## G. Kind-, winkel- en ouderschermen (als laatste: alleen een kader, vraag 17)
- [ ] `schermen/kinderen.py`: kies een kind, pincode, nieuw kind. ◐ (vraag 17)
- [ ] `schermen/winkel.py` (`AvatarSchermen`, 26 keer `put`): hub, winkel, rek, koop, kast, schermkleuren
      (die thema's moeten de nieuwe rollen krijgen). ◐ (vraag 17)
- [ ] `app.mijn_avatar`, `teken_avatar_menu`, `avatar_links`. ◐ (vraag 17)
- [ ] `schermen/ouder.py` (Ouderdeel, 26 keer menu/lezer/afvink…): toegang, wachtwoord en pin, kinderen, rapporten
      (`kies_periode`, `vraag_datum`, `toon_rapport`, `exporteer`), kalender, antwoorden (+ details), punten, Gemengd
      oefenen, Weergave, pincode, stoppen op slot, alles exporteren, wissen, opmerkingen. ◐ (vraag 17)
- [ ] Weergave (ouderdeel): een nieuwe keuze "rustig / uitgebreid" per kind? ◐ (vraag 3)

## H. Het klokvenster (`venster/`, `terminal/venster.py`)
- [ ] Het venster is hoogstens een kwart van het scherm breed; de terminal houdt zijn tekst links van kolom 60
      (`oefenaar.LINKS`). Met vakken: wat schuift er opzij? ◐ (vraag 21)
- [ ] F2 = de klok in de terminal: dan moet de klok (21 breed) in een vak passen. ◐ (vraag 2)

## I. De kern (wat de vakken nodig hebben; gouden regels 1 en 2)
- [ ] Het vak **Reeks**: al in de kern/opslag (resultaten, punten, op rij). ✔ (beta tekent het)
- [ ] **Vandaag** ("14 van 17 juist"), **Herhaalbak** (`opslag.herhaalbak`), **fris houden**, **laatst geoefend**,
      **percentage juist**: bestaan, maar niet als "regels met rollen" voor een vak. ◐ (één functie in de kern die
      de regels geeft)
- [ ] **Moeilijk voor jou** (denkfouten per onderwerp tellen, uit de foutlog/diagnose): nieuw in de kern. ◐
- [ ] **Stappen** (zinsdelen, vraagstuk): de stappen als regels uit het object/de kern, niet getekend door het
      scherm. ◐
- [ ] **Zo kan het** (na een fout, naast "Jouw klad"): een voorbeeldklad per vraag. `uitwerking` bestaat al voor een
      deel van de onderwerpen; voor welke niet? ◐ (vraag 12)
- [ ] Klad ✔ ✘ per regel bij een object (nu alleen bij een gewoon antwoordvak via `kern/klad.py`): ✔ beta; bevestigen
      (vraag 11).
- [ ] Bewaren: het klad in `extra["klad"]` (geen nieuwe migratie nodig zolang het in `extra` blijft). Nakijken dat
      het rapport en "antwoorden" in het ouderdeel het tonen. ✘ (klein)
- [ ] Instelling "rustig / uitgebreid" (`kern/instellingen.py`). ◐ (vraag 3)
- [ ] De grootte van het venster in het logboek bij het starten (vraag 1). ◐ (aanbevolen)

## J. Tests
- [ ] `tests/test_beta.py`: elk rooster en elke staartdeling past in het vak. → uitbreiden naar **elk object en elk
      model in elk leerjaar past in zijn vak, op 80×24 en op een groter scherm, ook in ASCII**.
- [ ] Tests met klikken op vaste coördinaten (breken zodra iets verschuift): `test_schermen` (7), `test_ouder` (9),
      `test_procenten` (2), `test_gemengd` (2), `test_taal_scherm` (2), `test_taal_werkwoorden` (2),
      `test_hoofdrekenen`, `test_getallen`, `test_stopslot`, `test_cijferen`, `test_menu_architecture`,
      `test_breuken` (elk 1). Beter: klikken op de zone van een actie, niet op (y, x).
- [ ] Tests die schermtekst lezen (meer dan 10 bestanden): nakijken dat ze de tekst nog vinden in een vak.
- [ ] De aapjestest (`test_stabiliteit`, ook in `test_gemengd`, `test_stopslot`, `test_taal_*`): op meer groottes
      draaien (80×24, 100×30, 160×50) en met het klokvenster.
- [ ] `test_architectuur`: een nieuwe regel bewaken: "geen vaste kolom voorbij het vak" of "objecten tekenen alleen
      in hun rechthoek". ✘ (welke regel precies)
- [ ] `docs/tools/scenarios.py` (tmux-scenario's: `scherm_tekst`, `rooster_getallen`, `vul_tabel` lezen het scherm):
      breken; worden toch in het handleidingproject opnieuw gemaakt.

## K. Documenten
- [ ] `docs/architectuur.md`: een stuk "Schermen: vakken en indeling" (vak, indeling, een object krijgt een
      rechthoek, toetsen in de rand, rollen).
- [ ] `CLAUDE.md`: "Alles past in 80×24" wordt "past in 80×24 en groeit mee"; Tab = klad overal.
- [ ] `docs/koers.md`: volgorde tegenover T2 Woordsoorten (vraag 5).
- [ ] `docs/taal.md`: de kleuren per zinsdeel en woordsoort in een vak.
- [ ] `docs/testlijst.md`: een stuk per verbouwd scherm.
- [ ] `CHANGELOG.md`, `VERSIE`, `README.md`: per versie.
- [ ] `docs/handleiding/` + schermafdrukken: in het handleidingproject (niet per versie).
- [ ] `werk/schermen.md`: na elke fase bijwerken.

## L. Van beta naar iedereen
- [ ] De schakelaar `LEERAVONTUUR_BETA=1` en `beta.DOMEINEN = {"Cijferen"}`: per domein uitbreiden, of in één keer?
      ◐ (vraag 14)
- [ ] Twee manieren van tekenen naast elkaar gaat tegen gouden regel 3 in: hoe lang mag dat? ◐ (vraag 14)
- [ ] Platformen: ronde hoeken en de ▀▄-pixels op Windows (conhost, Windows Terminal, PDCurses) en macOS Terminal
      echt bekijken; ASCII-modus als terugval. ✘ (nagaan)
- [ ] Een vergelijking met de vorige versie op een kopie van echte gegevens (afspraak bij een verbouwing).

---

## Open vragen (met de aanbeveling van Claude)
*1 tot 6 staan al in `schermen.md`; hier kort herhaald, 7 tot 24 zijn nieuw uit deze inventaris.*

**22/11, de vader: akkoord met de aanbevelingen van 2, 4, 6, 9, 10, 12–18, 21, 22 en 23.** **Alle vragen zijn beantwoord (22/11).** 1, 3, 5, 11, 19 en 20: zie hieronder.

1. **Beantwoord 22/11:** de zoon heeft een scherm van 1920×1080, en vaak start de vader het programma in een tty
   op Fedora (Ctrl+Alt+F3). Dat is ongeveer **240×67** tekens (lettertype `eurlatgr`, 8×16). Kleinere schermen
   moeten blijven werken (tot 80×24). Gevolgen: zie **M. De tty** en vraag 24.
2. Grote modellen en objecten (getallenlijn 72, balk 52, groepjes 68, klok 21×11, digitaal klokje 33, schatkaart,
   cm²-veld) → **aanbeveling:** zo'n model krijgt de volle breedte links; de klad-kolom schuift eronder of wordt
   smaller; op 80×24 is het klad dan een paar regels onder het model.
3. **Rustig** — **gekozen 22/11 (de vader):** een schakelaar die het kind zelf aan en uit zet als het scherm te druk
   is. Rustig = alleen **Vraag, Antwoord en Klad**; geen vak Tip, geen spiekbrief, geen cijfers. **Alle toetsen
   blijven werken** en staan in de voetregel. **Bevestigd 22/11:** F1 geeft in Rustig toch een tip (even, op de plaats
   van de vraag), zodat Rustig geen hulp wegneemt; de toets is **F3** (F1 = tip, F2 = klok); onthouden per kind
   (een instelling van het kind in `kern/instellingen.py`, via `kern/opslag.py`).
4. Tip-vak vóór F1 → alleen "F1 = tip 1 van 3".
5. **Gekozen 22/11:** T2 nog niet: overslaan, `docs/koers.md` niet aanpassen.
6. Hoofdmenu en titelscherm in vakken → apart beslissen.
7. **Eenheden** is een eigen kopie van de Oefenaar → **aanbeveling:** eerst laten opgaan in de Oefenaar (de tabel
   wordt een invoer-object), dan krijgt het de vakken vanzelf. Anders wordt alles twee keer gebouwd.
   **Gekozen 22/11 (de vader): akkoord.** Een opruimstap vóór de verbouwing; het kind ziet daar niets van.
8. **Vraagstuk** — **gekozen 22/11 (de vader): één werkwijze, de stappen met de pijltjes.** Nu tekent het
   vraagstuk het hele scherm zelf: het verhaal, daaronder de 4 stappen (Lees, Plan, Reken, Controle) als kopjes,
   een eigen klad in stap 3 (hoogstens 8 regels), Tab/Shift-Tab = volgende/vorige stap, eigen tips. Nieuw:
   - het **verhaal** in het Vraag-vak (gegevens aanduiden zoals nu); Plan en Controle ook in dat vak;
   - de **stappen** in een vak **Stappen** rechts (✔ gedaan, ▸ nu), zoals scherm 3 voor zinsdelen;
   - **geen eigen klad meer**: stap 3 Reken gebruikt de klad-kolom; Tab = klad, zoals overal;
   - de tips in het gewone vak **Tip**;
   - **de pijltjes** = naar een andere stap. Een klik werkt overal (een klik op een stap = naar die stap).
   - *Nog uit te werken:* in stap 1 doen de pijltjes al iets (←→ = naar het volgende gegeven, ↓ = naar "wat is
     gevraagd?", nog eens ↓ = naar stap 2). Voorstel: ←→ blijven binnen de stap, **↓ voorbij het laatste in de
     stap = volgende stap, ↑ bovenaan = vorige stap** (zoals nu al van stap 1 naar 2). Zo ook in Plan en Controle.
9. **Objecten met eigen tips** (zinsdelen, werkwoord, speur, keuze) → het object geeft de tekst, het vak Tip tekent
   ze; overal dezelfde plaats en "Tip 1 van n" in de rand.
10. **Tab-botsing**: Tab = klad overal, maar nu is Tab "vrij kleuren" (zinsdelen), "wissel" (werkwoord), "volgende
    stap" (vraagstuk), "volgende rij" (rooster, nu ↓). → per object een andere toets kiezen (voorstel: ↓/↑ of een
    letter die het kind niet typt). Elk geval apart voorleggen.
    **22/11:** het vraagstuk is beslist (vraag 8); zinsdelen, werkwoord en het rooster hebben geen klad, dus houdt
    Tab daar zijn betekenis (akkoord van de vader).
11. **Vervalt (22/11):** de vraag ging over het klad naast het rooster in de beta, en dat gaat weg (vraag 20). Het
    gewone klad kijkt de rekenregels al na, als een rekenmachine (de vader).
12. **"Zo kan het"** na een fout: voor welke onderwerpen bestaat er een voorbeeldklad? → alleen tonen waar de kern
    er een heeft; anders blijft het vak "Wat ging er mis?" alleen.
13. **Spiekbrief op 80×24** (geen plaats) en in een **examen** (geen tip, geen spiekbrief) → op 80×24 blijft F1
    na de laatste tip de spiekbrief over het hele scherm openen; in een examen krijgt de vraag de vrije plaats.
14. **Beta → iedereen**: per domein of in één keer? → per domein achter de schakelaar, en de oude weg pas weg als
    heel Wiskunde over is (dan één codepad).
15. **Menu met 8 à 10 items + kaartje** op 24 rijen → zonder lege regels tussen de items op 80×24; met lege regels
    pas vanaf 30 rijen.
16. **Snelrekenen** → een Vraag-vak, een groot vak Tijd en Reeks; geen klad (het moet snel).
17. **Ouderdeel, kinderkeuze, slot, oeps, opmerkingen, afvinklijst, één-regel-invoer** → als laatste; alleen een kader
    rond de bestaande schermen (zelfde `vak.py`), geen nieuwe indeling.
18. Te klein → de ondergrens blijft 80×24.
19. **Kleuren**: de vraag-band en de rand in de 5 thema's en in de gekochte schermkleuren → de `b_`-rollen worden
    gewone rollen; elk thema nakijken in tmux.
    **De vader 22/11: voorzichtig, elke soort vraag is anders.** Geen band die overal hetzelfde wordt geplakt:
    per soort vraag een eigen, verzorgd ontwerp waar het nodig is. Bv. bij Snelrekenen is het niet echt nodig, bij
    een vraagstuk is het helemaal anders (een verhaal, geen som). Dus: per soort vraag een schets, en pas bouwen
    na akkoord.
20. **Geen klad** — **gekozen 22/11 (de vader): het klad blijft uit waar het vandaag uit staat**; niets aan te
    passen. Het klad is een soort rekenmachine: het kijkt de rekenregels van het kind na. Waar er geen klad is,
    valt de kolom weg en krijgen Vraag, Tip en spiekbrief de plaats.
    Welke onderwerpen nu geen klad hebben (uit `klad` in de kern, 22/11):
    - **Getallen:** Plaatswaarde, Getallenlijn, Afronden, Deelbaarheid.
    - **Hoofdrekenen:** × en : met 10, 100, 1000; Tafels alleen bij uitbreiden (7 × 80), niet bij een tafel uit het
      hoofd; Gemengd (snelrekenen).
    - **Cijferen:** alle vier (het rooster is het rekenwerk). De klad-kolom van de beta gaat weg (de vader 22/11).
    - **Breuken en procenten:** Herkennen, Vergelijken, Vereenvoudigen, Breuk en kommagetal, Honderdveld, Procent,
      breuk en kommagetal.
    - **Meten:** de zeven maten (Eenheden: een eigen scherm zonder klad), Oppervlakte en omtrek.
    - **Tijd:** De klok alleen bij aflezen, zetten en in woorden (wel bij later, vroeger, 24 uur).
    - **Meetkunde:** Schatkaart, Hoeken.
    - **Vraagstukken:** Oplossen heeft een eigen klad (zie 8); Speurneus, Schatten en controleren: geen.
    - **Taal:** Zinsdelen en alle Werkwoordspelling.
    - **Wel klad:** Optellen en aftrekken, Verdubbelen en halveren, Slim × en : (verplicht), Breuk van een getal,
      Breuken optellen en aftrekken, Procent van een getal, Korting en btw, Formules, Tijd, Geld, Snelheid, Schaal.
21. **Klokvenster open** → de rechterkolom (maatje) valt weg; het klad blijft.
22. **Einde van een reeks** (rapport, `na_reeks`) → vakken: Resultaat, Maatje, Wat ging goed / Moeilijk voor jou, Kies.
    Eerst een schets voor de vader.
23. **Werkwoordspelling** (kofschip, bron, gevonden) → nog een schets nodig, zoals scherm 3 voor zinsdelen.
24. **Een groot scherm** (240×67 in de tty, ook een terminal op het hele scherm): alles mee laten groeien geeft een
    vraag van 200 tekens breed. Aanbeveling: de vakken groeien **tot ongeveer 120×40** en staan dan in het midden;
    daarboven alleen meer lucht. Zo blijft het op elk scherm hetzelfde beeld. **Gekozen 22/11 (de vader): akkoord.**

---

## M. De tty (Linux-console, Ctrl+Alt+F3)
- [ ] **De vader 22/11: in de tty werkt vandaag alles perfect** (Fedora 45 gebruikt een nieuwe console). **Daar
      niets aan veranderen.** (Een eerste controle op het oude lettertype `eurlatgr` gaf ontbrekende tekens: dat
      klopt niet voor deze console.)
- [ ] Nieuwe vakken en tekens wel in de tty bekijken voor ze klaar heten (ook ╭╮╰╯ en de kleuren van de band).
- [ ] Een groot scherm (ongeveer 240×67): zie vraag 24.
