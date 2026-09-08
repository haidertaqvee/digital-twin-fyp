import re
import random
import shutil
from pathlib import Path

# ---- Config ----
RAW_DIR = Path("E:/digital-twin-fyp/data/raw/AOI_2_Vegas_Train")
IMG_DIR = RAW_DIR / "RGB-PanSharpen"
LABEL_DIR = RAW_DIR / "geojson" / "buildings"

OUT_DIR = Path("E:/digital-twin-fyp/data/processed")
SUBSET_SIZE = 999
SEED = 42  # fixed seed = reproducible subset every time we run this

TRAIN_FRAC = 0.7
VAL_FRAC = 0.15
# remaining 0.15 goes to test


def main():
    # ---- Step 1: find all image files and extract their tile number ----
    pattern = re.compile(r"RGB-PanSharpen_AOI_2_Vegas_img(\d+)\.tif")

    pairs = []
    for img_path in IMG_DIR.glob("*.tif"):
        match = pattern.match(img_path.name)
        if not match:
            continue
        tile_id = match.group(1)
        label_path = LABEL_DIR / f"buildings_AOI_2_Vegas_img{tile_id}.geojson"
        if label_path.exists():
            pairs.append((tile_id, img_path, label_path))

    print(f"Found {len(pairs)} valid image-label pairs")

    # ---- Step 2: randomly sample our subset (reproducible via seed) ----
    random.seed(SEED)
    random.shuffle(pairs)
    subset = pairs[:SUBSET_SIZE]
    print(f"Selected {len(subset)} tiles for our working subset")

    # ---- Step 3: split into train/val/test ----
    n_train = int(len(subset) * TRAIN_FRAC)
    n_val = int(len(subset) * VAL_FRAC)

    train_set = subset[:n_train]
    val_set = subset[n_train:n_train + n_val]
    test_set = subset[n_train + n_val:]

    print(f"Train: {len(train_set)} | Val: {len(val_set)} | Test: {len(test_set)}")

    # ---- Step 4: copy files into organized folders ----
    copy_split("train", train_set)
    copy_split("val", val_set)
    copy_split("test", test_set)

    print("Done. Files copied to:", OUT_DIR)


# ---- Helper ----
def copy_split(split_name, items):
    img_out = OUT_DIR / split_name / "images"
    label_out = OUT_DIR / split_name / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)

    for tile_id, img_path, label_path in items:
        shutil.copy(img_path, img_out / img_path.name)
        shutil.copy(label_path, label_out / label_path.name)


if __name__ == "__main__":
    main()