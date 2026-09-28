import torch
from torch.utils.data import Dataset, DataLoader
import rasterio
import numpy as np
from PIL import Image
from pathlib import Path

# Fixed, dataset-wide normalization ceiling — derived from check_pixel_stats.py
# (95th percentile of per-tile maxima across a 100-tile sample).
# DO NOT compute this per-image. Every tile must be scaled against the SAME
# number, or the model sees inconsistent brightness for the same real material.
NORM_MAX = 1910.0


class SpaceNetDataset(Dataset):
    """
    Args:
        image_dir, mask_dir: the paired directories under data/processed/<split>/.
        tile_size: if set, return square crops of this size instead of whole
            650x650 tiles -- random crops when augment=True, center crops
            otherwise. Smaller crops mean bigger batches and more gradient
            steps per epoch, which matters with only ~673 training tiles.
        augment: horizontal/vertical flips plus 90-degree rotations, applied
            identically to image and mask. Valid here because overhead
            satellite imagery has no canonical up direction.

    Both default to the original whole-tile, no-augmentation behaviour, so
    existing callers are unaffected.
    """

    def __init__(self, image_dir, mask_dir, tile_size=None, augment=False):
        self.image_dir = Path(image_dir)
        self.mask_dir = Path(mask_dir)
        self.tile_size = tile_size
        self.augment = augment

        # We only list masks, since we already filtered out bad tiles in build_masks.py
        self.masks = sorted(self.mask_dir.glob("*.png"))

    def __len__(self):
        return len(self.masks)

    def _crop(self, image, mask):
        """Crop image and mask to self.tile_size at the same offset."""
        _, h, w = image.shape
        size = self.tile_size

        # Tiles smaller than the requested crop get reflect-padded up to it.
        if h < size or w < size:
            pad_h, pad_w = max(0, size - h), max(0, size - w)
            padding = [0, pad_w, 0, pad_h]
            image = torch.nn.functional.pad(image, padding, mode="reflect")
            mask = torch.nn.functional.pad(mask, padding, mode="reflect")
            _, h, w = image.shape

        if self.augment:
            top = int(torch.randint(0, h - size + 1, (1,)).item())
            left = int(torch.randint(0, w - size + 1, (1,)).item())
        else:
            top, left = (h - size) // 2, (w - size) // 2

        return (
            image[:, top : top + size, left : left + size],
            mask[:, top : top + size, left : left + size],
        )

    def _augment(self, image, mask):
        """Flips and 90-degree rotations, applied identically to both tensors."""
        if torch.rand(1).item() < 0.5:
            image, mask = torch.flip(image, [2]), torch.flip(mask, [2])
        if torch.rand(1).item() < 0.5:
            image, mask = torch.flip(image, [1]), torch.flip(mask, [1])

        turns = int(torch.randint(0, 4, (1,)).item())
        if turns:
            image = torch.rot90(image, turns, dims=[1, 2])
            mask = torch.rot90(mask, turns, dims=[1, 2])

        # rot90/flip return views; the collate step needs contiguous memory.
        return image.contiguous(), mask.contiguous()

    def __getitem__(self, idx):
        mask_path = self.masks[idx]

        # Reverse-engineer the image filename from the mask filename
        img_filename = mask_path.name.replace("mask_", "RGB-PanSharpen_").replace(".png", ".tif")
        img_path = self.image_dir / img_filename
        if not img_path.exists():
            raise FileNotFoundError(
                f"Dataset mismatch: mask {mask_path.name} has no paired image.\n"
                f"  Expected: {img_path}\n"
                "  The mask exists in masks/ but the matching image is missing from images/.\n"
                "  Check that build_subset.py and build_masks.py completed without interruption."
            )

        # 1. Load and normalize image using a FIXED dataset-wide scale
        with rasterio.open(img_path) as src:
            image = src.read([1, 2, 3])  # (Channels, Height, Width)
            image = image.astype(np.float32)

            # Clip first (kills rare glare/sensor-noise outlier pixels),
            # then scale by the same constant for every tile in the dataset.
            image = np.clip(image, 0, NORM_MAX)
            image = image / NORM_MAX

        # 2. Load and Normalize Mask
        mask = np.array(Image.open(mask_path), dtype=np.float32)
        mask = mask / 255.0  # Convert from 0/255 to 0/1 for binary cross-entropy loss

        # 3. Convert to PyTorch Tensors
        image_tensor = torch.from_numpy(image)
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)  # Add channel dim -> (1, H, W)

        # 4. Optional crop and augmentation (both no-ops by default)
        if self.tile_size is not None:
            image_tensor, mask_tensor = self._crop(image_tensor, mask_tensor)
        if self.augment:
            image_tensor, mask_tensor = self._augment(image_tensor, mask_tensor)

        return image_tensor, mask_tensor


# Quick test to verify the dataloader works if you run this file directly
if __name__ == "__main__":
    IMG_DIR = "E:/digital-twin-fyp/data/processed/train/images"
    MASK_DIR = "E:/digital-twin-fyp/data/processed/train/masks"

    dataset = SpaceNetDataset(IMG_DIR, MASK_DIR)
    print(f"Total dataset size: {len(dataset)} valid pairs")

    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    images, masks = next(iter(dataloader))
    print(f"Batch Image Tensor Shape: {images.shape} -> (Batch, Channels, Height, Width)")
    print(f"Batch Mask Tensor Shape: {masks.shape} -> (Batch, Channels, Height, Width)")

    # Sanity check: confirm the normalized values actually land in [0, 1]
    print(f"Image tensor min/max after normalization: {images.min():.3f} / {images.max():.3f}")
    print("Environment ready for model training.")