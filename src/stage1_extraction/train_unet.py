"""
Train the building-footprint U-Net (segmentation_models_pytorch, ResNet34
backbone) on the prepared SpaceNet splits.

Primary training script for TerraTwin. Fallback: `train.py` + `model.py`
(custom from-scratch UNet with AMP/resume/scheduler). This script is chosen
as primary because the ImageNet-pretrained encoder learns building footprints
faster on the small (673-tile) training set.

Metrics helpers (`ConfusionAccumulator`, `DiceLoss`) are imported from
`train.py` rather than re-implemented here, so the primary and fallback
trainers can never drift apart on how IoU/F1 are computed.

Runs unchanged with the local E:/digital-twin-fyp/... defaults. Pass
--data-dir / --ckpt-dir to point at a different layout (e.g. the AMD cloud
fallback, or after moving data) without editing the file.

Local smoke test (GTX 1660 Super, ~minutes):
    python src/stage1_extraction/train_unet.py --epochs 1 --limit 4

Full run (~1-1.5h on 1660 Super at batch 8):
    python src/stage1_extraction/train_unet.py --epochs 15

Resume after a dropped session (cloud GPU):
    python src/stage1_extraction/train_unet.py --epochs 15 --resume

Mixed precision defaults to bf16. fp16 is available but broken on this model:
the fp16 forward pass returns NaN logits (verified on the GTX 1660 Super), so
`--amp fp16` will train on nothing. An existing best checkpoint is archived to
models/archive/ rather than overwritten in place.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
import segmentation_models_pytorch as smp
from tqdm import tqdm

# Importable regardless of the caller's CWD. `from dataset import ...` only
# resolves when the script's own directory is on sys.path, which is true for
# `python src/stage1_extraction/train_unet.py` but not for `-m` or an external
# importer -- make it unconditional instead of depending on how it was launched.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataset import SpaceNetDataset
from train import ConfusionAccumulator, DiceLoss

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
DEFAULT_CKPT_DIR = Path("E:/digital-twin-fyp/models")
BEST_CKPT_NAME = "unet_resnet34_best.pth"
LAST_CKPT_NAME = "last.pt"
HISTORY_NAME = "unet_resnet34_history.json"


# ------------------------------------------------------------------
# 1. CLI arguments (defaults keep the original local behaviour)
# ------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Train U-Net (smp ResNet34) on SpaceNet masks")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                   help="Root holding {train,val}/{images,masks}.")
    p.add_argument("--ckpt-dir", type=Path, default=DEFAULT_CKPT_DIR,
                   help="Where checkpoints are written.")
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--batch-size", type=int, default=8,
                   help="8 fits in 6 GB VRAM (GTX 1660 Super). Drop to 4 on OOM.")
    p.add_argument("--tile-size", type=int, default=512,
                   help="Square crop size. 0 uses whole 650x650 tiles.")
    p.add_argument("--num-workers", type=int, default=2,
                   help="Raise on Linux/cloud.")
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--pos-weight", type=float, default=1.0,
                   help="Weight on the building class in BCE. >1 trades precision for recall.")
    p.add_argument("--patience", type=int, default=5,
                   help="Epochs of no val-IoU improvement before the LR is halved.")
    p.add_argument("--amp", choices=("off", "bf16", "fp16"), default="bf16",
                   help="Mixed precision. bf16 keeps fp32 range; fp16 NaNs the logits "
                        "on this repo's smp ResNet34 (BatchNorm in half precision).")
    p.add_argument("--no-amp", action="store_true",
                   help="Deprecated alias for --amp off.")
    p.add_argument("--resume", action="store_true",
                   help="Continue from last.pt in --ckpt-dir.")
    p.add_argument("--limit", type=int, default=0,
                   help="Use only N tiles per split. For smoke tests.")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


# ------------------------------------------------------------------
# 2. Device + reproducibility
# ------------------------------------------------------------------
# PyTorch ROCm (AMD MI300X) and CUDA (GTX 1660 Super) both surface as
# torch.cuda, so this single branch covers both -- nothing here is CUDA-only.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def resolve_amp(args):
    """Returns (autocast_dtype, grad_scaler_enabled).

    The two are decided together because they are not the same switch: bf16
    wants autocast ON but loss scaling OFF (its exponent range matches fp32,
    so gradients cannot underflow -- the thing GradScaler exists to prevent).
    fp16 needs the scaler, and empirically NaNs this model's forward pass,
    which is why it is not the default.

    On CPU autocast is dropped entirely rather than emulated.
    """
    mode = "off" if args.no_amp else args.amp
    if mode == "off" or DEVICE.type != "cuda":
        return None, False
    if mode == "bf16":
        return torch.bfloat16, False
    return torch.float16, True


def seed_everything(seed):
    """Seed every RNG the training path touches.

    numpy is seeded because SpaceNetDataset draws its augment/crop randomness
    through torch, but numpy still backs the rasterio -> tensor conversion
    path; leaving it unseeded makes `--seed` only half-reproducible.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ------------------------------------------------------------------
# 3. Compound loss (BCE + soft Dice)
# ------------------------------------------------------------------
def build_criterion(args):
    """BCEWithLogits + Dice, the two terms summed per batch.

    BCE alone can score well by under-predicting buildings, since they cover a
    minority of pixels; Dice responds directly to overlap and cancels that
    failure mode. Both run on logits -- BCEWithLogitsLoss is numerically safer
    than sigmoid + BCE.
    """
    bce = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([args.pos_weight], device=DEVICE)
        if args.pos_weight != 1.0
        else None
    )
    return bce, DiceLoss()


# ------------------------------------------------------------------
# 4. Dataloaders
# ------------------------------------------------------------------
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

    # drop_last only on the train split, and only when a full batch exists to
    # drop -- otherwise `--limit 4 --batch-size 8` would silently train on
    # nothing at all.
    drop_last = bool(augment and len(ds) > args.batch_size)

    # A seeded generator keeps the shuffle order reproducible under --seed.
    generator = torch.Generator().manual_seed(args.seed) if augment else None

    return DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=augment,
        num_workers=args.num_workers,
        pin_memory=DEVICE.type == "cuda",
        drop_last=drop_last,
        generator=generator,
        persistent_workers=args.num_workers > 0,
    )


# ------------------------------------------------------------------
# 5. One pass over a loader
# ------------------------------------------------------------------
def run_epoch(model, loader, device, bce, dice, autocast_dtype, optimizer=None, scaler=None):
    """Training pass when an optimizer is given, otherwise evaluation.

    autocast_dtype picks the dtype the forward pass runs in. When None,
    autocast is off entirely -- forward + backward both in fp32. When set, the
    scaler is still needed under fp16 (to keep small gradients from underflow)
    but not under bf16. The two are decided by resolve_amp, not by probing the
    scaler after construction, since bf16 needs the former True and the latter
    False at the same time.

    Loss is weighted by batch size before averaging so a ragged final batch
    does not skew the reported number. Metrics accumulate TP/FP/FN over the
    whole split -- per-batch IoU averaging is dominated by near-empty tiles,
    where a handful of pixels swings the score.
    """
    training = optimizer is not None
    model.train() if training else model.eval()

    total_loss = 0.0
    metrics = ConfusionAccumulator()
    autocast_enabled = autocast_dtype is not None
    use_scaler = training and scaler is not None and scaler.is_enabled()

    bar = tqdm(loader, desc="[Train]" if training else "[Val]", leave=False)
    for images, masks in bar:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, dtype=autocast_dtype, enabled=autocast_enabled):
                logits = model(images)
                loss = bce(logits, masks) + dice(logits, masks)

        if training:
            optimizer.zero_grad(set_to_none=True)
            if use_scaler:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
            bar.set_postfix(loss=f"{loss.item():.4f}")

        total_loss += loss.item() * images.size(0)
        # Metrics in fp32 -- thresholding fp16 probabilities near 0.5 is noisy.
        metrics.update(logits.detach().float(), masks)

    return total_loss / len(loader.dataset), metrics


# ------------------------------------------------------------------
# 6. Checkpointing
# ------------------------------------------------------------------
def serializable_args(args):
    """vars(args) with Paths stringified.

    Keeping the checkpoint to plain primitives means it loads under torch's
    default weights_only=True, and stays readable if the data directory moves
    between machines (local E:/ vs. the AMD cloud bundle).
    """
    return {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}


def save_checkpoint(path, model, optimizer, scheduler, scaler, epoch, val_metrics, best_iou, args):
    """Key names match the pre-existing checkpoint so old .pth files still load."""
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "scaler_state_dict": scaler.state_dict(),
            "val_iou": val_metrics.iou,
            "val_f1": val_metrics.f1,
            "best_val_iou": best_iou,
            "args": serializable_args(args),
        },
        path,
    )


def archive_existing_best(best_path):
    """Move a pre-existing best checkpoint into <ckpt-dir>/archive/ instead of
    letting the new run overwrite it.

    A fresh run starts at best_val_iou=0.0, so its first epoch always "beats"
    the old best and writes straight over it. models/ is gitignored -- an
    overwritten checkpoint is gone, not recoverable. Timestamped archives keep
    every completed run.
    """
    if not best_path.exists():
        return None
    archive_dir = best_path.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = archive_dir / f"{best_path.stem}_{stamp}{best_path.suffix}"
    best_path.replace(dest)
    return dest


def load_checkpoint(path, model, optimizer, scheduler, scaler, device):
    """Returns (next_epoch, best_iou_so_far).

    weights_only=False because checkpoints written before this revision
    embedded argparse Path objects. The scheduler/scaler states are optional
    so an older checkpoint still resumes instead of raising.
    """
    ckpt = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    optimizer.load_state_dict(ckpt["optimizer_state_dict"])
    if scheduler is not None and "scheduler_state_dict" in ckpt:
        scheduler.load_state_dict(ckpt["scheduler_state_dict"])
    if scaler is not None and "scaler_state_dict" in ckpt:
        scaler.load_state_dict(ckpt["scaler_state_dict"])

    # Fall back through older key spellings for checkpoints from earlier runs.
    best_iou = ckpt.get("best_val_iou", ckpt.get("val_iou", 0.0))
    return ckpt["epoch"] + 1, best_iou


# ------------------------------------------------------------------
# 7. Training loop
# ------------------------------------------------------------------
def run_training(args):
    # Normalize the deprecated alias before anything reads AMP settings.
    if args.no_amp:
        args.amp = "off"
    autocast_dtype, use_scaler = resolve_amp(args)

    seed_everything(args.seed)
    args.ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_path = args.ckpt_dir / BEST_CKPT_NAME
    last_path = args.ckpt_dir / LAST_CKPT_NAME
    history_path = args.ckpt_dir / HISTORY_NAME

    # Fresh runs archive the previous best checkpoint instead of clobbering it.
    # Resumed runs keep the same lineage, so the check does not apply to them.
    archived = None
    if not args.resume and best_path.exists():
        archived = archive_existing_best(best_path)

    print(f"--> Initializing training pipeline on device: {DEVICE}")
    if DEVICE.type == "cuda":
        print(f"    GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("    WARNING: no GPU visible -- expect this to be very slow at 512px.")
    print(f"    data-dir: {args.data_dir} | ckpt-dir: {args.ckpt_dir}")
    amp_label = "off" if autocast_dtype is None else ("bf16" if autocast_dtype == torch.bfloat16 else "fp16")
    print(f"    torch {torch.__version__} | smp {smp.__version__} | autocast {amp_label} | scaler {'on' if use_scaler else 'off'} | seed {args.seed}")
    if archived is not None:
        print(f"    Archived previous best: {archived}")

    train_loader = build_loader(args, "train", augment=True)
    val_loader = build_loader(args, "val", augment=False)
    print(
        f"Loaded {len(train_loader.dataset)} train tiles | "
        f"{len(val_loader.dataset)} validation tiles "
        f"(tile_size={args.tile_size or 'whole'}, batch={args.batch_size})."
    )

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=1,
    ).to(DEVICE)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"    Trainable parameters: {n_params:,}")

    bce, dice = build_criterion(args)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=args.patience
    )
    # torch.amp.GradScaler (not the deprecated torch.cuda.amp one) -- device_type
    # is what makes this work identically on ROCm and CUDA. Loss scaling only
    # matters for fp16, where tiny gradients would underflow in the 5-bit
    # exponent; bf16 keeps fp32's 8-bit exponent and runs without a scaler.
    scaler = torch.amp.GradScaler(device=DEVICE.type, enabled=use_scaler)

    start_epoch, best_val_iou = 1, 0.0
    if args.resume:
        if not last_path.exists():
            raise SystemExit(f"--resume given but {last_path} does not exist. Train from scratch instead.")
        start_epoch, best_val_iou = load_checkpoint(
            last_path, model, optimizer, scheduler, scaler, DEVICE
        )
        print(f"    Resumed from epoch {start_epoch - 1} (best val IoU {best_val_iou:.4f})")

    history = []
    for epoch in range(start_epoch, args.epochs + 1):
        t0 = time.time()

        train_loss, train_metrics = run_epoch(
            model, train_loader, DEVICE, bce, dice, autocast_dtype, optimizer, scaler
        )
        val_loss, val_metrics = run_epoch(
            model, val_loader, DEVICE, bce, dice, autocast_dtype
        )
        scheduler.step(val_metrics.iou)

        elapsed = time.time() - t0
        current_lr = optimizer.param_groups[0]["lr"]
        print(
            f"Epoch {epoch:02d}/{args.epochs:02d} | "
            f"Train Loss: {train_loss:.4f} IoU {train_metrics.iou:.4f} | "
            f"Val Loss: {val_loss:.4f} IoU {val_metrics.iou:.4f} F1 {val_metrics.f1:.4f} "
            f"P {val_metrics.precision:.3f} R {val_metrics.recall:.3f} | "
            f"lr {current_lr:.2e} | {elapsed:.0f}s"
        )

        record = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "train_iou": round(train_metrics.iou, 6),
            "val_loss": round(val_loss, 6),
            "val_iou": round(val_metrics.iou, 6),
            "val_f1": round(val_metrics.f1, 6),
            "val_precision": round(val_metrics.precision, 6),
            "val_recall": round(val_metrics.recall, 6),
            "lr": current_lr,
            "seconds": round(elapsed, 1),
        }
        history.append(record)

        # last.pt every epoch so a dropped cloud session costs one epoch, not
        # the whole run; best.pth only on improvement.
        save_checkpoint(last_path, model, optimizer, scheduler, scaler,
                        epoch, val_metrics, best_val_iou, args)
        if val_metrics.iou > best_val_iou:
            best_val_iou = val_metrics.iou
            save_checkpoint(best_path, model, optimizer, scheduler, scaler,
                            epoch, val_metrics, best_val_iou, args)
            print(f"  --> [Saved Checkpoint] New best Val IoU: {best_val_iou:.4f} to {best_path}")

        # Write the history incrementally too -- if the run dies mid-way, the
        # epochs that did complete are still on disk for the writeup.
        history_path.write_text(json.dumps(
            {"args": serializable_args(args),
             "torch": torch.__version__,
             "device": str(DEVICE),
             "gpu": torch.cuda.get_device_name(0) if DEVICE.type == "cuda" else None,
             "best_val_iou": best_val_iou,
             "history": history},
            indent=2,
        ), encoding="utf-8")

    best = max(history, key=lambda r: r["val_iou"]) if history else None
    print("\n--> Training complete.")
    if best:
        print(
            f"    Best epoch {best['epoch']}: val IoU {best['val_iou']:.4f} | "
            f"F1 {best['val_f1']:.4f} | P {best['val_precision']:.3f} | R {best['val_recall']:.3f}"
        )
    print(f"    Checkpoints: {best_path}")
    print(f"                 {last_path}")
    print(f"    History:     {history_path}")


if __name__ == "__main__":
    run_training(parse_args())
