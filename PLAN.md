# PLAN — Implementatie Deel 1 (runnable tutorial)

## Doel
Een werkende ARI workflow bouwen voor Deel 1 van `4.md`, met:
1. gestructureerde invoer,
2. deterministische stabiliteitsberekening via `xslope`,
3. AI-conceptrapport,
4. gebruikersfeedback + geaccepteerde rapportversie,
5. daarna relevante code terugplaatsen in `4.md`.

---

## Kaders (vastgezet)
- Gebruik **`xslope`** (niet `pyslope`).
- **Geen Excel-interface** voor geometrie; we bouwen `slope_data` direct uit workflowdata.
- DataModels blijven in de bijbehorende step-bestanden (geen aparte `models/` map).
- `Grondlaag`: `bovenkant`, `onderkant`, `materiaal`.
- Validatie laag: `onderkant < bovenkant`.
- `Grondprofiel` bevat verplicht: `grondwaterstand_nap`.
- Geometrie invoer: alleen maaiveldpunten (`x`, `z`).
- `xslope` cirkel-seeding:
  - `Yo` afleiden uit `z_min/z_max`.
  - `R` afleiden uit `Yo`, `z_min`, `z_max` (niet op basis van x-lengte).

---

## Implementatieplan (stap voor stap)

## Stap 1 — Structuur & contracts vastleggen
**Doel:** project klaarzetten zodat alle volgende stappen eenduidig kunnen coderen.

### Acties
- Maak helper-map en step-bestanden:
  - `helpers/xslope_engine.py`
  - `helpers/rapport_generator.py`
  - `steps/voer_grondprofiel_in.py`
  - `steps/voer_parameters_in.py`
  - `steps/laad_geometrie_uit_excel.py` *(naam blijft uit blog-consistentie; inhoud wordt prompt-based geometrie-invoer)*
  - `steps/bereken_stabiliteit.py`
  - `steps/genereer_rapport.py`
  - `steps/vraag_rapport_feedback.py`
- Leg per step vast:
  - `requires`
  - `produces`
  - storage (`Table.PROJECT` vs `Table.WORKFLOW`)
- Vervang `example` segment in `workflow.py` door `stabiliteitsrapportage` keten.

### Oplevering
- Bestandsstructuur en lege/skeleton classes staan klaar.
- Segment draait en toont de juiste flow (zelfs als execute nog TODO is).

### Reviewmoment
- Jij checkt of namen/flow exact aansluiten op de tutorialtekst.

---

## Stap 2 — Step 1 implementeren: grondprofiel
**Doel:** grondlagen + grondwaterstand robuust inlezen.

### Acties
- DataModels in `steps/voer_grondprofiel_in.py`:
  - `Grondlaag`
  - `Grondprofiel`
- `VoerGrondprofielInStep.execute()`:
  - vraag aantal lagen,
  - vraag per laag: `bovenkant`, `onderkant`, `materiaal`,
  - vraag `grondwaterstand_nap`,
  - valideer `onderkant < bovenkant` en niet-lege materiaalnaam,
  - sla op als `ctx["grondprofiel"]` (`Table.PROJECT`).

### Oplevering
- Step 1 volledig werkend en handmatig testbaar.

### Reviewmoment
- Samen checken of UX/validaties precies goed zijn.

---

## Stap 3 — Step 2 implementeren: parameters
- Models: `MateriaalParameters`, `RekenInstellingen`.
- Invoer + validatie (waardenbereiken).
- Opslaan in `Table.PROJECT`.

---

## Stap 4 — Step 3 implementeren: geometrie-invoer (prompt-based)
- Model: `GeometriePunt`, `Geometrie`.
- Invoer aantal punten + per punt `x`, `z`.
- Sorteren op `x`, minstens 2 unieke punten.
- Opslaan als `ctx["geometrie"]` in `Table.PROJECT`.

---

## Stap 5 — Helper bouwen: `helpers/xslope_engine.py`
- `build_slope_data(...)`:
  - maak `ground_surface`, `profile_lines`, `materials`, `piezo_line` uit workflowdata,
  - vertaal NAP grondwaterstand naar piezolijn,
  - genereer `circles` met Yo/R-regels op basis van z-bereik.
- `run_analysis(...)`:
  - run `xslope.search.circular_search(...)`,
  - haal maatgevende FS/cirkel/resultaat op,
  - return gestandaardiseerde output.

---

## Stap 6 — Step 4 implementeren: bereken stabiliteit
- Model: `StabiliteitsResultaat`.
- Lees requirements uit context.
- Roep `xslope_engine` helper aan.
- Sla `stabiliteitsresultaat` op in `Table.WORKFLOW`.

---

## Stap 7 — Helper bouwen: `helpers/rapport_generator.py`
- Functie die uit gestructureerde input een conceptrapporttekst maakt.
- Eerste versie mag template-based zijn (deterministisch) met optionele LLM-haak.

---

## Stap 8 — Step 5 implementeren: genereer rapport
- Model: `ConceptRapport`.
- Verzamel contextdata.
- Roep rapport-helper aan.
- Sla op in `Table.WORKFLOW`.

---

## Stap 9 — Step 6 implementeren: feedback + accepted version
- Models: `RapportFeedback`, `GeaccepteerdRapport`.
- Flow:
  - concept tonen,
  - akkoord?
  - zo niet: feedback en/of aangepaste tekst vragen,
  - accepted tekst bepalen.
- Opslaan in `Table.PROJECT`.

---

## Stap 10 — Integratie, runnen, fouten fixen
- E2E run via `python main.py`.
- Contractfouten fixen (missing products, type mismatches, keys/tables).
- Minimaal 1 volledige succesvolle run documenteren.

---

## Stap 11 — Relevante code terugplaatsen in `4.md`
- Alleen kernsnippets toevoegen:
  - execute van Step 1, Step 4, Step 5, Step 6,
  - kern van `xslope_engine` mapping.
- Blog leesbaar houden (helpers niet volledig dumpen).

---

## Volgorde van uitvoering
1. Stap 1 (nu)
2. Stap 2
3. Stap 3
4. Stap 4
5. Stap 5
6. Stap 6
7. Stap 7
8. Stap 8
9. Stap 9
10. Stap 10
11. Stap 11

---

## Startstatus
- PLAN opgesteld.
- **Nu starten met Stap 1.**
