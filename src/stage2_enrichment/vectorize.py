"""
Stage 2 — vectorize a binary building mask back into georeferenced polygons.

This is the exact inverse of `stage1_extraction/build_masks.py`, which turned
`buildings_*.geojson` footprints into 0/255 PNG masks by rasterizing them with
each tile's affine transform. Here we read that transform back off the paired
`.tif` and run `rasterio.features.shapes` on the mask, so every polygon lands
in the same EPSG:4326 coordinates the labels arrived in.

Works on ground-truth masks (`--source masks`) and on model predictions
(`--source predictions`) alike. Predictions need the cleanup that GT does not:
binary thresholding, small-area filtering, and Douglas-Peucker simplification
to undo the stairstepping that pixel boundaries introduce.

Typical use:
    python src/stage2_enrichment/vectorize.py --split test --source masks
    python src/stage2_enrichment/vectorize.py --split test --source predictions

Output: data/processed/<split>/vectors/buildings_<source>.geojson
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
from shapely.validation import make_valid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heights import LEVEL_HEIGHT_M, estimate_levels

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")

# Three pixels at 0.3 m/pixel is ~2.7 m^2 -- below this a blob is speckle from
# a misclassified shadow or roof edge, not a building.
DEFAULT_MIN_AREA_PX = 3
DEFAULT_SIMPLIFY_PX = 0.75


def parse_args():
    p = argparse.ArgumentParser(description="Vectorize building masks to georeferenced polygons")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--source", default="masks", choices=["masks", "predictions"],
                   help="masks = ground truth PNGs; predictions = model output PNGs.")
    p.add_argument("--pred-dir", type=Path, default=None,
                   help="Directory of prediction PNGs when --source predictions.")
    p.add_argument("--threshold", type=float, default=0.5,
                   help="Probability threshold applied to prediction PNGs.")
    p.add_argument("--min-area-px", type=float, default=DEFAULT_MIN_AREA_PX,
                   help="Drop polygons smaller than this many pixels.")
    p.add_argument("--simplify-px", type=float, default=DEFAULT_SIMPLIFY_PX,
                   help="Douglas-Peucker tolerance in pixels. 0 disables.")
    p.add_argument("--limit", type=int, default=0, help="Process only N tiles.")
    return p.parse_args()


def mask_to_polygons(mask, transform, min_area_px, simplify_px, threshold=None):
    """Binary mask -> list of shapely polygons in the raster's CRS.

    threshold is applied first for prediction masks, which are stored as
    0-255 probability PNGs rather than the hard 0/255 of the GT masks.
    """
    if threshold is not None:
        binary = (mask.astype(np.float32) / 255.0 >= threshold).astype(np.uint8)
    else:
        binary = (mask > 0).astype(np.uint8)

    if binary.sum() == 0:
        return []

    min_area_m2 = min_area_px * abs(transform.a * transform.e)

    polys = []
    for geom, value in shapes(binary, mask=binary, transform=transform, connectivity=8):
        if value != 1:
            continue
        poly = shape(geom)
        # shapes() can emit slivers and self-intersections at pixel corners.
        if not poly.is_valid:
            poly = make_valid(poly)
        if poly.is_empty or poly.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        if poly.area < min_area_m2:
            continue
        if simplify_px > 0:
            tol = simplify_px * abs(transform.a)
            poly = poly.simplify(tol, preserve_topology=True)
            if poly.is_empty or poly.area < min_area_m2:
                continue
        polys.append(poly)

    return polys


def vectorize_split(args):
    split_dir = args.data_dir / args.split
    img_dir = split_dir / "images"

    if args.source == "predictions":
        mask_dir = args.pred_dir or (split_dir / "predictions")
        threshold = args.threshold
    else:
        mask_dir = split_dir / "masks"
        threshold = None

    if not mask_dir.exists():
        raise SystemExit(
            f"No {args.source} directory at {mask_dir}.\n"
            + ("Run the inference script first to produce prediction PNGs."
               if args.source == "predictions"
               else "Run build_masks.py first.")
        )

    mask_paths = sorted(mask_dir.glob("*.png"))
    if args.limit:
        mask_paths = mask_paths[: args.limit]
    if not mask_paths:
        raise SystemExit(f"No PNG masks found in {mask_dir}.")

    print(f"--- {args.split.upper()} ({args.source}) ---")
    print(f"Vectorizing {len(mask_paths)} tiles from {mask_dir}")

    records = []
    empty_tiles = 0
    crs_seen = None

    for mask_path in mask_paths:
        # mask_<...>.png -> RGB-PanSharpen_<...>.tif, the same .replace()
        # convention build_masks.py and dataset.py use.
        img_name = mask_path.name.replace("mask_", "RGB-PanSharpen_").replace(".png", ".tif")
        img_path = img_dir / img_name
        if not img_path.exists():
            raise SystemExit(
                f"Mask {mask_path.name} has no paired image.\n  Expected: {img_path}\n"
                "Filename prefixes must stay in lockstep (see CLAUDE.md)."
            )

        with rasterio.open(img_path) as src:
            transform = src.transform
            crs = src.crs
            if crs_seen is not None and crs != crs_seen:
                raise SystemExit(
                    f"CRS mismatch across tiles: {crs_seen} vs {crs} at {img_path.name}. "
                    "Vectorization assumes one CRS for the whole split."
                )
            crs_seen = crs

        from PIL import Image
        mask = np.array(Image.open(mask_path))
        if mask.ndim == 3:
            mask = mask[..., 0]

        polys = mask_to_polygons(
            mask, transform, args.min_area_px, args.simplify_px, threshold=threshold
        )
        if not polys:
            empty_tiles += 1

        for poly in polys:
            records.append(
                {
                    "tile": mask_path.stem.replace("mask_", ""),
                    "geometry": poly,
                }
            )

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=crs_seen)
    gdf["area_m2"] = gdf.to_crs("EPSG:32611").geometry.area
    gdf["levels"] = estimate_levels(gdf["area_m2"])
    gdf["height_m"] = gdf["levels"] * LEVEL_HEIGHT_M

    out_dir = split_dir / "vectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"buildings_{args.source}.geojson"
    gdf.to_file(out_path, driver="GeoJSON")

    print(f"Polygons: {len(gdf)} across {len(mask_paths) - empty_tiles} tiles "
          f"({empty_tiles} empty)")
    if len(gdf):
        print(f"Area m^2: median {gdf['area_m2'].median():.1f} | "
              f"levels {gdf['levels'].value_counts().sort_index().to_dict()}")
    print(f"Wrote {out_path}")
    return gdf


if __name__ == "__main__":
    vectorize_split(parse_args())
