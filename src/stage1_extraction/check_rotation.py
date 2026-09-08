"""
Diagnostic: checks whether SpaceNet image tiles have rotation/shear baked
into their affine transform, and whether the building CRS reprojection
is behaving as expected. Run this and paste the full output.
"""
import rasterio
import geopandas as gpd
from pathlib import Path
import random
import math

TRAIN_IMG_DIR = Path("E:/digital-twin-fyp/data/processed/train/images")
TRAIN_LABEL_DIR = Path("E:/digital-twin-fyp/data/processed/train/labels")

random.seed(1)
all_images = sorted(TRAIN_IMG_DIR.glob("*.tif"))
sample = random.sample(all_images, 8)

for img_path in sample:
    label_name = img_path.name.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")
    label_path = TRAIN_LABEL_DIR / label_name

    with rasterio.open(img_path) as src:
        t = src.transform
        img_crs = src.crs

    print(f"\n{img_path.name}")
    print(f"  transform: a={t.a:.6f} b={t.b:.6f} c={t.c:.2f} d={t.d:.6f} e={t.e:.6f} f={t.f:.2f}")

    # rotation angle implied by the transform, in degrees
    # (0 degrees = perfectly north-up, no rotation)
    rotation_deg = math.degrees(math.atan2(t.b, t.a))
    print(f"  implied rotation: {rotation_deg:.4f} degrees")
    print(f"  image CRS: {img_crs}")

    if label_path.exists():
        buildings = gpd.read_file(label_path)
        print(f"  buildings CRS (before reprojection): {buildings.crs}")
        print(f"  buildings count: {len(buildings)}")