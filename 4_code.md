---
title: Van terminal naar team: bouw je eerste AI workflow met ARI (v2)
author: Tom Laumen
date: juni 2026
read_time: 14 min lezen
series: AI met een bouwhelm op
---

> In deze v2 staat de volledige Deel 1 workflowlogica uitgewerkt.  
> Alle step-logica staat hieronder; alleen helper-implementaties staan niet volledig in dit document.

## Overzicht workflow

```text
VoerGrondprofielInStep
→ VoerParametersInStep
→ LaadGeometrieStep
→ BerekenStabiliteitStep
→ GenereerRapportStep
→ VraagRapportFeedbackStep
```

---

## Dependencies

```bash
uv add ari-core xslope tabulate openai anthropic
```

---

## workflow.py

```python
"""Workflow segment definitions for Deel 1 stabiliteitsrapportage."""

from ari_core.workflow.registry import SegmentRegistry
from ari_core.workflow.segment import Segment

from steps.bereken_stabiliteit import BerekenStabiliteitStep
from steps.genereer_rapport import GenereerRapportStep
from steps.laad_geometrie import LaadGeometrieStep
from steps.voer_grondprofiel_in import VoerGrondprofielInStep
from steps.voer_parameters_in import VoerParametersInStep
from steps.vraag_rapport_feedback import VraagRapportFeedbackStep

registry = SegmentRegistry()

registry.register(
    Segment(
        name="stabiliteitsrapportage",
        description="Voer grondgegevens in, bereken stabiliteit en rond een rapport af",
        steps=[
            VoerGrondprofielInStep,
            VoerParametersInStep,
            LaadGeometrieStep,
            BerekenStabiliteitStep,
            GenereerRapportStep,
            VraagRapportFeedbackStep,
        ],
        requires=[],
    )
)
```

---

## helpers/document_viewer.py

```python
from __future__ import annotations

from html import escape


def markdown_to_html(markdown: str) -> str:
    html: list[str] = []
    in_list = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()

        if not line:
            if in_list:
                html.append("</ul>")
                in_list = False
            continue

        if line.startswith("# "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{escape(line[2:])}</li>")
        else:
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{escape(line)}</p>")

    if in_list:
        html.append("</ul>")

    return "\n".join(html)


class DocumentViewer:
    def __init__(self, title: str, markdown: str) -> None:
        self.title = title
        self.markdown = markdown

    def render_html(self) -> str:
        title = escape(self.title)
        body = markdown_to_html(self.markdown)
        return f"""
        <div style='font-family: sans-serif; max-width: 900px; margin: 0 auto; line-height: 1.5;'>
          <h2>{title}</h2>
          <article style='border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: #fafafa;'>
            {body}
          </article>
          <button id='verder' style='margin-top: 12px;'>Verder</button>
        </div>
        <script>
          document.getElementById('verder').addEventListener('click', function () {{
            window.parent.postMessage({{ value: true, summary: 'Document bekeken' }}, '*');
          }});
        </script>
        """
```

---

## Stap 1 — Grondprofiel invoeren

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import confirm, prompt
from ari_core.workflow.step import Product, Step, StepContext


def as_float(value: object) -> float:
    return float(str(value).replace(",", "."))


class Grondlaag(DataModel):
    bovenkant: float
    onderkant: float
    materiaal: str


class Grondprofiel(DataModel):
    lagen: list[Grondlaag]
    grondwaterstand_nap: float


class VoerGrondprofielInStep(Step):
    name = "voer_grondprofiel_in"
    requires = []
    produces = [Product(key="grondprofiel", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        maaiveld_nap = prompt("Wat is het maaiveldniveau (NAP)?")

        lagen: list[Grondlaag] = []
        huidige_bovenkant = as_float(maaiveld_nap)

        while True:
            laag_nr = len(lagen) + 1
            onderkant = prompt(f"Laag {laag_nr} - onderkant (NAP):")
            materiaal = prompt(f"Laag {laag_nr} - materiaal:")

            lagen.append(
                Grondlaag(
                    bovenkant=huidige_bovenkant,
                    onderkant=as_float(onderkant),
                    materiaal=str(materiaal).strip(),
                )
            )

            huidige_bovenkant = as_float(onderkant)

            doorgaan = confirm("Nog een laag toevoegen?", default=False)
            if not doorgaan:
                break

        grondwaterstand_nap = prompt("Wat is de grondwaterstand (NAP)?")

        ctx["grondprofiel"] = Grondprofiel(
            lagen=lagen,
            grondwaterstand_nap=as_float(grondwaterstand_nap),
        )
```

---

## Stap 2 — Materiaalparameters per grondsoort

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from steps.voer_grondprofiel_in import Grondprofiel, as_float


class GrondsoortParameters(DataModel):
    volumiek_gewicht_kN_m3: float
    cohesie_kPa: float
    wrijvingshoek_graden: float


class MateriaalParameters(DataModel):
    per_materiaal: dict[str, GrondsoortParameters]


class VoerParametersInStep(Step):
    name = "voer_parameters_in"
    requires = [Requirement(key="grondprofiel", source=Table.WORKFLOW, model=Grondprofiel)]
    produces = [Product(key="materiaal_parameters", dest=Table.PROJECT)]

    def execute(self, ctx: StepContext) -> None:
        grondprofiel: Grondprofiel = ctx["grondprofiel"]
        materialen = sorted({laag.materiaal for laag in grondprofiel.lagen})

        per_materiaal: dict[str, GrondsoortParameters] = {}

        for naam in materialen:
            gamma = prompt(f"{naam} - volumiek gewicht (kN/m3):")
            cohesie = prompt(f"{naam} - cohesie (kPa):")
            phi = prompt(f"{naam} - wrijvingshoek (graden):")

            per_materiaal[naam] = GrondsoortParameters(
                volumiek_gewicht_kN_m3=as_float(gamma),
                cohesie_kPa=as_float(cohesie),
                wrijvingshoek_graden=as_float(phi),
            )

        ctx["materiaal_parameters"] = MateriaalParameters(per_materiaal=per_materiaal)
```

---

## Stap 3 — Geometrie als puntenlijst

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import prompt
from ari_core.workflow.step import Product, Step, StepContext

from steps.voer_grondprofiel_in import as_float


class GeometriePunt(DataModel):
    x: float
    z: float


class Geometrie(DataModel):
    punten: list[GeometriePunt]


def parse_geometriepunten(value: object) -> list[GeometriePunt]:
    punten = []
    for paar in str(value).split(";"):
        x, z = paar.split(",")
        punten.append(GeometriePunt(x=as_float(x), z=as_float(z)))

    return sorted(punten, key=lambda p: p.x)


class LaadGeometrieStep(Step):
    name = "laad_geometrie"
    requires = []
    produces = [Product(key="geometrie", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        punten = prompt(
            "Geef maaiveldpunten als x,z-paren gescheiden door puntkomma's. "
            "Voorbeeld: 0,8.0; 10,7.5; 20,5.0"
        )

        ctx["geometrie"] = Geometrie(
            punten=parse_geometriepunten(punten)
        )
```

---

## Stap 4 — Stabiliteit berekenen

De rekenlogica zit in helpers:

- `build_slope_data(...)`: zet workflowdata om naar xslope-input.
- `run_analysis(...)`: draait de xslope-analyse en geeft de maatgevende resultaten terug.

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from helpers.xslope_engine import build_slope_data, run_analysis
from steps.laad_geometrie import Geometrie
from steps.voer_grondprofiel_in import Grondprofiel
from steps.voer_parameters_in import MateriaalParameters


class StabiliteitsResultaat(DataModel):
    veiligheidsfactor: float
    maatgevende_cirkel_x0: float
    maatgevende_cirkel_y0: float
    maatgevende_cirkel_r: float


class SlipcircleViewerComponent:
    def __init__(self, image_base64: str, veiligheidsfactor: float) -> None:
        self.image_base64 = image_base64
        self.veiligheidsfactor = veiligheidsfactor

    def render_html(self) -> str:
        return f"""
        <div style='font-family: sans-serif; max-width: 1000px; margin: 0 auto;'>
          <h3>Maatgevende glijcirkel</h3>
          <p>Veiligheidsfactor (Bishop): <strong>{self.veiligheidsfactor:.3f}</strong></p>
          <img
            src='data:image/png;base64,{self.image_base64}'
            alt='Maatgevende glijcirkel'
            style='max-width: 100%; border: 1px solid #ddd; border-radius: 8px;'
          />
          <div style='margin-top: 12px;'>
            <button id='verder'>Verder</button>
          </div>
        </div>
        <script>
          document.getElementById('verder').addEventListener('click', function () {{
            window.parent.postMessage({{ value: true, summary: 'Glijcirkel bekeken' }}, '*');
          }});
        </script>
        """


class BerekenStabiliteitStep(Step):
    name = "bereken_stabiliteit"
    requires = [
        Requirement(key="grondprofiel", source=Table.WORKFLOW, model=Grondprofiel),
        Requirement(key="materiaal_parameters", source=Table.PROJECT, model=MateriaalParameters),
        Requirement(key="geometrie", source=Table.WORKFLOW, model=Geometrie),
    ]
    produces = [Product(key="stabiliteitsresultaat", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        grondprofiel: Grondprofiel = ctx["grondprofiel"]
        materiaal_parameters: MateriaalParameters = ctx["materiaal_parameters"]
        geometrie: Geometrie = ctx["geometrie"]

        slope_data = build_slope_data(
            grondprofiel=grondprofiel,
            materiaal_parameters=materiaal_parameters,
            geometrie=geometrie,
        )
        analyse = run_analysis(slope_data, num_slices=30, include_plot=True)

        plot_base64 = analyse.get("plot_base64")
        if plot_base64:
            ui(SlipcircleViewerComponent(plot_base64, analyse["veiligheidsfactor"]))

        ctx["stabiliteitsresultaat"] = StabiliteitsResultaat(
            veiligheidsfactor=analyse["veiligheidsfactor"],
            maatgevende_cirkel_x0=analyse["maatgevende_cirkel_x0"],
            maatgevende_cirkel_y0=analyse["maatgevende_cirkel_y0"],
            maatgevende_cirkel_r=analyse["maatgevende_cirkel_r"],
        )
```

---

## Stap 5 — Concept rapport

Helper:

- `genereer_rapport(..., feedback_pointers=None)`: maakt een rapporttekst in markdown op basis van de gestructureerde invoer.

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from helpers.document_viewer import DocumentViewer
from helpers.rapport_generator import genereer_rapport
from steps.bereken_stabiliteit import StabiliteitsResultaat
from steps.laad_geometrie import Geometrie
from steps.voer_grondprofiel_in import Grondprofiel
from steps.voer_parameters_in import MateriaalParameters


class ConceptRapport(DataModel):
    titel: str
    inhoud_markdown: str


class GenereerRapportStep(Step):
    name = "genereer_rapport"
    requires = [
        Requirement(key="grondprofiel", source=Table.WORKFLOW, model=Grondprofiel),
        Requirement(key="materiaal_parameters", source=Table.PROJECT, model=MateriaalParameters),
        Requirement(key="geometrie", source=Table.WORKFLOW, model=Geometrie),
        Requirement(key="stabiliteitsresultaat", source=Table.WORKFLOW, model=StabiliteitsResultaat),
    ]
    produces = [Product(key="concept_rapport", dest=Table.WORKFLOW)]

    def execute(self, ctx: StepContext) -> None:
        grondprofiel: Grondprofiel = ctx["grondprofiel"]
        materiaal_parameters: MateriaalParameters = ctx["materiaal_parameters"]
        geometrie: Geometrie = ctx["geometrie"]
        stabiliteitsresultaat: StabiliteitsResultaat = ctx["stabiliteitsresultaat"]

        inhoud = genereer_rapport(
            grondprofiel=grondprofiel,
            materiaal_parameters=materiaal_parameters,
            geometrie=geometrie,
            stabiliteitsresultaat=stabiliteitsresultaat,
            feedback_pointers=None,
        )

        concept_rapport = ConceptRapport(
            titel="Concept stabiliteitsrapport",
            inhoud_markdown=inhoud,
        )

        ui(DocumentViewer(concept_rapport.titel, concept_rapport.inhoud_markdown))

        ctx["concept_rapport"] = concept_rapport
```

---

## Stap 6 — Feedback + finale rapportversie

```python
from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import confirm, prompt, ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from helpers.document_viewer import DocumentViewer
from helpers.rapport_generator import genereer_rapport
from steps.bereken_stabiliteit import StabiliteitsResultaat
from steps.laad_geometrie import Geometrie
from steps.voer_grondprofiel_in import Grondprofiel
from steps.voer_parameters_in import MateriaalParameters


class RapportFeedback(DataModel):
    opmerkingen: list[str]


class GeaccepteerdRapport(DataModel):
    inhoud_markdown: str


def vraag_pointers() -> list[str]:
    pointers: list[str] = []

    while True:
        opmerking = prompt("Welke opmerking wil je meegeven voor de volgende rapportversie?")
        pointers.append(str(opmerking).strip())

        doorgaan = confirm("Nog een opmerking toevoegen?", default=False)
        if not doorgaan:
            break

    return pointers


class VraagRapportFeedbackStep(Step):
    name = "vraag_rapport_feedback"
    requires = [
        Requirement(key="grondprofiel", source=Table.WORKFLOW, model=Grondprofiel),
        Requirement(key="materiaal_parameters", source=Table.PROJECT, model=MateriaalParameters),
        Requirement(key="geometrie", source=Table.WORKFLOW, model=Geometrie),
        Requirement(key="stabiliteitsresultaat", source=Table.WORKFLOW, model=StabiliteitsResultaat),
    ]
    produces = [
        Product(key="rapport_feedback", dest=Table.PROJECT),
        Product(key="geaccepteerd_rapport", dest=Table.PROJECT),
    ]

    def execute(self, ctx: StepContext) -> None:
        grondprofiel: Grondprofiel = ctx["grondprofiel"]
        materiaal_parameters: MateriaalParameters = ctx["materiaal_parameters"]
        geometrie: Geometrie = ctx["geometrie"]
        stabiliteitsresultaat: StabiliteitsResultaat = ctx["stabiliteitsresultaat"]

        pointers = vraag_pointers()

        aangepaste_rapporttekst = genereer_rapport(
            grondprofiel=grondprofiel,
            materiaal_parameters=materiaal_parameters,
            geometrie=geometrie,
            stabiliteitsresultaat=stabiliteitsresultaat,
            feedback_pointers=pointers,
        )

        ui(DocumentViewer("Aangepast stabiliteitsrapport", aangepaste_rapporttekst))

        ctx["rapport_feedback"] = RapportFeedback(opmerkingen=pointers)
        ctx["geaccepteerd_rapport"] = GeaccepteerdRapport(inhoud_markdown=aangepaste_rapporttekst)
```

---

## Runnen

```bash
uv run python main.py
```

---

## Opmerking over helpers

De volledige helperimplementaties staan in:

- `helpers/xslope_engine.py`
- `helpers/rapport_generator.py`
- `helpers/document_viewer.py`

Die zijn bewust buiten deze pagina gehouden om de tutorial op step-logica te focussen.
