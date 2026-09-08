"""
Train the building-footprint U-Net (segmentation_models_pytorch, ResNet34
backbone) on the prepared SpaceNet splits.

Primary training script for TerraTwin. Fallback: `train.py` + `model.py`
(custom from-scratch UNet with AMP/resume/scheduler). This script is chosen
as primary because the ImageNet-pretrained encoder learns building footprints
faster on the small (673-tile) training set.

Runs unchanged with the local E:/digital-twin-fyp/... defaults. Pass
--data-dir / --ckpt-dir to point at a different layout (e.g. the AMD cloud
fallback, or after moving data) without editing the file.

Local smoke test (GTX 1660 Super, ~minutes):
    python src/stage1_extraction/train_unet.py --epochs 1 --limit 4

Full run (~1-1.5h on 1660 Super at batch 8):
    python src/stage1_extraction/train_unet.py --epochs 15
"""

import argparse
import random

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
import segmentation_models_pytorch as smp
from tqdm import tqdm
from pathlib import Path

from dataset import SpaceNetDataset

# ------------------------------------------------------------------
# 1. CLI arguments (defaults keep the original local behaviour)
# ------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Train U-Net (smp ResNet34) on SpaceNet masks")
    p.add_argument("--data-dir", type=Path, default="E:/digital-twin-fyp/data/processed",
                   help="Root holding {train,val}/{images,masks}.")
    p.add_argument("--ckpt-dir", type=Path, default="E:/digital-twin-fyp/models",
                   help="Where checkpoints are written.")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--batch-size", type=int, default=8,
                   help="8 fits in 6 GB VRAM (GTX 1660 Super). Drop to 4 on OOM.")
    p.add_argument("--tile-size", type=int, default=512)
    p.add_argument("--num-workers", type=int, default=2,
                   help="Raise on Linux/cloud.")
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--limit", type=int, default=0,
                   help="Use only N tiles per split. For smoke tests.")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


# ------------------------------------------------------------------
# 2. Device Setup
# ------------------------------------------------------------------
# PyTorch ROCm (AMD MI300X) and CUDA (GTX 1660 Super) both use torch.cuda.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ------------------------------------------------------------------
# 3. Compound Loss (BCE + Soft Dice)
# ------------------------------------------------------------------
class BCEDiceLoss(nn.Module):
    def __init__(self, smooth=1.0):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.smooth = smooth

    def forward(self, logits, targets):
        bce_loss = self.bce(logits, targets)
        probs = torch.sigmoid(logits)
        
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)
        intersection = (probs_flat * targets_flat).sum()
        
        dice_loss = 1.0 - (2.0 * intersection + self.smooth) / (
            probs_flat.sum() + targets_flat.sum() + self.smooth
        )
        return bce_loss + dice_loss

# ------------------------------------------------------------------
# 4. Metric Evaluation (IoU & F1/Dice Score)
# ------------------------------------------------------------------
def compute_metrics(logits, targets, threshold=0.5, eps=1e-7):
    preds = (torch.sigmoid(logits) > threshold).float()
    intersection = (preds * targets).sum().item()
    total_pred = preds.sum().item()
    total_target = targets.sum().item()
    union = total_pred + total_target - intersection

    iou = (intersection + eps) / (union + eps)
    f1 = (2.0 * intersection + eps) / (total_pred + total_target + eps)
    return iou, f1

# ------------------------------------------------------------------
# 5. Training & Validation Pipelines
# ------------------------------------------------------------------
def build_loader(args, split, augment):
    ds = SpaceNetDataset(
        image_dir=args.data_dir / split / "images",
        mask_dir=args.data_dir / split / "masks",
        tile_size=args.tile_size,
        augment=augment,
    )
    if not len(ds):
        raise SystemExit(
            f"No masks found for split '{split}' under {args.data_dir / split / 'masks'}.\n"
            "Run build_subset.py then build_masks.py first."
        )
    if args.limit:
        ds = Subset(ds, range(min(args.limit, len(ds))))

    return DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=augment,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=augment and len(ds) > args.batch_size,
    )


def run_training(args):
    torch.manual_seed(args.seed)
    random.seed(args.seed)
    args.ckpt_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.ckpt_dir / "unet_resnet34_best.pth"

    print(f"--> Initializing training pipeline on device: {DEVICE}")
    print(f"    data-dir: {args.data_dir} | ckpt-dir: {args.ckpt_dir}")
    if DEVICE.type == "cpu":
        print("    WARNING: no GPU visible -- expect this to be very slow at 512px.")

    train_loader = build_loader(args, "train", augment=True)
    val_loader = build_loader(args, "val", augment=False)
    print(f"Loaded {len(train_loader.dataset)} train tiles | {len(val_loader.dataset)} validation tiles.")

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1
    ).to(DEVICE)

    criterion = BCEDiceLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    best_val_iou = 0.0

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        loop = tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs} [Train]", leave=False)

        for images, masks in loop:
            images = images.to(DEVICE, non_blocking=True)
            masks = masks.to(DEVICE, non_blocking=True)

            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, masks)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

        avg_train_loss = train_loss / len(train_loader)

        # Validation Phase
        model.eval()
        val_loss = 0.0
        total_iou = 0.0
        total_f1 = 0.0

        with torch.no_grad():
            for images, masks in val_loader:
                images = images.to(DEVICE, non_blocking=True)
                masks = masks.to(DEVICE, non_blocking=True)

                logits = model(images)
                loss = criterion(logits, masks)
                val_loss += loss.item()

                batch_iou, batch_f1 = compute_metrics(logits, masks)
                total_iou += batch_iou
                total_f1 += batch_f1

        avg_val_loss = val_loss / len(val_loader)
        avg_val_iou = total_iou / len(val_loader)
        avg_val_f1 = total_f1 / len(val_loader)

        print(
            f"Epoch {epoch:02d}/{args.epochs:02d} | "
            f"Train Loss: {avg_train_loss:.4f} | "
            f"Val Loss: {avg_val_loss:.4f} | "
            f"Val IoU: {avg_val_iou:.4f} | "
            f"Val F1: {avg_val_f1:.4f}"
        )

        # Save Best Checkpoint
        if avg_val_iou > best_val_iou:
            best_val_iou = avg_val_iou
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_iou": avg_val_iou,
                "val_f1": avg_val_f1,
                "args": vars(args),
            }, checkpoint_path)
            print(f"  --> [Saved Checkpoint] New best Val IoU: {best_val_iou:.4f} to {checkpoint_path}")

if __name__ == "__main__":
    run_training(parse_args())