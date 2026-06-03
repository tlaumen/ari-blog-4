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
    requires = [
        Requirement(key="grondprofiel", source=Table.WORKFLOW, model=Grondprofiel)
    ]
    produces = [Product(key="materiaal_parameters", dest=Table.WORKFLOW)]

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
