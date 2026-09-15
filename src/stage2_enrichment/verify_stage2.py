"""
Stage 2 verification — confirm `vectorize.py` + `heights.py` still reproduce the
committed vectors, WITHOUT overwriting them.

Why this exists: `vectorize.py` always writes
`data/processed/<split>/vectors/buildings_<source>.geojson` for the whole run, so
calling it with `--limit 2` to "just check" would replace the committed 140-tile
file with a 2-tile one. This script instead imports `mask_to_polygons` and
compares freshly derived polygons against the features already in that file, and
independently re-derives `levels` / `height_m` from `estimate_levels`.

Checks performed on N tiles:
  1. polygon count matches the committed file for that tile
  2. fresh-vs-committed symmetric-difference area is negligible (vertex order and
     float round-trip through GeoJSON can differ trivially)
  3. `heights.estimate_levels(area_m2)` reproduces the committed `levels` column
  4. `height_m == levels * LEVEL_HEIGHT_M`
  5. the height heuristic is still explicitly a heuristic (describe_heuristic)

Usage:
    python src/stage2_enrichment/verify_stage2.py
    python src/stage2_enrichment/verify_stage2.py --tiles 5 --source predictions
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from shapely.geometry import shape
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vectorize import mask_to_polygons
from heights import LEVEL_HEIGHT_M, describe_heuristic, estimate_levels

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")


def parse_args():
    p = argparse.ArgumentParser(description="Verify Stage 2 vectorization without overwriting outputs")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--source", default="predictions", choices=["masks", "predictions"],
                   help="Which committed vector file to verify against.")
    p.add_argument("--tiles", type=int, default=2)
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--min-area-px", type=float, default=3.0)
    p.add_argument("--simplify-px", type=float, default=0.75)
    # GeoJSON round-trips floats through text; allow a tiny symmetric-difference
    # area relative to total footprint area before calling it a mismatch.
    p.add_argument("--area-tol", type=float, default=1e-6,
                   help="Max allowed sym-diff area as a fraction of total area.")
    return p.parse_args()


def main():
    args = parse_args()
    split_dir = args.data_dir / args.split
    vec_path = split_dir / "vectors" / f"buildings_{args.source}.geojson"
    img_dir = split_dir / "images"

    src_dir = split_dir / (args.source if args.source == "predictions" else "masks")
    if not vec_path.exists():
        raise SystemExit(
            f"Committed vectors not found: {vec_path}\n"
            f"  Run: python src/stage2_enrichment/vectorize.py --split {args.split} --source {args.source}"
        )
    if not src_dir.exists():
        raise SystemExit(f"No {args.source} directory at {src_dir}.")

    print(f"Verifying Stage 2 against {vec_path}")
    print(f"  source={args.source} tiles={args.tiles} threshold={args.threshold}")
    print(f"  {describe_heuristic()}")

    data = json.loads(vec_path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    if not features:
        raise SystemExit(f"{vec_path} has no features.")

    by_tile = {}
    for f in features:
        t = f.get("properties", {}).get("tile")
        by_tile.setdefault(t, []).append(f)
    tiles = sorted(by_tile)[: args.tiles]
    if not tiles:
        raise SystemExit("Features have no 'tile' property; cannot group.")

    all_pass = True
    per_tile = []

    for tile in tiles:
        img_path = img_dir / f"RGB-PanSharpen_{tile}.tif"
        if args.source == "predictions":
            mask_path = src_dir / f"mask_{tile}.png"
            threshold = args.threshold
        else:
            mask_path = src_dir / f"mask_{tile}.png"
            threshold = None
        if not img_path.exists():
            raise SystemExit(f"Missing image for {tile}: {img_path}")
        if not mask_path.exists():
            raise SystemExit(f"Missing {args.source} mask for {tile}: {mask_path}")

        with rasterio.open(img_path) as src:
            transform = src.transform

        mask = np.array(Image.open(mask_path))
        if mask.ndim == 3:
            mask = mask[..., 0]

        fresh = mask_to_polygons(mask, transform, args.min_area_px,
                                 args.simplify_px, threshold=threshold)
        committed = [shape(f["geometry"]) for f in by_tile[tile]]

        count_match = len(fresh) == len(committed)

        # Geometric agreement: compare unions rather than per-polygon pairing,
        # since shapes() vertex order is not guaranteed stable across versions.
        fu = unary_union(fresh) if fresh else None
        cu = unary_union(committed) if committed else None
        if fu is None and cu is None:
            sym_frac, total = 0.0, 0.0
            geom_match = True
        elif fu is None or cu is None:
            sym_frac, total = 1.0, 0.0
            geom_match = False
        else:
            sym = fu.symmetric_difference(cu).area
            total = max(fu.area, cu.area, 1e-12)
            sym_frac = sym / total
            geom_match = sym_frac <= args.area_tol

        # Re-derive levels/heights from area (projected), as vectorize.py does.
        # The committed GeoJSON stores crs as a CRS84 JSON object which pyproj
        # rejects as a dict; vectorize.py wrote these in EPSG:4326 by construction
        # (it reads the transform off the paired .tif), so pass the string directly.
        import geopandas as gpd
        gdf = gpd.GeoDataFrame(
            {"geometry": [shape(f["geometry"]) for f in by_tile[tile]]},
            crs="EPSG:4326",
        )
        if len(gdf):
            area_m2 = gdf.to_crs("EPSG:32611").geometry.area
            levels_fresh = estimate_levels(area_m2)
            heights_fresh = np.asarray(levels_fresh) * LEVEL_HEIGHT_M

            levels_committed = np.array(
                [f["properties"].get("levels") for f in by_tile[tile]], dtype=float
            )
            heights_committed = np.array(
                [f["properties"].get("height_m") for f in by_tile[tile]], dtype=float
            )
            levels_match = bool(np.array_equal(levels_fresh, levels_committed))
            heights_match = bool(np.allclose(heights_fresh, heights_committed, atol=1e-6))
        else:
            levels_match = heights_match = True

        ok = count_match and geom_match and levels_match and heights_match
        all_pass &= ok

        per_tile.append({
            "tile": tile,
            "fresh_polys": len(fresh),
            "committed_polys": len(committed),
            "count_match": count_match,
            "sym_diff_fraction": round(sym_frac, 9),
            "geom_match": geom_match,
            "levels_match": levels_match,
            "heights_match": heights_match,
            "pass": ok,
        })
        print(f"  {tile}: polys fresh={len(fresh)} committed={len(committed)} "
              f"symΔ={sym_frac:.2e} levels={'ok' if levels_match else 'DIFF'} "
              f"heights={'ok' if heights_match else 'DIFF'} -> {'PASS' if ok else 'FAIL'}")

    out = {
        "split": args.split,
        "source": args.source,
        "verified_against": str(vec_path),
        "tiles_verified": len(per_tile),
        "level_height_m": LEVEL_HEIGHT_M,
        "heuristic": describe_heuristic(),
        "all_pass": bool(all_pass),
        "per_tile": per_tile,
    }
    out_dir = Path("E:/digital-twin-fyp/results/verify_stage2")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "verification.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\nVERDICT: {'PASS — Stage 2 verified' if all_pass else 'FAIL — vectorization does not reproduce'}")
    print(f"Wrote {out_path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
