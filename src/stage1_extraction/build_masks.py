import rasterio
from rasterio.features import rasterize
import geopandas as gpd
import numpy as np
from pathlib import Path
from PIL import Image

BASE_DIR = Path("E:/digital-twin-fyp/data/processed")


def build_masks_for_split(split_name: str):
    """Generate rasterized building masks for one split (train/val/test)."""
    img_dir = BASE_DIR / split_name / "images"
    label_dir = BASE_DIR / split_name / "labels"
    mask_out_dir = BASE_DIR / split_name / "masks"
    mask_out_dir.mkdir(parents=True, exist_ok=True)

    all_images = sorted(img_dir.glob("*.tif"))
    print(f"\n--- {split_name.upper()} ---")
    print(f"Found {len(all_images)} image tiles")

    skipped_nodata = 0
    skipped_missing_label = 0
    made = 0

    for img_path in all_images:
        label_name = img_path.name.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")
        label_path = label_dir / label_name

        if not label_path.exists():
            skipped_missing_label += 1
            continue

        with rasterio.open(img_path) as src:
            transform = src.transform
            out_shape = (src.height, src.width)
            img_crs = src.crs
            img_data = src.read([1, 2, 3])

            nodata_fraction = np.mean(np.all(img_data == 0, axis=0))
            if nodata_fraction > 0.15:
                skipped_nodata += 1
                continue

        buildings = gpd.read_file(label_path)

        if buildings.empty:
            mask = np.zeros(out_shape, dtype=np.uint8)
        else:
            if buildings.crs != img_crs:
                buildings = buildings.to_crs(img_crs)

            shapes = [(geom, 1) for geom in buildings.geometry if geom is not None and not geom.is_empty]
            mask = rasterize(
                shapes,
                out_shape=out_shape,
                transform=transform,
                fill=0,
                dtype=np.uint8,
            )

        mask_path = mask_out_dir / img_path.name.replace("RGB-PanSharpen_", "mask_").replace(".tif", ".png")
        Image.fromarray(mask * 255).save(mask_path)
        made += 1

    print(f"Masks created: {made}")
    print(f"Skipped (mostly no-data): {skipped_nodata}")
    print(f"Skipped (missing label file): {skipped_missing_label}")
    return made, skipped_nodata, skipped_missing_label


if __name__ == "__main__":
    totals = {"made": 0, "nodata": 0, "missing": 0}

    for split in ["train", "val", "test"]:
        made, nodata, missing = build_masks_for_split(split)
        totals["made"] += made
        totals["nodata"] += nodata
        totals["missing"] += missing

    print("\n=== TOTAL ACROSS ALL SPLITS ===")
    print(f"Masks created: {totals['made']}")
    print(f"Skipped (mostly no-data): {totals['nodata']}")
    print(f"Skipped (missing label file): {totals['missing']}")