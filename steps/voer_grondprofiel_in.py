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
