from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from .helpers.document_viewer import DocumentViewer
from .helpers.rapport_generator import genereer_rapport
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
        Requirement(
            key="materiaal_parameters", source=Table.WORKFLOW, model=MateriaalParameters
        ),
        Requirement(key="geometrie", source=Table.WORKFLOW, model=Geometrie),
        Requirement(
            key="stabiliteitsresultaat",
            source=Table.WORKFLOW,
            model=StabiliteitsResultaat,
        ),
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
