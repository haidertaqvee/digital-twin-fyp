"""
Stage 4 / Unity Export — Generate 16-bit heightmap and landcover texture for Unity URP terrain.

Reads a georeferenced satellite tile and its vectorized building footprints with heights,
and outputs simulation-ready assets for Unity URP:
  1. heightmap.png: 16-bit grayscale PNG (uint16) with pixel values = height_m * scale.
  2. landcover.png: RGB PNG showing ground and buildings color-coded by vulnerability class.
  3. metadata.json: Georeferencing bounds, resolution, and Unity terrain setup parameters.

Usage:
    python src/export_unity.py --tile AOI_2_Vegas_img4174
    python src/export_unity.py --tile AOI_2_Vegas_img4174 --out-dir data/processed/unity_export
"""

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image
import rasterio
from rasterio.features import rasterize

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
DEFAULT_DEMO_DIR = DEFAULT_DATA_DIR / "demo_tiles"
DEFAULT_OUT_DIR = DEFAULT_DATA_DIR / "unity_export"
DEFAULT_TILE = "AOI_2_Vegas_img4174"

# 1 mm per height unit in uint16 (e.g. 9.0 m = 9000, max range ~65.5 m fits comfortably in 16-bit)
DEFAULT_HEIGHT_SCALE = 1000.0

VULN_COLORS = {
    "low": (16, 185, 129),      # Emerald #10b981
    "medium": (245, 158, 11),   # Amber #f59e0b
    "high": (239, 68, 68),      # Crimson #ef4444
    "default": (56, 189, 248),  # Sky blue #38bdf8
}
GROUND_COLOR = (30, 41, 59)     # Slate #1e293b


def parse_args():
    p = argparse.ArgumentParser(description="Export 16-bit heightmap and landcover mask for Unity")
    p.add_argument("--tile", default=DEFAULT_TILE, help="Tile name (e.g. AOI_2_Vegas_img4174)")
    p.add_argument("--split", default="test", help="Dataset split where TIF resides")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--height-scale", type=float, default=DEFAULT_HEIGHT_SCALE,
                   help="Scale factor for 16-bit heightmap (units per metre)")
    return p.parse_args()


def export_tile_assets(tile_name, tif_path, geojson_path, out_dir, height_scale):
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read TIF transform and dimensions
    with rasterio.open(tif_path) as src:
        transform = src.transform
        shape = src.shape  # (H, W)
        crs = src.crs
        bounds = src.bounds

    print(f"Loaded raster {tif_path.name}: {shape[1]}x{shape[0]} px, CRS {crs}")

    # 2. Read building GeoJSON
    gdf = gpd.read_file(geojson_path)
    if "height_m" not in gdf.columns:
        raise ValueError(f"No height_m column in {geojson_path}")

    print(f"Loaded {len(gdf)} building footprints from {geojson_path.name}")

    # 3. Burn heightmap (16-bit uint16)
    shapes = [(geom, float(h)) for geom, h in zip(gdf.geometry, gdf["height_m"])]
    height_raster = rasterize(shapes, out_shape=shape, transform=transform, fill=0.0, dtype=np.float32)

    max_h = float(height_raster.max())
    min_h = float(height_raster.min())
    print(f"Height range: {min_h:.1f} m to {max_h:.1f} m")

    uint16_heights = np.clip(height_raster * height_scale, 0, 65535).astype(np.uint16)
    heightmap_img = Image.fromarray(uint16_heights)
    heightmap_path = out_dir / f"{tile_name}_heightmap.png"
    heightmap_img.save(heightmap_path)
    print(f"Wrote 16-bit heightmap: {heightmap_path.name} ({heightmap_path.stat().st_size} bytes)")

    # 4. Burn landcover RGB texture
    # Create base ground texture
    rgb_arr = np.zeros((shape[0], shape[1], 3), dtype=np.uint8)
    rgb_arr[:, :] = GROUND_COLOR

    # Rasterize each vulnerability group
    for vclass, color in VULN_COLORS.items():
        if vclass == "default":
            continue
        subset = gdf[gdf.get("vuln_class", "") == vclass]
        if len(subset) == 0:
            continue
        mask = rasterize([(geom, 1) for geom in subset.geometry], out_shape=shape, transform=transform, fill=0, dtype=np.uint8)
        rgb_arr[mask == 1] = color

    landcover_img = Image.fromarray(rgb_arr)
    landcover_path = out_dir / f"{tile_name}_landcover.png"
    landcover_img.save(landcover_path)
    print(f"Wrote landcover texture: {landcover_path.name} ({landcover_path.stat().st_size} bytes)")

    # 5. Calculate physical footprint size in metres
    gdf_utm = gdf.to_crs("EPSG:32611")
    utm_bounds = gdf_utm.total_bounds
    width_m = float(utm_bounds[2] - utm_bounds[0]) if len(gdf) else 195.0
    height_m = float(utm_bounds[3] - utm_bounds[1]) if len(gdf) else 195.0

    # 6. Metadata and Unity setup guide
    metadata = {
        "tile": tile_name,
        "pixel_dimensions": {"width": shape[1], "height": shape[0]},
        "crs": str(crs),
        "bounds_wgs84": {
            "west": bounds.left,
            "south": bounds.bottom,
            "east": bounds.right,
            "north": bounds.top,
        },
        "approx_ground_size_m": {
            "width_x": round(width_m, 1),
            "length_z": round(height_m, 1),
            "max_height_y": round(max_h, 1),
        },
        "height_encoding": {
            "format": "16-bit Grayscale PNG (uint16)",
            "scale_units_per_metre": height_scale,
            "formula": "height_m = pixel_value / 1000.0",
        },
        "structures_count": len(gdf),
        "unity_urp_setup": {
            "terrain_width_x": 195.0,
            "terrain_length_z": 195.0,
            "terrain_height_y": round(max_h, 1),
            "heightmap_resolution": shape[1],
            "landcover_material": "URP Lit with landcover.png as Albedo",
        },
    }

    meta_path = out_dir / f"{tile_name}_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote Unity metadata: {meta_path.name}")

    return {
        "heightmap": str(heightmap_path),
        "landcover": str(landcover_path),
        "metadata": str(meta_path),
    }


def main():
    args = parse_args()
    tile = args.tile

    # Find TIF image
    tif_name = f"RGB-PanSharpen_{tile}.tif"
    tif_path = args.data_dir / args.split / "images" / tif_name
    if not tif_path.exists():
        raise SystemExit(f"Raster image not found: {tif_path}")

    # Find GeoJSON
    geojson_name = f"tile_{tile}.geojson"
    geojson_path = args.demo_dir / geojson_name
    if not geojson_path.exists():
        geojson_path = args.data_dir / args.split / "vectors" / "buildings_predictions.geojson"
        if not geojson_path.exists():
            raise SystemExit(f"Building vectors not found in {args.demo_dir} or vectors/")

    out_tile_dir = args.out_dir / tile
    print(f"Exporting Unity assets for {tile} to {out_tile_dir} ...")
    res = export_tile_assets(tile, tif_path, geojson_path, out_tile_dir, args.height_scale)
    print("Unity export complete:")
    for k, v in res.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
