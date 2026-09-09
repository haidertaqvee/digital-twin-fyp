# Stage 2 — Enrichment (vectorize + heights)

Turns Stage 1's binary masks into **georeferenced building polygons with heights**,
ready for Stage 3 extrusion and Stage 4 Unity.

```
satellite .tif ──► mask .png ──► vectorize.py ──► buildings.geojson
                                  (inverse of       (+ area_m2,
                                   build_masks.py)    levels, height_m)
                                                       │
                                                       └─► heights.py
                                                           (documented heuristic)
```

## Files

| File | Role |
|------|------|
| [vectorize.py](vectorize.py) | mask PNG → polygons via `rasterio.features.shapes`, using each tile's affine transform so coordinates land in EPSG:4326 |
| [heights.py](heights.py) | footprint area → `building:levels` → `height_m`. The only place heights are invented. |

## Usage

```powershell
# Ground truth masks (validates the round-trip against SpaceNet labels)
python src/stage2_enrichment/vectorize.py --split test --source masks

# Model predictions (run stage1_extraction/inference.py first)
python src/stage1_extraction/inference.py --split test
python src/stage2_enrichment/vectorize.py --split test --source predictions
```

Output: `data/processed/<split>/vectors/buildings_<source>.geojson` with columns
`tile`, `geometry`, `area_m2`, `levels`, `height_m`.

## Verified behaviour (2026-09-09, test split)

- **3,987 polygons across 140/146 tiles** (6 tiles have no buildings), EPSG:4326,
  0 null and 0 invalid geometries.
- **Round-trip IoU 0.992–0.996** vs the original SpaceNet `buildings_*.geojson`
  on three sampled tiles — vectorization faithfully inverts `build_masks.py`.
- Polygon counts differ from labels by ≤1 per tile; median areas agree within ~5 m².

## The height heuristic — read this before trusting `height_m`

**SpaceNet Vegas contains no height information.** This was verified over 1,561
features / 40 tiles on 2026-09-09:

- every geometry is `POLYGON Z` with **Z exactly 0.0**;
- `AREA`, `Shape_Leng`, `Shape_Le_1`, `SISL` are **all zero**;
- `Shape_Le_2` is partially zero and inconsistent with true projected area;
- `Shape_Le_3` is footprint area in **square degrees**, not metres.

So heights are inferred from footprint area alone, in `heights.py`:

| area (m²) | levels | height (m @ 3.0 m/level) |
|-----------|--------|--------------------------|
| < 150 | 1 | 3 |
| 150–300 | 2 | 6 |
| 300–600 | 3 | 9 |
| > 600 | 4 | 12 (capped — no towers in this AOI) |

Thresholds come from the observed distribution (median 164 m², p75 208, p95 417,
max 2180; ~29.7 buildings/tile — Vegas suburban sprawl). This is a **documented
assumption, not a measurement**. Replace it with a DSM or an OSM `building:levels`
join when one is available; `estimate_levels()` is the single symbol
`vectorize.py` imports, so swapping it requires no other change.

## Conventions inherited from Stage 1

- Filenames stay in lockstep via string `.replace()`:
  `RGB-PanSharpen_AOI_2_Vegas_img{N}.tif` ↔ `buildings_...geojson` ↔ `mask_...png`.
- `masks/` is the source of truth for which tiles exist.
- One CRS per split — `vectorize.py` aborts if tiles disagree rather than
  silently mixing coordinate systems.

## Known rough edges

- **3.7% of polygons are under 5 m²** (24.7% under 50 m²). On ground-truth masks
  these are real small structures plus raster speckle at building corners; on
  *predicted* masks they will be mostly noise. Raise `--min-area-px` for Unity
  output rather than trusting every polygon.
- `--simplify-px 0.75` applies Douglas-Peucker in pixel units to undo pixel
  stairstepping. Set to `0` if you need pixel-exact boundaries.
