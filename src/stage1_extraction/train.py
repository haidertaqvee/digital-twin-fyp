"""
Train the building-footprint U-Net on the prepared SpaceNet splits.

Designed to survive a dropped cloud session: every epoch writes last.pt, and
--resume picks up from it (model, optimizer, scaler, scheduler, epoch, best
score). Relevant when renting a GPU by the hour.

Typical run:
    python src/stage1_extraction/train.py --epochs 60 --tile-size 512 --batch-size 8

Smoke test first (two epochs over a handful of tiles):
    python src/stage1_extraction/train.py --epochs 2 --limit 16 --batch-size 2
"""

import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset

from dataset import SpaceNetDataset
from model import UNet

DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
CKPT_DIR = Path("E:/digital-twin-fyp/models")


def parse_args():
    p = argparse.ArgumentParser(description="Train U-Net on SpaceNet building masks")
    p.add_argument("--data-dir", type=Path, default=DATA_DIR)
    p.add_argument("--ckpt-dir", type=Path, default=CKPT_DIR)
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--tile-size", type=int, default=512,
                   help="Square crop size. 0 uses whole 650x650 tiles.")
    p.add_argument("--base-channels", type=int, default=64,
                   help="U-Net width. Halve this if you run out of VRAM.")
    p.add_argument("--num-workers", type=int, default=4)
    p.add_argument("--pos-weight", type=float, default=1.0,
                   help="Weight on the building class in BCE. >1 trades precision for recall.")
    p.add_argument("--no-amp", action="store_true", help="Disable mixed precision.")
    p.add_argument("--resume", action="store_true", help="Continue from last.pt.")
    p.add_argument("--limit", type=int, default=0,
                   help="Use only N tiles per split. For smoke tests.")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


class DiceLoss(nn.Module):
    """
    Soft Dice on the positive class. Paired with BCE because buildings cover a
    minority of pixels: BCE alone can score well by under-predicting them,
    while Dice responds directly to overlap.
    """

    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        probs = probs.reshape(probs.size(0), -1)
        targets = targets.reshape(targets.size(0), -1)

        intersection = (probs * targets).sum(dim=1)
        union = probs.sum(dim=1) + targets.sum(dim=1)
        dice = (2 * intersection + self.smooth) / (union + self.smooth)
        return 1 - dice.mean()


class ConfusionAccumulator:
    """
    Sums TP/FP/FN over the whole validation split before computing IoU and F1,
    rather than averaging per-image scores. Per-image averaging is skewed by
    near-empty tiles, where a handful of pixels swings the score.
    """

    def __init__(self):
        self.tp = self.fp = self.fn = 0

    def update(self, logits, targets, threshold=0.5):
        preds = (torch.sigmoid(logits) > threshold).float()
        self.tp += torch.sum(preds * targets).item()
        self.fp += torch.sum(preds * (1 - targets)).item()
        self.fn += torch.sum((1 - preds) * targets).item()

    @property
    def iou(self):
        denom = self.tp + self.fp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self):
        denom = 2 * self.tp + self.fp + self.fn
        return 2 * self.tp / denom if denom else 0.0

    @property
    def precision(self):
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self):
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0


def build_loader(args, split, augment):
    tile_size = args.tile_size if args.tile_size > 0 else None
    ds = SpaceNetDataset(
        image_dir=args.data_dir / split / "images",
        mask_dir=args.data_dir / split / "masks",
        tile_size=tile_size,
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


def run_epoch(model, loader, device, bce, dice, optimizer=None, scaler=None):
    """One pass over a loader. Training when optimizer is given, else evaluation."""
    training = optimizer is not None
    model.train() if training else model.eval()

    total_loss = 0.0
    metrics = ConfusionAccumulator()
    use_amp = scaler is not None and scaler.is_enabled()

    for images, masks in loader:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=use_amp):
                logits = model(images)
                loss = bce(logits, masks) + dice(logits, masks)

        if training:
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

        total_loss += loss.item() * images.size(0)
        # Metrics in fp32 -- thresholding fp16 probabilities near 0.5 is noisy.
        metrics.update(logits.detach().float(), masks)

    return total_loss / len(loader.dataset), metrics


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    args.ckpt_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}"
          + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))
    if device.type == "cpu":
        print("  No GPU visible -- expect this to be very slow at 512px.")

    train_loader = build_loader(args, "train", augment=True)
    val_loader = build_loader(args, "val", augment=False)
    print(f"Train tiles: {len(train_loader.dataset)} | Val tiles: {len(val_loader.dataset)}")

    model = UNet(base_channels=args.base_channels).to(device)
    bce = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([args.pos_weight], device=device)
        if args.pos_weight != 1.0 else None
    )
    dice = DiceLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", patience=5)
    scaler = torch.cuda.amp.GradScaler(enabled=not args.no_amp and device.type == "cuda")

    start_epoch, best_iou = 1, 0.0
    last_path, best_path = args.ckpt_dir / "last.pt", args.ckpt_dir / "best.pt"

    if args.resume and last_path.exists():
        ckpt = torch.load(last_path, map_location=device)
        model.load_state_dict(ckpt["model"])
        optimizer.load_state_dict(ckpt["optimizer"])
        scheduler.load_state_dict(ckpt["scheduler"])
        scaler.load_state_dict(ckpt["scaler"])
        start_epoch, best_iou = ckpt["epoch"] + 1, ckpt["best_iou"]
        print(f"Resumed from epoch {ckpt['epoch']} (best val IoU {best_iou:.4f})")

    for epoch in range(start_epoch, args.epochs + 1):
        t0 = time.time()
        train_loss, train_metrics = run_epoch(
            model, train_loader, device, bce, dice, optimizer, scaler
        )
        val_loss, val_metrics = run_epoch(model, val_loader, device, bce, dice)
        scheduler.step(val_metrics.iou)

        print(
            f"Epoch {epoch:3d}/{args.epochs} "
            f"| train loss {train_loss:.4f} IoU {train_metrics.iou:.4f} "
            f"| val loss {val_loss:.4f} IoU {val_metrics.iou:.4f} F1 {val_metrics.f1:.4f} "
            f"P {val_metrics.precision:.3f} R {val_metrics.recall:.3f} "
            f"| {time.time() - t0:.0f}s"
        )

        state = {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "scaler": scaler.state_dict(),
            "epoch": epoch,
            "best_iou": best_iou,
            "args": vars(args),
        }
        torch.save(state, last_path)

        if val_metrics.iou > best_iou:
            best_iou = val_metrics.iou
            state["best_iou"] = best_iou
            torch.save(state, best_path)
            print(f"  new best val IoU {best_iou:.4f} -> {best_path.name}")

    print(f"\nDone. Best val IoU: {best_iou:.4f}")
    print(f"Checkpoints in {args.ckpt_dir}")


if __name__ == "__main__":
    main()

