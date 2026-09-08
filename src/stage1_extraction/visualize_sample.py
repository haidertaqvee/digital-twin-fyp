import matplotlib.pyplot as plt
import rasterio
import geopandas as gpd
from pathlib import Path

TRAIN_IMG_DIR = Path("E:/digital-twin-fyp/data/processed/train/images")
TRAIN_LABEL_DIR = Path("E:/digital-twin-fyp/data/processed/train/labels")

IMG_PATH = sorted(TRAIN_IMG_DIR.glob("*.tif"))[0]
tile_name = IMG_PATH.name.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")
LABEL_PATH = TRAIN_LABEL_DIR / tile_name

print(f"Using image: {IMG_PATH.name}")

with rasterio.open(IMG_PATH) as src:
    image = src.read([1, 2, 3])
    image = image.transpose(1, 2, 0)
    bounds = src.bounds  # real-world geographic extent of this image

image = image.astype(float)
image = (image - image.min()) / (image.max() - image.min())

extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

buildings = gpd.read_file(LABEL_PATH)
print(f"Number of buildings in this tile: {len(buildings)}")

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

axes[0].imshow(image, extent=extent)
axes[0].set_title("Satellite image (RGB)")
axes[0].axis("off")

axes[1].imshow(image, extent=extent)
buildings.plot(ax=axes[1], facecolor="none", edgecolor="red", linewidth=1.5)
axes[1].set_title("Image + building footprints overlaid")
axes[1].axis("off")

plt.tight_layout()
plt.savefig("E:/digital-twin-fyp/notebooks/sample_check.png", dpi=150)
print("Saved visualization to notebooks/sample_check.png")
plt.show()
