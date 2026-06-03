from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

module_path = Path(__file__).resolve().parents[1] / "steps" / "helpers" / "xslope_engine.py"
spec = importlib.util.spec_from_file_location("xslope_engine", module_path)
assert spec is not None
xslope_engine = importlib.util.module_from_spec(spec)
sys.modules["xslope_engine"] = xslope_engine
assert spec.loader is not None
spec.loader.exec_module(xslope_engine)
build_slope_data = xslope_engine.build_slope_data


def _geometry() -> SimpleNamespace:
    return SimpleNamespace(
        punten=[
            SimpleNamespace(x=0, z=0),
            SimpleNamespace(x=10, z=0),
            SimpleNamespace(x=15, z=5),
            SimpleNamespace(x=20, z=5),
            SimpleNamespace(x=25, z=0),
            SimpleNamespace(x=30, z=0),
        ]
    )


def _material_parameters() -> SimpleNamespace:
    return SimpleNamespace(
        per_materiaal={
            "veen": SimpleNamespace(
                volumiek_gewicht_kN_m3=12,
                cohesie_kPa=2,
                wrijvingshoek_graden=15,
            ),
            "zand": SimpleNamespace(
                volumiek_gewicht_kN_m3=18,
                cohesie_kPa=0,
                wrijvingshoek_graden=30,
            ),
            "klei": SimpleNamespace(
                volumiek_gewicht_kN_m3=17,
                cohesie_kPa=5,
                wrijvingshoek_graden=20,
            ),
        }
    )


def test_build_slope_data_daylighting_layer_tops() -> None:
    geometrie = _geometry()
    grondprofiel = SimpleNamespace(
        lagen=[
            SimpleNamespace(bovenkant=6, onderkant=3, materiaal="zand"),
            SimpleNamespace(bovenkant=3, onderkant=-2, materiaal="klei"),
            SimpleNamespace(bovenkant=-2, onderkant=-10, materiaal="zand"),
        ],
        grondwaterstand_nap=0,
    )
    materiaal_parameters = _material_parameters()

    slope_data = build_slope_data(
        grondprofiel=grondprofiel,
        materiaal_parameters=materiaal_parameters,
        geometrie=geometrie,
    )

    assert [
        slope_data["materials"][line["mat_id"]]["name"]
        for line in slope_data["profile_lines"]
    ] == ["zand", "klei", "zand"]
    assert slope_data["profile_lines"][0]["coords"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (15.0, 5.0),
        (20.0, 5.0),
        (25.0, 0.0),
        (30.0, 0.0),
    ]
    assert slope_data["profile_lines"][1]["coords"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (13.0, 3.0),
        (22.0, 3.0),
        (25.0, 0.0),
        (30.0, 0.0),
    ]
    assert slope_data["profile_lines"][2]["coords"] == [
        (0.0, -2.0),
        (30.0, -2.0),
    ]


def test_build_slope_data_removes_layers_above_geometry_top_and_caps_first_remaining_layer() -> None:
    grondprofiel = SimpleNamespace(
        lagen=[
            SimpleNamespace(bovenkant=8, onderkant=6, materiaal="veen"),
            SimpleNamespace(bovenkant=6, onderkant=3, materiaal="zand"),
            SimpleNamespace(bovenkant=3, onderkant=-2, materiaal="klei"),
        ],
        grondwaterstand_nap=0,
    )

    slope_data = build_slope_data(
        grondprofiel=grondprofiel,
        materiaal_parameters=_material_parameters(),
        geometrie=_geometry(),
    )

    assert [
        slope_data["materials"][line["mat_id"]]["name"]
        for line in slope_data["profile_lines"]
    ] == ["zand", "klei"]
    assert slope_data["profile_lines"][0]["coords"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (15.0, 5.0),
        (20.0, 5.0),
        (25.0, 0.0),
        (30.0, 0.0),
    ]
    assert slope_data["profile_lines"][1]["coords"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (13.0, 3.0),
        (22.0, 3.0),
        (25.0, 0.0),
        (30.0, 0.0),
    ]


def test_build_slope_data_raises_first_layer_top_to_geometry_top_when_profile_starts_below_zmax() -> None:
    grondprofiel = SimpleNamespace(
        lagen=[
            SimpleNamespace(bovenkant=3, onderkant=-2, materiaal="klei"),
            SimpleNamespace(bovenkant=-2, onderkant=-10, materiaal="zand"),
        ],
        grondwaterstand_nap=0,
    )

    slope_data = build_slope_data(
        grondprofiel=grondprofiel,
        materiaal_parameters=_material_parameters(),
        geometrie=_geometry(),
    )

    assert [
        slope_data["materials"][line["mat_id"]]["name"]
        for line in slope_data["profile_lines"]
    ] == ["klei", "zand"]
    assert slope_data["profile_lines"][0]["coords"] == [
        (0.0, 0.0),
        (10.0, 0.0),
        (15.0, 5.0),
        (20.0, 5.0),
        (25.0, 0.0),
        (30.0, 0.0),
    ]
    assert slope_data["profile_lines"][1]["coords"] == [
        (0.0, -2.0),
        (30.0, -2.0),
    ]


def test_build_slope_data_raises_if_all_layers_are_above_geometry_top() -> None:
    grondprofiel = SimpleNamespace(
        lagen=[
            SimpleNamespace(bovenkant=8, onderkant=6, materiaal="veen"),
        ],
        grondwaterstand_nap=0,
    )

    with pytest.raises(ValueError, match="Geen grondlagen over"):
        build_slope_data(
            grondprofiel=grondprofiel,
            materiaal_parameters=_material_parameters(),
            geometrie=_geometry(),
        )
