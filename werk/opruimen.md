# Opruimen: wat eenvoudiger kan

**Status:** in overleg. Een audit van main (60ab177, 16/11/2026). Deel 1 is gedaan (branch `opruimen`); de rest wacht
op "actie". Niets hiervan verandert wat het kind ziet.

## Gedaan (branch `opruimen`)
- Zes definities weg die nergens gebruikt werden (elke naam stond maar één keer in de repo, bij de definitie):
  `klad.OP_NAAM`, `klad.lees_klad`, `cijferen._uit_cijfers`, `meetkunde.hoek_soort`, `procenten.STRATEGIE`,
  `winkel.straf_tekst`. Eerst nagebootst (de volledige suite met die namen uit het geheugen gehaald: 595 OK).
- CLAUDE.md van 304 naar ±110 regels; de details woord voor woord naar `docs/architectuur.md`.

## Open (aanbeveling van Claude bij elk punt)
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

## Fasen (pas na "actie")
- A: punt 1 + 2 (één PR, tests + tmux van Zinsdelen en Werkwoordspelling).
- B: punt 4 + 5 (één PR, alleen data en docs).
