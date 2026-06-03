from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import matplotlib
from shapely.geometry import LineString, MultiPolygon, Polygon
from xslope.search import circular_search

matplotlib.use("Agg")
from xslope.plot import plot_solution

if TYPE_CHECKING:
    from steps.laad_geometrie import Geometrie
    from steps.voer_grondprofiel_in import Grondprofiel
    from steps.voer_parameters_in import MateriaalParameters


@dataclass(frozen=True)
class _NormalizedLayer:
    bovenkant: float
    onderkant: float
    materiaal: str


def _to_sorted_ground_coords(geometrie: Geometrie) -> list[tuple[float, float]]:
    coords = sorted([(float(p.x), float(p.z)) for p in geometrie.punten], key=lambda t: t[0])
    if len(coords) < 2:
        raise ValueError("Geometrie moet minimaal 2 punten bevatten.")

    xs = [x for x, _ in coords]
    if len(set(xs)) != len(xs):
        raise ValueError("Geometrie bevat dubbele x-waarden; gebruik strikt oplopende unieke x.")

    ground_line = LineString(coords)
    if not ground_line.is_simple:
        raise ValueError("Geometrie is ongeldig (zelf-intersectie).")

    return coords


def _build_geometry_template(ground_coords: list[tuple[float, float]]) -> Polygon:
    x_min = ground_coords[0][0]
    x_max = ground_coords[-1][0]
    z_max = max(z for _, z in ground_coords)
    cap_z = z_max + 1.0

    template_coords = [(x_min, cap_z), *ground_coords, (x_max, cap_z), (x_min, cap_z)]
    template = Polygon(template_coords)

    if not template.is_valid:
        raise ValueError("Geometrie-template polygon is ongeldig.")
    if template.is_empty:
        raise ValueError("Geometrie-template polygon is leeg.")

    return template


def _select_main_polygon(diff_geom) -> Polygon:
    if diff_geom.is_empty:
        raise ValueError("Leeg resultaat bij bepalen van laaggrens.")

    if isinstance(diff_geom, Polygon):
        return diff_geom

    if isinstance(diff_geom, MultiPolygon):
        parts = sorted(diff_geom.geoms, key=lambda g: g.area, reverse=True)
        main = parts[0]
        for extra in parts[1:]:
            z_min, z_max = extra.bounds[1], extra.bounds[3]
            if (z_max - z_min) >= 0.1:
                raise ValueError("Laaggrens resulteert in meerdere betekenisvolle polygonen; invoer controleren.")
        return main

    raise ValueError(f"Onverwacht geometrie-type bij laaggrens: {diff_geom.geom_type}")


def _extract_top_boundary_from_polygon(poly: Polygon, top_z: float, bottom_z: float) -> list[tuple[float, float]]:
    eps = 1e-8
    pts = list(poly.exterior.coords)

    # remove fake-bottom points
    filtered = [(float(x), float(z)) for x, z in pts if abs(float(z) - bottom_z) > eps]
    if len(filtered) < 2:
        return []

    # take top envelope by x (handles vertical sides / duplicate x)
    envelope: dict[float, float] = {}
    for x, z in filtered:
        envelope[x] = max(z, envelope.get(x, float("-inf")))

    coords = sorted(envelope.items(), key=lambda t: t[0])
    if len(coords) < 2:
        return []

    # clip tiny floating noise around top_z
    snapped = [(x, top_z if abs(z - top_z) < 1e-8 else z) for x, z in coords]
    return snapped


def _build_layer_top_boundary(
    *,
    ground_coords: list[tuple[float, float]],
    geometry_template: Polygon,
    top_z: float,
) -> list[tuple[float, float]]:
    x_min = ground_coords[0][0]
    x_max = ground_coords[-1][0]
    bottom_z = top_z - 1000.0

    boundary_poly = Polygon([
        (x_min, top_z),
        (x_max, top_z),
        (x_max, bottom_z),
        (x_min, bottom_z),
        (x_min, top_z),
    ])

    if not boundary_poly.is_valid:
        raise ValueError("Boundary polygon is ongeldig.")

    diff = boundary_poly.difference(geometry_template)
    main_poly = _select_main_polygon(diff)
    top_boundary = _extract_top_boundary_from_polygon(main_poly, top_z=top_z, bottom_z=bottom_z)

    if len(top_boundary) < 2:
        # Fallback no-intersection behavior
        return [(x_min, top_z), (x_max, top_z)]

    return top_boundary


def _normalize_layers_to_geometry_top(lagen: list, z_max: float) -> list[_NormalizedLayer]:
    normalized = [
        _NormalizedLayer(
            bovenkant=float(laag.bovenkant),
            onderkant=float(laag.onderkant),
            materiaal=str(laag.materiaal).strip(),
        )
        for laag in lagen
        if float(laag.onderkant) <= z_max
    ]

    if not normalized:
        raise ValueError("Geen grondlagen over binnen de geometrie na afkappen op z_max.")

    first = normalized[0]
    normalized[0] = _NormalizedLayer(
        bovenkant=float(z_max),
        onderkant=first.onderkant,
        materiaal=first.materiaal,
    )

    return normalized


def _build_materials_and_map(materiaal_parameters: MateriaalParameters) -> tuple[list[dict], dict[str, int]]:
    materials: list[dict] = []
    mat_id_by_name: dict[str, int] = {}

    for idx, (naam, p) in enumerate(materiaal_parameters.per_materiaal.items()):
        mat_id_by_name[naam] = idx
        materials.append(
            {
                "name": naam,
                "gamma": float(p.volumiek_gewicht_kN_m3),
                "option": "mc",
                "c": float(p.cohesie_kPa),
                "phi": float(p.wrijvingshoek_graden),
                "cp": 0.0,
                "r_elev": 0.0,
                "d": 0.0,
                "psi": 0.0,
                "u": "none",
                "sigma_gamma": 0.0,
                "sigma_c": 0.0,
                "sigma_phi": 0.0,
                "sigma_cp": 0.0,
                "sigma_d": 0.0,
                "sigma_psi": 0.0,
                "k1": 0.0,
                "k2": 0.0,
                "alpha": 0.0,
                "kr0": 0.0,
                "h0": 0.0,
                "E": 0.0,
                "nu": 0.0,
            }
        )

    if not materials:
        raise ValueError("Geen materiaalparameters beschikbaar.")

    return materials, mat_id_by_name


def _build_circles(ground_coords: list[tuple[float, float]]) -> list[dict]:
    x_min = ground_coords[0][0]
    x_max = ground_coords[-1][0]
    z_vals = [z for _, z in ground_coords]
    z_min = min(z_vals)
    z_max = max(z_vals)

    L = x_max - x_min
    H = max(z_max - z_min, 1.0)

    x_fracs = [0.35, 0.50, 0.65]
    y_fracs = [0.25, 0.75, 1.50]
    r_fracs = [1.05, 1.35, 1.80]

    circles: list[dict] = []
    for xf in x_fracs:
        xo = x_min + xf * L
        for yf in y_fracs:
            yo = z_max + yf * H
            r_base = yo - z_min
            for rf in r_fracs:
                r = rf * r_base
                circles.append({
                    "Xo": float(xo),
                    "Yo": float(yo),
                    "Depth": float(yo - r),
                    "R": float(r),
                })

    return circles


def build_slope_data(
    grondprofiel: Grondprofiel,
    materiaal_parameters: MateriaalParameters,
    geometrie: Geometrie,
) -> dict:
    ground_coords = _to_sorted_ground_coords(geometrie)
    geometry_template = _build_geometry_template(ground_coords)

    materials, mat_id_by_name = _build_materials_and_map(materiaal_parameters)

    x_min = ground_coords[0][0]
    x_max = ground_coords[-1][0]
    z_vals = [z for _, z in ground_coords]
    z_min = min(z_vals)
    z_max = max(z_vals)
    H = max(z_max - z_min, 1.0)
    L = x_max - x_min

    lagen = _normalize_layers_to_geometry_top(grondprofiel.lagen, z_max)

    profile_lines: list[dict] = []
    for i, laag in enumerate(lagen):
        mat_naam = laag.materiaal.strip()
        if mat_naam not in mat_id_by_name:
            raise ValueError(f"Geen parameters gevonden voor materiaal '{mat_naam}'.")

        if i == 0:
            coords = ground_coords
        else:
            coords = _build_layer_top_boundary(
                ground_coords=ground_coords,
                geometry_template=geometry_template,
                top_z=float(laag.bovenkant),
            )

        profile_lines.append({
            "coords": coords,
            "mat_id": mat_id_by_name[mat_naam],
        })

    circles = _build_circles(ground_coords)

    x_pad = max(0.1 * L, 1.0)
    gw = float(grondprofiel.grondwaterstand_nap)

    return {
        "ground_surface": LineString(ground_coords),
        "profile_lines": profile_lines,
        "materials": materials,
        "gamma_water": 9.81,
        "tcrack_depth": 0.0,
        "tcrack_water": 0.0,
        "k_seismic": 0.0,
        "max_depth": float(z_min - 2.0 * H),
        "piezo_line": [(x_min - x_pad, gw), (x_max + x_pad, gw)],
        "piezo_line2": [],
        "dloads": [],
        "dloads2": [],
        "reinforce_lines": [],
        "pile_lines": [],
        "mesh": None,
        "circles": circles,
    }


def _render_plot_solution_base64(slope_data: dict, best_result: dict) -> str:
    import matplotlib.pyplot as plt

    open_before = set(plt.get_fignums())

    original_show = plt.show
    plt.show = lambda *args, **kwargs: None
    try:
        plot_solution(
            slope_data,
            slice_df=best_result["slices"],
            failure_surface=best_result["failure_surface"],
            results=best_result["solver_result"],
            save_png=False,
        )
    finally:
        plt.show = original_show

    open_after = list(set(plt.get_fignums()) - open_before)
    if open_after:
        fig = plt.figure(open_after[-1])
    else:
        fig = plt.gcf()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode("ascii")


def run_analysis(slope_data: dict, *, num_slices: int = 30, include_plot: bool = False) -> dict:
    results, converged, _path, _cache = circular_search(
        slope_data,
        method_name="bishop",
        diagnostic=False,
        num_slices=num_slices,
    )

    finite = [r for r in results if float(r.get("FS", 9999.0)) < 9999.0]
    if not finite:
        raise ValueError("Geen geldige xslope-oplossing gevonden (FS=9999 voor alle kandidaten).")

    best = min(finite, key=lambda r: float(r["FS"]))

    result = {
        "converged": bool(converged),
        "veiligheidsfactor": float(best["FS"]),
        "maatgevende_cirkel_x0": float(best["Xo"]),
        "maatgevende_cirkel_y0": float(best["Yo"]),
        "maatgevende_cirkel_r": float(best["Yo"] - best["Depth"]),
        "maatgevende_cirkel_depth": float(best["Depth"]),
    }

    if include_plot:
        result["plot_base64"] = _render_plot_solution_base64(slope_data, best)

    return result
