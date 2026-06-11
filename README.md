# vitru-problem-rc-beam

RC beam optimisation problem for [Vitru](https://vitru.app) — a multi-objective structural optimisation platform.

## What it does

Optimises a reinforced concrete beam section for **ultimate bending capacity to AS 3600-2018**, navigating trade-offs between section area and steel area across concrete grade, depth, bar size, and bar count.

The solver drives NSGA-II across the design space and returns a Pareto front of non-dominated solutions. Each candidate is evaluated by building a full `concreteproperties` section and calling `AS3600.ultimate_bending_capacity()`.

## Scope

- Standard: AS 3600-2018
- Section type: rectangular (T-beam and circular variants are planned)
- Limit state: ULS bending only (no shear, deflection, or crack width checks)
- Cover: checked against AS 3600 Table 4.10.3 for exposure class

## Known limitations

- `rho_min` uses the rectangular-section factor `0.2` — not valid for T-beams or circular sections
- No shear, deflection, or crack width checks
- Rectangular section only in the current release

## Dependencies

- [concreteproperties](https://github.com/robbievanleeuwen/concrete-properties) by Robbie van Leeuwen — section analysis and AS 3600 design code
- [sectionproperties](https://github.com/robbievanleeuwen/section-properties) by Robbie van Leeuwen — geometry primitives

## Installation

```bash
pip install vitru-problem-rc-beam
```

Or as a local editable install (from within the Vitru solver repo):

```bash
uv pip install -e ./problems/rc_beam
```

## Usage

```python
from vitru_problem_rc_beam import evaluate

inputs = {
    "beam_type": "rc_beam_rectangular",
    "fc_MPa": 40,
    "fsy_MPa": 500,
    "b_mm": 300,
    "D_mm": 700,
    "n_bot": 4,
    "dia_bot_mm": 24,
    "n_top": 2,
    "dia_top_mm": 16,
    "cover_bot_mm": 30,
    "cover_top_mm": 30,
    "cover_side_mm": 30,
    "n_side_per_face": 0,
    "dia_side_mm": 16,
    "M_star_kNm": 500.0,
    "N_star_kN": 0.0,
    "exposure_class": "A1",
    "unit_cost_concrete_AUD_per_m3": 180.0,
    "unit_cost_steel_AUD_per_kg": 1.80,
    "carbon_concrete_kgCO2e_per_m3": {
        "25": 195, "32": 225, "40": 270, "50": 320, "65": 370, "80": 410,
    },
    "carbon_steel_kgCO2e_per_kg": 1.51,
}

results = evaluate(inputs)
print(results["phi_Muo_kNm"])   # factored bending capacity in kNm
print(results["bending_utilisation"])
```

## Links

- [vitru.app](https://vitru.app)
- [GitHub](https://github.com/VitruOS/vitru-problem-rc-beam)
