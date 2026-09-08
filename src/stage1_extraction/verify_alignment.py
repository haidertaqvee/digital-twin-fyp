import matplotlib.pyplot as plt
import rasterio
import geopandas as gpd
from pathlib import Path

TRAIN_IMG_DIR = Path("E:/digital-twin-fyp/data/processed/train/images")
TRAIN_LABEL_DIR = Path("E:/digital-twin-fyp/data/processed/train/labels")

TARGET_NAME = "RGB-PanSharpen_AOI_2_Vegas_img1489.tif"
IMG_PATH = TRAIN_IMG_DIR / TARGET_NAME
LABEL_PATH = TRAIN_LABEL_DIR / TARGET_NAME.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")

if not IMG_PATH.exists():
    IMG_PATH = sorted(TRAIN_IMG_DIR.glob("*.tif"))[0]
    LABEL_PATH = TRAIN_LABEL_DIR / IMG_PATH.name.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")
    print(f"img1489 not in train split, using {IMG_PATH.name} instead")

with rasterio.open(IMG_PATH) as src:
    image = src.read([1, 2, 3])
    image = image.transpose(1, 2, 0)
    bounds = src.bounds
    raster_crs = src.crs

image = image.astype(float)
image = (image - image.min()) / (image.max() - image.min())
extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

buildings = gpd.read_file(LABEL_PATH)

print(f"Raster CRS:    {raster_crs}")
print(f"GeoJSON CRS:   {buildings.crs}")
print(f"CRS match:     {raster_crs == buildings.crs}")
print(f"Raster bounds: {bounds}")
print(f"Building bounds: {buildings.total_bounds}")

if buildings.crs != raster_crs:
    print(">>> MISMATCH DETECTED - reprojecting buildings to raster CRS")
    buildings = buildings.to_crs(raster_crs)

fig, axes = plt.subplots(1, 2, figsize=(14, 7))

axes[0].imshow(image, extent=extent)
axes[0].set_title(f"{IMG_PATH.stem} - Full tile ({len(buildings)} buildings)")
axes[0].axis("off")

axes[1].imshow(image, extent=extent)
buildings.plot(ax=axes[1], facecolor="none", edgecolor="red", linewidth=1.2, aspect=None)
axes[1].set_title("With building overlay (after CRS check)")
axes[1].axis("off")

plt.tight_layout()
plt.savefig("E:/digital-twin-fyp/notebooks/alignment_check.png", dpi=200)
print("Saved to notebooks/alignment_check.png")

if len(buildings) > 0:
    b0 = buildings.iloc[0]
    minx, miny, maxx, maxy = b0.geometry.bounds
    pad = (maxx - minx) * 2

    fig2, ax2 = plt.subplots(figsize=(8, 8))
    ax2.imshow(image, extent=extent)
    buildings.plot(ax=ax2, facecolor="none", edgecolor="red", linewidth=2, aspect=None)
    ax2.set_xlim(minx - pad, maxx + pad)
    ax2.set_ylim(miny - pad, maxy + pad)
    ax2.set_title("Zoomed: first building, close inspection")
    plt.savefig("E:/digital-twin-fyp/notebooks/alignment_check_zoom.png", dpi=200)
    print("Saved zoomed view to notebooks/alignment_check_zoom.png")

plt.show()
