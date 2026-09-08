import matplotlib.pyplot as plt
import rasterio
import geopandas as gpd
import random
from pathlib import Path

TRAIN_IMG_DIR = Path("E:/digital-twin-fyp/data/processed/train/images")
TRAIN_LABEL_DIR = Path("E:/digital-twin-fyp/data/processed/train/labels")

random.seed(7)
all_images = sorted(TRAIN_IMG_DIR.glob("*.tif"))
sample_images = random.sample(all_images, 6)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for ax, img_path in zip(axes, sample_images):
    tile_name = img_path.name.replace("RGB-PanSharpen_", "buildings_").replace(".tif", ".geojson")
    label_path = TRAIN_LABEL_DIR / tile_name

    with rasterio.open(img_path) as src:
        image = src.read([1, 2, 3])
        image = image.transpose(1, 2, 0)
        bounds = src.bounds

    image = image.astype(float)
    image = (image - image.min()) / (image.max() - image.min())
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    buildings = gpd.read_file(label_path)

    ax.imshow(image, extent=extent)
    ax.set_aspect("equal")  # set this ourselves BEFORE plotting buildings, to avoid geopandas' buggy auto-calculation

    if not buildings.empty:
        buildings.plot(ax=ax, facecolor="none", edgecolor="red", linewidth=1, aspect=None)

    ax.set_title(f"{img_path.stem}\n({len(buildings)} buildings)", fontsize=10)
    ax.axis("off")

plt.tight_layout()
plt.savefig("E:/digital-twin-fyp/notebooks/sample_grid.png", dpi=150)
print("Saved grid of 6 sample tiles to notebooks/sample_grid.png")
plt.show()
