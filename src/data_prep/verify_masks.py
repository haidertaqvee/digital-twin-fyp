import rasterio
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from PIL import Image
import random

TRAIN_IMG_DIR = Path("E:/digital-twin-fyp/data/processed/train/images")
MASK_OUT_DIR = Path("E:/digital-twin-fyp/data/processed/train/masks")


def verify_alignment():
    mask_files = list(MASK_OUT_DIR.glob("*.png"))
    if not mask_files:
        print("No masks found in the directory.")
        return

    sample_mask_path = random.choice(mask_files)

    img_filename = sample_mask_path.name.replace("mask_", "RGB-PanSharpen_").replace(".png", ".tif")
    sample_img_path = TRAIN_IMG_DIR / img_filename

    if not sample_img_path.exists():
        print(f"Could not find matching image: {sample_img_path}")
        return

    with rasterio.open(sample_img_path) as src:
        img_data = src.read([1, 2, 3])
        img_data = img_data.transpose(1, 2, 0)
        img_data = img_data.astype(float)
        img_data = (img_data - img_data.min()) / (img_data.max() - img_data.min())

    mask_data = np.array(Image.open(sample_mask_path))

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

    ax1.imshow(img_data)
    ax1.set_title(f"Original Image\n{img_filename}")
    ax1.axis("off")

    ax2.imshow(mask_data, cmap='gray')
    ax2.set_title("Generated Mask (255 = Building, 0 = Background)")
    ax2.axis("off")

    # Fixed solid red overlay, built manually as an RGBA array instead of
    # using a colormap. This guarantees buildings are ALWAYS the same red,
    # with alpha=0 (fully transparent) on background pixels and alpha=0.5
    # on building pixels. No colormap scaling involved, so no risk of the
    # color shifting between figures.
    red_overlay = np.zeros((*mask_data.shape, 4), dtype=float)  # (H, W, RGBA)
    red_overlay[..., 0] = 1.0   # R
    red_overlay[..., 1] = 0.0   # G
    red_overlay[..., 2] = 0.0   # B
    red_overlay[..., 3] = np.where(mask_data > 0, 0.5, 0.0)  # alpha: visible only on buildings

    ax3.imshow(img_data)
    ax3.imshow(red_overlay)
    ax3.set_title("Alignment Overlay Check")
    ax3.axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    verify_alignment()