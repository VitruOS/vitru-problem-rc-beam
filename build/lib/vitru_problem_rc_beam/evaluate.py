from vitru_problem_rc_beam.geometry.rectangular import (
    build_geometry as build_rectangular,
)
from vitru_problem_rc_beam.geometry.rectangular import (
    compute_spacing_outputs as spacing_rectangular,
)

# from .geometry.circular import build_geometry as build_circular      # TODO
# from .geometry.tee import build_geometry as build_tee                # TODO
# from .geometry.tee import compute_spacing_outputs as spacing_tee     # TODO
from vitru_problem_rc_beam.analyse import analyse

# ── Geometry builder registry ─────────────────────────────────────────────────
# Keyed by schema id. Add new beam types here as they are implemented.

_BUILDERS = {
    "rc_beam_rectangular": (build_rectangular, spacing_rectangular),
    # "rc_beam_circular":  (build_circular,    None),
    # "rc_beam_tee":       (build_tee,         spacing_tee),
}


def evaluate(inputs: dict) -> dict:
    """
    Top-level evaluate function for the rc_beam problem family.

    Called by the MOO engine for each candidate solution. Receives a flat
    dict of all variables (at candidate values) and parameters merged together.
    Returns a flat dict of all outputs promised by the schema evaluate.outputs
    block.

    Parameters
    ----------
    inputs : dict
        Merged variables + parameters. Must include "beam_type" key set
        to a valid schema id (e.g. "rc_beam_rectangular").

    Returns
    -------
    dict
        All structural, cost, carbon and spacing outputs.
    """

    beam_type = inputs.get("beam_type", "rc_beam_rectangular")

    if beam_type not in _BUILDERS:
        raise ValueError(
            f"Unknown beam type '{beam_type}'. " f"Available: {list(_BUILDERS.keys())}"
        )

    build_geometry, compute_spacing = _BUILDERS[beam_type]

    # ── Stage 1: build geometry ───────────────────────────────────────
    geometry = build_geometry(inputs)

    # ── Stage 2: spacing outputs (rectangular and tee only) ───────────
    spacing_outputs = {}
    if compute_spacing is not None:
        spacing_outputs = compute_spacing(inputs)

    # ── Stage 3: structural analysis ──────────────────────────────────
    analysis_outputs = analyse(geometry, inputs)

    # ── Merge and return ──────────────────────────────────────────────
    return {
        **analysis_outputs,
        **spacing_outputs,
    }
