from math import pi
from concreteproperties.concrete_section import ConcreteSection
from concreteproperties.design_codes.as3600 import AS3600

from vitru_problem_rc_beam.geometry.rectangular import (
    build_geometry as build_rectangular_geometry,
)


def analyse(geometry, inputs: dict) -> dict:
    """
    Beam-type agnostic AS 3600 ultimate bending analysis.

    Receives a CompoundGeometry from any geometry builder and the full
    merged inputs dict (variables + parameters). Returns a dict of
    all outputs promised by the schema evaluate.outputs block.

    Parameters
    ----------
    geometry : CompoundGeometry
        Built by the geometry resolver (rectangular, circular or tee).
    inputs : dict
        Full merged inputs — variables at candidate values + parameters.

    Returns
    -------
    dict with keys:
        phi_Muo_kNm, ku, rho_min, rho_t,
        cover_min_mm, cover_tension_mm,
        d_mm, b_eff_mm,
        Ag_mm2, Ast_total_mm2,
        cost_per_m_AUD, carbon_per_m_kgCO2e
    """

    # ── Build section and assign to AS3600 design code ────────────────
    conc_sec = ConcreteSection(geometry)
    dc = AS3600()
    dc.assign_concrete_section(conc_sec)

    # ── Design actions (N·mm and N) ───────────────────────────────────
    # Schema stores M* in kNm and N* in kN — convert to N and N·mm
    N_star_N = inputs["N_star_kN"] * 1e3
    M_star_kNm = inputs["M_star_kNm"]

    # ── Ultimate bending capacity ─────────────────────────────────────
    # theta=0: sagging (tension at bottom, compression at top)
    # n_design: factored axial force in N (compression positive)
    factored, unfactored, phi = dc.ultimate_bending_capacity(
        theta=0,
        n_design=N_star_N,
    )

    phi_Muo_kNm = factored.m_xy / 1e6  # N·mm → kN·m
    ku = unfactored.k_u  # neutral axis parameter

    # ── Gross section properties ──────────────────────────────────────
    gross = dc.get_gross_properties()
    Ag_mm2 = gross.total_area  # gross concrete + steel area

    # ── Minimum steel ratio (AS 3600 Cl. 8.1.6.1) ────────────────────
    # rho_min = max(0.2 * (D/d)^2 * f_ct_f / fsy, 0.0025)
    # concreteproperties gives us f_ct_f via the concrete material
    # We need to extract it — it's stored on the concrete geometry material
    fc = inputs["fc_MPa"]
    fsy = inputs["fsy_MPa"]
    D_mm = inputs["D_mm"]
    d_mm = _effective_depth(inputs)
    b_eff_mm = _effective_width(inputs)

    # f_ct_f per AS 3600 Cl. 3.1.1.3: 0.6 * sqrt(f'c)
    f_ct_f = 0.6 * (fc**0.5)
    # TODO: This is currently hard-coded as 0.2 which is only for rectangular sections
    rho_min = max(0.2 * (D_mm / d_mm) ** 2 * (f_ct_f / fsy), 0.0025)

    # ── Actual tensile steel ratio ────────────────────────────────────
    Ast_bot = _ast_bottom(inputs)
    rho_t = Ast_bot / (b_eff_mm * d_mm)

    # ── Total steel area (all faces) ──────────────────────────────────
    Ast_total_mm2 = _ast_total(inputs)

    # ── Cover outputs ─────────────────────────────────────────────────
    cover_tension_mm = _cover_tension(inputs)
    cover_min_mm = _cover_min(
        inputs["exposure_class"], inputs["fc_MPa"], inputs.get("formwork", "standard")
    )

    # ── Cost ──────────────────────────────────────────────────────────
    cost_table = inputs["unit_cost_concrete_AUD_per_m3"]
    conc_rate = _interp_carbon(cost_table, fc)
    steel_rate = inputs["unit_cost_steel_AUD_per_t"]
    rho_steel = 7850  # kg/m³

    vol_conc_per_m = Ag_mm2 / 1e6  # m²  (per metre of beam)
    mass_steel_per_m = (Ast_total_mm2 / 1e6) * rho_steel  # kg/m
    mass_steel_per_m_t = mass_steel_per_m / 1000  # t/m

    cost_per_m_AUD = vol_conc_per_m * conc_rate + mass_steel_per_m_t * steel_rate

    # ── Embodied carbon ───────────────────────────────────────────────
    carbon_table = inputs["carbon_concrete_kgCO2e_per_m3"]
    carbon_conc_per_m3 = _interp_carbon(carbon_table, fc)
    carbon_steel_per_kg = inputs["carbon_steel_kgCO2e_per_kg"]

    carbon_per_m_kgCO2e = (
        vol_conc_per_m * carbon_conc_per_m3 + mass_steel_per_m * carbon_steel_per_kg
    )

    return {
        "phi_Muo_kNm": phi_Muo_kNm,
        "ku": ku,
        "rho_min": rho_min,
        "rho_t": rho_t,
        "cover_min_mm": cover_min_mm,
        "cover_tension_mm": cover_tension_mm,
        "d_mm": d_mm,
        "b_eff_mm": b_eff_mm,
        "Ag_mm2": Ag_mm2,
        "Ast_total_mm2": Ast_total_mm2,
        "cost_per_m_AUD": cost_per_m_AUD,
        "carbon_per_m_kgCO2e": carbon_per_m_kgCO2e,
        "bending_utilisation": M_star_kNm / phi_Muo_kNm,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────


def _interp_carbon(carbon_table: dict, fc: float) -> float:
    """
    Linear interpolation of carbon intensity for grades not in the table.
    Clamps to the nearest defined grade outside the table range.
    """
    grades = sorted(int(k) for k in carbon_table)
    if fc <= grades[0]:
        return carbon_table[str(grades[0])]
    if fc >= grades[-1]:
        return carbon_table[str(grades[-1])]
    key = str(int(fc))
    if key in carbon_table:
        return carbon_table[key]
    lo = max(g for g in grades if g < fc)
    hi = min(g for g in grades if g > fc)
    t = (fc - lo) / (hi - lo)
    return carbon_table[str(lo)] + t * (carbon_table[str(hi)] - carbon_table[str(lo)])


def _effective_depth(inputs: dict) -> float:
    """
    Effective depth d — extreme compression fibre to centroid of tension steel.
    Beam type resolved from available keys.
    """
    D = inputs["D_mm"]

    if "b_mm" in inputs or "b_w_mm" in inputs:
        # Rectangular or T-beam — tension steel at bottom
        cover_bot = inputs["cover_bot_mm"]
        dia_bot = inputs["dia_bot_mm"]
        return D - cover_bot - dia_bot / 2

    else:
        # Circular — d = radius + bar ring radius (to centroid of tension bars)
        cover = inputs["cover_mm"]
        dia_bar = inputs["dia_bar_mm"]
        r_bar = D / 2 - cover - dia_bar / 2
        return D / 2 + r_bar


def _effective_width(inputs: dict) -> float:
    """b_eff for steel ratio calculation — web width for T-beam, b for rect, D for circular."""
    if "b_w_mm" in inputs:
        return inputs["b_w_mm"]
    elif "b_mm" in inputs:
        return inputs["b_mm"]
    else:
        return inputs["D_mm"]  # circular — use diameter as proxy


def _cover_tension(inputs: dict) -> float:
    """Nominal cover to the tension face bars."""
    if "cover_bot_mm" in inputs:
        return inputs["cover_bot_mm"]
    return inputs["cover_mm"]  # circular


def _ast_bottom(inputs: dict) -> float:
    """Area of tensile (bottom) steel in mm²."""
    if "n_bot" in inputs:
        n = inputs["n_bot"]
        dia = inputs["dia_bot_mm"]
        return n * pi * (dia / 2) ** 2
    else:
        # Circular — all bars contribute, use half as tension-side proxy
        n = inputs["n_bars"]
        dia = inputs["dia_bar_mm"]
        return (n / 2) * pi * (dia / 2) ** 2


def _ast_total(inputs: dict) -> float:
    """Total steel area across all faces in mm²."""
    if "n_bars" in inputs:
        # Circular
        n = inputs["n_bars"]
        dia = inputs["dia_bar_mm"]
        return n * pi * (dia / 2) ** 2

    # Rectangular or T-beam
    n_bot = inputs["n_bot"]
    n_top = inputs["n_top"]
    dia_bot = inputs["dia_bot_mm"]
    dia_top = inputs["dia_top_mm"]

    ast = n_bot * pi * (dia_bot / 2) ** 2 + n_top * pi * (dia_top / 2) ** 2

    n_side = inputs.get("n_side_per_face", 0)
    if n_side > 0:
        dia_side = inputs.get("dia_side_mm", 16)
        ast += 2 * n_side * pi * (dia_side / 2) ** 2  # both faces

    return ast


def _cover_min(exposure_class: str, fc_MPa: float, formwork: str = "standard") -> float:
    """
    Minimum cover per AS 3600 Table 4.10.3.

    Parameters
    ----------
    exposure_class : str
        AS 3600 exposure classification: A1, A2, B1, B2, C1, C2
    fc_MPa : float
        Characteristic compressive strength f'c in MPa
    formwork : str
        "standard" — Table 4.10.3.2 (standard formwork and compaction)
        "rigid"    — Table 4.10.3.3 (repetitive/intense compaction or self-compacting
                     concrete in rigid formwork)

    Returns
    -------
    float
        Minimum cover in mm. Returns None if the combination is not
        permitted (dashes in the table).
    """

    # Table 4.10.3.2 — standard formwork
    # {exposure_class: {fc_threshold: cover_mm}}
    # fc_threshold is the MINIMUM f'c for that cover value
    standard = {
        "A1": {20: 20, 25: 20, 32: 20, 40: 20, 50: 20},
        "A2": {20: 50, 25: 30, 32: 25, 40: 20, 50: 20},
        "B1": {25: 60, 32: 40, 40: 30, 50: 25},
        "B2": {32: 65, 40: 45, 50: 35},
        "C1": {40: 70, 50: 50},
        "C2": {50: 65},
    }

    # Table 4.10.3.3 — rigid formwork
    rigid = {
        "A1": {20: 20, 25: 20, 32: 20, 40: 20, 50: 20},
        "A2": {20: 45, 25: 30, 32: 20, 40: 20, 50: 20},
        "B1": {25: 45, 32: 30, 40: 25, 50: 20},
        "B2": {32: 50, 40: 35, 50: 25},
        "C1": {40: 60, 50: 45},
        "C2": {50: 60},
    }

    table = standard if formwork == "standard" else rigid

    if exposure_class not in table:
        raise ValueError(f"Unknown exposure class '{exposure_class}'")

    grades = table[exposure_class]

    # Find the cover for the lowest fc threshold that fc_MPa meets or exceeds
    cover = None
    for fc_threshold in sorted(grades.keys()):
        if fc_MPa >= fc_threshold:
            cover = grades[fc_threshold]

    if cover is None:
        raise ValueError(
            f"Concrete grade f'c={fc_MPa} MPa is not permitted for "
            f"exposure class {exposure_class} with {formwork} formwork. "
            f"Minimum f'c required: {min(grades.keys())} MPa."
        )

    return cover
