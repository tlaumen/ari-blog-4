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
