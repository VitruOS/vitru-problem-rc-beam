# vitru-problem-rc-beam

Python package for evaluating reinforced concrete beam sections to **AS 3600-2018**. Given a beam geometry and reinforcement layout, it returns factored bending capacity, utilisation, steel ratios, cost, and embodied carbon.

Designed as a standalone evaluation library — use it in your own scripts, parametric studies, or optimisation loops.

## Scope

- Standard: AS 3600-2018
- Section types: rectangular (T-beam and circular planned)
- Limit state: ULS bending
- Checks: flexural capacity, ductility (ku), minimum steel ratio, nominal cover

## Installation

```bash
pip install vitru-problem-rc-beam
```

> **Note:** this package is not yet on PyPI. Until it is, install from source:
> ```bash
> git clone https://github.com/VitruOS/vitru-problem-rc-beam
> cd vitru-problem-rc-beam
> pip install .
> ```

## Quick start

```python
from vitru_problem_rc_beam import evaluate

results = evaluate({
    # Section
    "b_mm": 350,
    "D_mm": 700,
    "fc_MPa": 40,
    # Reinforcement
    "n_bot": 4,   "dia_bot_mm": 24,
    "n_top": 2,   "dia_top_mm": 16,
    # Design action
    "M_star_kNm": 600.0,
})

print(f"φMuo = {results['phi_Muo_kNm']:.1f} kNm")
print(f"utilisation = {results['bending_utilisation']:.3f}")
print(f"ku = {results['ku']:.3f}")
```

All parameters not supplied use the defaults listed below.

## Inputs

### Required

| Key | Unit | Description |
|-----|------|-------------|
| `b_mm` | mm | Beam width |
| `D_mm` | mm | Overall section depth |
| `fc_MPa` | MPa | Characteristic compressive strength f'c |
| `n_bot` | — | Number of bottom (tension) bars |
| `dia_bot_mm` | mm | Bottom bar diameter |
| `n_top` | — | Number of top bars |
| `dia_top_mm` | mm | Top bar diameter |
| `M_star_kNm` | kNm | Factored design bending moment (sagging positive) |

### Optional — reinforcement and cover

| Key | Default | Unit | Description |
|-----|---------|------|-------------|
| `fsy_MPa` | `500` | MPa | Reinforcement yield strength |
| `N_star_kN` | `0.0` | kN | Factored axial force (compression positive) |
| `cover_bot_mm` | `30` | mm | Nominal cover to bottom bars |
| `cover_top_mm` | `30` | mm | Nominal cover to top bars |
| `cover_side_mm` | `30` | mm | Nominal cover to side bars |
| `n_side_per_face` | `0` | — | Side face bars per vertical face (AS 3600 Cl. 8.6 when D > 750 mm) |
| `dia_side_mm` | `16` | mm | Side bar diameter (used only when `n_side_per_face > 0`) |

### Optional — exposure and formwork

| Key | Default | Valid values | Description |
|-----|---------|--------------|-------------|
| `exposure_class` | `"A1"` | `A1 A2 B1 B2 C1 C2` | AS 3600 Table 4.3 exposure class — governs minimum cover |
| `formwork` | `"standard"` | `standard rigid` | Formwork type — governs minimum cover per AS 3600 Table 4.10.3 |

### Optional — cost and carbon

Default carbon intensities are from the EPIC Australia database v3 (general purpose cement blend). Default rates are indicative Sydney 2025 market values.

| Key | Default | Unit | Description |
|-----|---------|------|-------------|
| `unit_cost_concrete_AUD_per_m3` | `180.0` | AUD/m³ | Concrete supply and place rate |
| `unit_cost_steel_AUD_per_kg` | `1.80` | AUD/kg | Reinforcing steel supply and fix rate |
| `carbon_steel_kgCO2e_per_kg` | `1.51` | kgCO₂e/kg | Steel embodied carbon factor |
| `carbon_concrete_kgCO2e_per_m3` | see below | kgCO₂e/m³ | Concrete embodied carbon by grade |

The concrete carbon factor is a `dict` keyed by f'c grade (as a string). Values for grades between defined keys are linearly interpolated; outside the range the nearest value is used.

```python
# Default values (EPIC Australia v3)
"carbon_concrete_kgCO2e_per_m3": {
    "25": 195,
    "32": 225,
    "40": 270,
    "50": 320,
    "65": 370,
    "80": 410,
}
```

To override a single grade without changing the rest, pass the full dict with your modified value:

```python
results = evaluate({
    ...,
    "carbon_concrete_kgCO2e_per_m3": {
        "25": 195, "32": 225, "40": 230,   # 40 MPa updated
        "50": 320, "65": 370, "80": 410,
    },
})
```

## Outputs

`evaluate()` returns a flat `dict` with the following keys:

| Key | Unit | Description |
|-----|------|-------------|
| `phi_Muo_kNm` | kNm | Factored ultimate bending capacity φMuo |
| `bending_utilisation` | — | M* / φMuo |
| `ku` | — | Neutral axis parameter (ductility check; must be ≤ 0.36 per AS 3600 Cl. 8.1.5) |
| `rho_t` | — | Actual tensile steel ratio Ast / (b·d) |
| `rho_min` | — | Minimum steel ratio per AS 3600 Cl. 8.1.6.1 |
| `d_mm` | mm | Effective depth (extreme compression fibre to centroid of tension steel) |
| `b_eff_mm` | mm | Effective width used for steel ratio (= `b_mm` for rectangular) |
| `Ag_mm2` | mm² | Gross section area (concrete + steel) |
| `Ast_total_mm2` | mm² | Total reinforcement area (all faces) |
| `cost_per_m_AUD` | AUD/m | Material cost per metre of beam |
| `carbon_per_m_kgCO2e` | kgCO₂e/m | Embodied carbon per metre of beam |
| `cover_min_mm` | mm | Minimum required cover per AS 3600 Table 4.10.3 |
| `cover_tension_mm` | mm | Nominal cover provided to tension face bars |
| `s_bot_mm` | mm | Derived centre-to-centre spacing of bottom bars |
| `s_top_mm` | mm | Derived centre-to-centre spacing of top bars |
| `clear_spacing_bot_mm` | mm | Clear spacing between bottom bars |
| `clear_spacing_top_mm` | mm | Clear spacing between top bars |

## Parametric study example

```python
from vitru_problem_rc_beam import evaluate

base = {
    "b_mm": 300, "D_mm": 700, "fc_MPa": 40,
    "n_bot": 4, "dia_bot_mm": 24,
    "n_top": 2, "dia_top_mm": 16,
    "M_star_kNm": 600.0,
}

for D in range(500, 1001, 50):
    r = evaluate({**base, "D_mm": D})
    print(f"D={D:4d}  φMuo={r['phi_Muo_kNm']:6.1f} kNm  "
          f"util={r['bending_utilisation']:.3f}  "
          f"cost={r['cost_per_m_AUD']:.2f} AUD/m")
```

## Known limitations

- `rho_min` uses the rectangular-section factor `0.2` — not valid for T-beams or circular sections
- ULS bending only — no shear, deflection, or crack width checks
- Rectangular section only in the current release

## Dependencies

- [concreteproperties](https://github.com/robbievanleeuwen/concrete-properties) by Robbie van Leeuwen — section analysis and AS 3600 design code implementation
- [sectionproperties](https://github.com/robbievanleeuwen/section-properties) by Robbie van Leeuwen — geometry primitives

## Development

```bash
git clone https://github.com/VitruOS/vitru-problem-rc-beam
cd vitru-problem-rc-beam
pip install -e .
```

## Links

- [GitHub](https://github.com/VitruOS/vitru-problem-rc-beam)
- [Vitru](https://vitru.io) — multi-objective structural optimisation platform
