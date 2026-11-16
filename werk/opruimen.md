# Opruimen: wat eenvoudiger kan

**Status:** gebouwd (16/11/2026, "actie" van de vader). Een audit van main (60ab177). Niets hiervan verandert wat
het kind ziet. Branches, na elkaar samen te voegen: `opruimen` → `opruimen-a` → `opruimen-b`.

## Gedaan (branch `opruimen`)
- Zes definities weg die nergens gebruikt werden (elke naam stond maar één keer in de repo, bij de definitie):
  `klad.OP_NAAM`, `klad.lees_klad`, `cijferen._uit_cijfers`, `meetkunde.hoek_soort`, `procenten.STRATEGIE`,
  `winkel.straf_tekst`. Eerst nagebootst (de volledige suite met die namen uit het geheugen gehaald: 595 OK).
- CLAUDE.md van 304 naar ±110 regels; de details woord voor woord naar `docs/architectuur.md`.

## Wat de audit vond (met de aanbeveling)
1. **Dezelfde tip-code twee keer.** `terminal/zinsdelen.py` en `terminal/werkwoord.py` hebben ±30 dezelfde regels
   (`tips_op`, `spiekbrief_bekeken`, `hulp`, `rijen`, het einde van `volgende_tip`, `tweede_kans`, `spiekbrief_aan`).
   → Eén klein gedeeld stuk (bv. `terminal/hulpstap.py`). Aanbevolen vóór T2 Woordsoorten, dat er een derde kopie
   van zou maken.
2. **Een nieuw invoer-object = drie plaatsen** in `terminal/oefenaar.py`: `INVOER`, `GEEN_TWEEDE_KANS` en een
   uitzondering in `vraagtekst`. → Twee attributen op het object (`eigen_tweede_kans`, `vraag_is_zin`). Aanbevolen,
   samen met punt 1.
3. **`CU.BINNENKORT` is altijd leeg** (`terminal/curriculum/__init__.py:60`; het was alleen Taal). → Laten staan:
   Frans kan het later gebruiken. Alleen melden.
4. **`onregelmatig` in de leerlijnen van de verleden tijd** (`taal.werkwoordspelling.vt_zwak.json`, `vt_sterk.json`)
   wordt daar niet gelezen (alleen Tegenwoordige tijd gebruikt het, `werkwoorden.py:879`). → Weghalen (2 regels per
   leerjaar); de leerlijn-test bewaakt het.
5. **`docs/plan.md` is 957 regels**, deels vervangen door `docs/koers.md` en `werk/`. → Inkorten tot de tabellen
   "Klaar" en "Nog te doen"; de oude fasebeschrijvingen staan al in de PR's en de CHANGELOG.

**Niet dood, ook al lijkt het zo:** `_alles_juist`, `_rekenfout`, `_denkfout` in `vraagstukken.py` worden met
`getattr(self, "_" + soort)` opgeroepen (regel 1213).

## Fasen
- A (`opruimen-a`): punt 1 + 2. `terminal/stappenhulp.py` (`StappenHulp`); `geen_tweede_kans` en `vraag_is_zin` op
  de objecten; `tests/test_invoer_objecten.py` bewaakt dat de lijst en `vraagtekst` hetzelfde blijven. tmux: F1 tip 1,
  tip 2, spiekbrief, Esc, weer tip 1 in Zinsdelen en Werkwoordspelling.
- B (`opruimen-b`): punt 4 + 5.

**Anders dan afgesproken:** `docs/plan.md` is niet tot de twee tabellen ingekort maar van 957 naar 715 regels: alleen
wat verouderd was ging weg (de stand van zaken van 0.23.1, hoofdstuk L met de architectuur en menu's van 0.20, de
structuur van 0.20). De hoofdstukken over Frans, Avontuur, de winkel, publiceren … zijn nog de plannen voor later en
bleven staan. Punt 3 (`BINNENKORT`) bleef zoals aanbevolen.
