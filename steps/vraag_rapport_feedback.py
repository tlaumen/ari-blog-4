from __future__ import annotations

from ari_core.models import DataModel, Table
from ari_core.prompting import confirm, prompt, ui
from ari_core.workflow.step import Product, Requirement, Step, StepContext

from .helpers.document_viewer import DocumentViewer
from .helpers.rapport_generator import genereer_rapport
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
        opmerking = prompt(
            "Welke opmerking wil je meegeven voor de volgende rapportversie?"
        )
        pointers.append(str(opmerking).strip())

        doorgaan = confirm("Nog een opmerking toevoegen?", default=False)
        if not doorgaan:
            break

    return pointers


class VraagRapportFeedbackStep(Step):
    name = "vraag_rapport_feedback"
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
    produces = [
        Product(key="rapport_feedback", dest=Table.WORKFLOW),
        Product(key="geaccepteerd_rapport", dest=Table.WORKFLOW),
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
        ctx["geaccepteerd_rapport"] = GeaccepteerdRapport(
            inhoud_markdown=aangepaste_rapporttekst
        )
