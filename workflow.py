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
