from math import pi
from sectionproperties.pre.library.concrete_sections import concrete_rectangular_section
from concreteproperties.design_codes.as3600 import AS3600


def build_geometry(inputs: dict) -> object:
    """
    RReturns a CompoundGeometry for a rectangular RC beam.

    Expects inputs keys (merged variables + parameters from schema):
        b_mm, D_mm, fc_MPa, fsy_MPa
        n_bot, dia_bot_mm, cover_bot_mm
        n_top, dia_top_mm, cover_top_mm
        n_side_per_face, dia_side_mm, cover_side_mm   (side bars, default 0)

    Bar input mode:
        Beam mode (default): n_bot/n_top provided directly.
        Spacing mode: n derived from s_bot_mm/s_top_mm before this call, passed in as n_bot/n_top.

    Returns
    -------
    CompoundGeometry
    """

    # ── Unpack ────────────────────────────────────────────────────────
    b = inputs["b_mm"]
    D = inputs["D_mm"]
    fc = inputs["fc_MPa"]
    fsy = inputs["fsy_MPa"]

    n_bot = round(inputs["n_bot"])
    dia_bot = inputs["dia_bot_mm"]
    cover_bot = inputs["cover_bot_mm"]

    n_top = round(inputs["n_top"])
    dia_top = inputs["dia_top_mm"]
    cover_top = inputs["cover_top_mm"]

    n_side = round(inputs.get("n_side_per_face", 0))
    dia_side = inputs.get("dia_side_mm", 16)
    cover_side = inputs.get("cover_side_mm", 30)

    # ── Materials via AS3600 design code ──────────────────────────────
    dc = AS3600()
    concrete_mat = dc.create_concrete_material(compressive_strength=fc)
    reinforcement_mat = dc.create_steel_material(yield_strength=fsy)

    # ── Bar areas ─────────────────────────────────────────────────────
    area_bot = pi * (dia_bot / 2) ** 2
    area_top = pi * (dia_top / 2) ** 2
    area_side = pi * (dia_side / 2) ** 2

    # ── Concrete section with top and bottom bars ──────────────────────
    # concrete_rectangular_section places bars anchored to cover
    geom = concrete_rectangular_section(
        d=D,
        b=b,
        dia_top=dia_top,
        area_top=area_top,
        n_top=n_top,
        c_top=cover_top,
        dia_bot=dia_bot,
        area_bot=area_bot,
        n_bot=n_bot,
        c_bot=cover_bot,
        dia_side=dia_side,
        area_side=area_side,
        n_side=n_side,
        c_side=cover_side,
        n_circle=4,
        conc_mat=concrete_mat,  # type: ignore
        steel_mat=reinforcement_mat,  # type: ignore
    )

    return geom


def compute_spacing_outputs(inputs: dict) -> dict:
    """
    Computes spacing-related outputs for constraint checking.
    Called by analyse.py after geometry is built.

    Returns keys:
        clear_spacing_bot_mm, clear_spacing_top_mm, clear_spacing_side_mm,
        min_clear_spacing_bot_mm, min_clear_spacing_top_mm, min_clear_spacing_side_mm,
        n_bot_required_mm, n_top_required_mm,
        s_bot_mm, s_top_mm, s_side_mm  (derived spacings, beam mode)
    """

    b = inputs["b_mm"]
    D = inputs["D_mm"]
    n_bot = round(inputs["n_bot"])
    dia_bot = inputs["dia_bot_mm"]
    cover_bot = inputs["cover_bot_mm"]
    n_top = round(inputs["n_top"])
    dia_top = inputs["dia_top_mm"]
    cover_top = inputs["cover_top_mm"]
    n_side = round(inputs.get("n_side_per_face", 0))
    dia_side = inputs.get("dia_side_mm", 16)
    cover_side = inputs["cover_side_mm"]

    # Centre-to-centre spacing
    available_bot = b - 2 * cover_side - dia_bot
    s_bot = available_bot / max(n_bot - 1, 1)
    clear_bot = s_bot - dia_bot

    available_top = b - 2 * cover_side - dia_top
    s_top = available_top / max(n_top - 1, 1)
    clear_top = s_top - dia_top

    # Minimum clear spacing per AS 3600 Cl. 8.1.7
    min_clear_bot = max(1.5 * dia_bot, 25.0)
    min_clear_top = max(1.5 * dia_top, 25.0)
    min_clear_side = max(1.5 * dia_side, 25.0)

    # Width required to fit n bars at minimum spacing
    b_bot_required_mm = 2 * cover_side + n_bot * dia_bot + (n_bot - 1) * min_clear_bot
    b_top_required_mm = 2 * cover_side + n_top * dia_top + (n_top - 1) * min_clear_top

    # Side bar spacing — distributed over height
    if n_side > 0:
        y_bot_bar = cover_bot + dia_bot / 2
        y_top_bar = D - cover_top - dia_top / 2
        web_height = y_top_bar - y_bot_bar
        s_side = web_height / (n_side + 1)
        clear_side = s_side - dia_side
    else:
        s_side = None
        clear_side = None

    scores = []
    if n_bot > 1:
        scores.append(100.0 * min_clear_bot / clear_bot)
    if n_top > 1:
        scores.append(100.0 * min_clear_top / clear_top)
    congestion_score = max(scores) if scores else 0.0

    return {
        "s_bot_mm": s_bot,
        "s_top_mm": s_top,
        "s_side_mm": s_side,
        "clear_spacing_bot_mm": clear_bot,
        "clear_spacing_top_mm": clear_top,
        "clear_spacing_side_mm": clear_side,
        "min_clear_spacing_bot_mm": min_clear_bot,
        "min_clear_spacing_top_mm": min_clear_top,
        "min_clear_spacing_side_mm": min_clear_side,
        "b_bot_required_mm": b_bot_required_mm,
        "b_top_required_mm": b_top_required_mm,
        "congestion_score": congestion_score,
    }
