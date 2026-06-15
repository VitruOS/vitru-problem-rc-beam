# packages/solver/vitru/problems/rc_beam/tests/test_inputs.py
#
# Default inputs dict for testing the rectangular RC beam geometry builder
# and analyse.py. Values taken directly from schema v0.6 defaults.
#
# Usage:
#   from test_inputs import inputs_rectangular, inputs_circular, inputs_tee
#   geom = build_geometry(inputs_rectangular)
#   results = analyse(geom, inputs_rectangular)

# ── RECTANGULAR ───────────────────────────────────────────────────────────────

inputs_rectangular = {
    # -- Shared variables (base schema) --
    "fc_MPa": 32,
    "fsy_MPa": 500,
    # -- Geometry variables (rectangular child schema) --
    "b_mm": 350,
    "D_mm": 600,
    # Bottom face — beam mode (n free, s derived)
    "n_bot": 4,
    "dia_bot_mm": 24,
    "s_bot_mm": None,  # derived by geometry builder
    # Top face — beam mode
    "n_top": 2,
    "dia_top_mm": 16,
    "s_top_mm": None,  # derived by geometry builder
    # -- Parameters (rectangular child schema) --
    "cover_bot_mm": 30,
    "cover_top_mm": 30,
    "cover_side_mm": 30,
    "n_side_per_face": 0,
    "dia_side_mm": 16,
    "s_side_mm": None,  # derived by geometry builder
    # -- Parameters (base schema) --
    "M_star_kNm": 500.0,
    "N_star_kN": 0.0,
    "exposure_class": "A1",
    "unit_cost_concrete_AUD_per_m3": {"25": 270, "32": 300, "40": 310, "50": 330, "65": 350, "80": 380},
    "unit_cost_steel_AUD_per_t": 1800,
    "carbon_concrete_kgCO2e_per_m3": {
        "25": 195,
        "32": 225,
        "40": 270,
        "50": 320,
        "65": 370,
        "80": 410,
    },
    "carbon_steel_kgCO2e_per_kg": 1.51,
}


# ── CIRCULAR ──────────────────────────────────────────────────────────────────

inputs_circular = {
    # -- Shared variables --
    "fc_MPa": 32,
    "fsy_MPa": 500,
    # -- Geometry variables (circular child schema) --
    "D_mm": 500,
    "n_bars": 8,
    "dia_bar_mm": 20,
    # -- Parameters (circular child schema) --
    "cover_mm": 30,
    # -- Parameters (base schema) --
    "M_star_kNm": 500.0,
    "N_star_kN": 0.0,
    "exposure_class": "A1",
    "unit_cost_concrete_AUD_per_m3": {"25": 270, "32": 300, "40": 310, "50": 330, "65": 350, "80": 380},
    "unit_cost_steel_AUD_per_t": 1800,
    "carbon_concrete_kgCO2e_per_m3": {
        "25": 195,
        "32": 225,
        "40": 270,
        "50": 320,
        "65": 370,
        "80": 410,
    },
    "carbon_steel_kgCO2e_per_kg": 1.51,
}


# ── T-BEAM ────────────────────────────────────────────────────────────────────

inputs_tee = {
    # -- Shared variables --
    "fc_MPa": 32,
    "fsy_MPa": 500,
    # -- Geometry variables (tee child schema) --
    "b_w_mm": 300,
    "D_mm": 700,
    "b_f_mm": 1000,
    "D_f_mm": 150,
    # Bottom face — beam mode
    "n_bot": 5,
    "dia_bot_mm": 28,
    "s_bot_mm": None,  # derived by geometry builder
    # Top face — beam mode
    "n_top": 4,
    "dia_top_mm": 16,
    "s_top_mm": None,  # derived by geometry builder
    # -- Parameters (tee child schema) --
    "cover_bot_mm": 30,
    "cover_top_mm": 30,
    "cover_side_mm": 30,
    "n_side_per_face": 0,
    "dia_side_mm": 16,
    "s_side_mm": None,  # derived by geometry builder
    # -- Parameters (base schema) --
    "M_star_kNm": 500.0,
    "N_star_kN": 0.0,
    "exposure_class": "A1",
    "unit_cost_concrete_AUD_per_m3": {"25": 270, "32": 300, "40": 310, "50": 330, "65": 350, "80": 380},
    "unit_cost_steel_AUD_per_t": 1800,
    "carbon_concrete_kgCO2e_per_m3": {
        "25": 195,
        "32": 225,
        "40": 270,
        "50": 320,
        "65": 370,
        "80": 410,
    },
    "carbon_steel_kgCO2e_per_kg": 1.51,
}
