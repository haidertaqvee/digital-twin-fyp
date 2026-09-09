"""
Stage 2 — building height heuristic for SpaceNet Vegas.

SpaceNet Vegas has no heights. Every geometry is POLYGON Z with Z=0, and the
attribute columns that look like heights (AREA, Shape_Leng, SISL, Shape_Le_2)
are either all-zero or in the wrong units (Shape_Le_3 is square degrees).
This was verified over 1,561 features across 40 tiles on 2026-09-09:
  - Z coords: 1,491 sampled, all exactly 0.0
  - AREA/Shape_Leng/Shape_Le_1/SISL: all 0.0
  - Shape_Le_2: partially 0, inconsistent with true projected area
  - footprint areas (EPSG:32611): median 164 m2, p75 208 m2, p95 417 m2,
    max 2180 m2; ~29.7 buildings/tile (Vegas suburban sprawl)

So heights are genuinely absent. Any 3D extrusion for Unity must invent them,
and the honest thing is to do it with an explicit, documented rule rather than
pretending a learned model produced them. This file is that rule.

The heuristic maps footprint area -> building:levels -> height_m. It is tuned
to Vegas: small footprints are single-story suburban houses, large ones are
commercial/low-rise. It is intentionally coarse — a DSM or OSM building:levels
join would replace it when available.

Swap this file out without touching vectorize.py: `estimate_levels` is the
only symbol vectorize.py imports.
"""

import numpy as np
import pandas as pd

LEVEL_HEIGHT_M = 3.0  # metres per storey, standard for Unity extrusion

# Area thresholds (m2, measured in EPSG:32611) -> levels.
# Chosen from the observed distribution above:
#   < 150  -> 1 level  (small house / garage, ~40% of footprints)
#   150-300 -> 2 levels (large house / duplex, ~40%)
#   300-600 -> 3 levels (small commercial, ~15%)
#   > 600   -> 4 levels (large commercial, ~5%, capped — no towers in this AOI)
_LEVEL_BINS_M2 = [150, 300, 600]
_LEVEL_VALUES = [1, 2, 3, 4]


def estimate_levels(area_m2):
    """
    Footprint area (m2) -> integer building:levels.

    Accepts a scalar, numpy array, or pandas Series and returns the same shape
    with integer levels. Mirrors the OSM `building:levels` tag so downstream
    code can treat this column and a future OSM join identically.
    """
    if isinstance(area_m2, pd.Series):
        return pd.Series(
            np.digitize(area_m2.to_numpy(), _LEVEL_BINS_M2).astype(int) + 1,
            index=area_m2.index,
        ).clip(lower=1, upper=4)
    arr = np.asarray(area_m2, dtype=float)
    # np.digitize returns 0..len(bins); +1 maps to 1..4
    levels = np.digitize(arr, _LEVEL_BINS_M2).astype(int) + 1
    levels = np.clip(levels, 1, 4)
    if levels.ndim == 0:
        return int(levels)
    return levels


def describe_heuristic():
    """One-liner for logs/reports so the assumption is never hidden."""
    return (
        f"heights: area->levels via {list(zip(_LEVEL_BINS_M2, _LEVEL_VALUES))} "
        f"+ cap 4, {LEVEL_HEIGHT_M} m/level (documented heuristic; "
        f"SpaceNet Vegas has no ground-truth heights)"
    )
