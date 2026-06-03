from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from .helpers.xslope_engine import build_slope_data, run_analysis
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
        Requirement(
            key="materiaal_parameters", source=Table.WORKFLOW, model=MateriaalParameters
        ),
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
