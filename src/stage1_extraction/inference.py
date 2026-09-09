"""
Stage 1 inference — run the trained U-Net over a split and write prediction
masks + split-wide metrics.

Two outputs, because Stage 2 and the FYP report need different things:
  1. `<split>/predictions/mask_*.png` — 0-255 probability maps at full 650x650
     tile size. vectorize.py thresholds these into polygons.
  2. `<split>/predictions/metrics.json` — split-wide IoU/F1/P/R from the same
     ConfusionAccumulator used during training, so the reported number is
     computed identically to the val curve.

Whole-tile inference at 650x650 is deliberate: the model trained on 512 crops,
but padding to 768 and cropping back costs accuracy at tile edges and buys
nothing on a 6 GB GPU. 650 is not divisible by 32, and smp's ResNet34 encoder
handles that by padding internally.

Usage:
    python src/stage1_extraction/inference.py --split test
    python src/stage1_extraction/inference.py --split val --ckpt models/unet_resnet34_best.pth
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import segmentation_models_pytorch as smp
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import SpaceNetDataset, NORM_MAX
from train import ConfusionAccumulator

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
DEFAULT_CKPT = Path("E:/digital-twin-fyp/models/unet_resnet34_best.pth")


def parse_args():
    p = argparse.ArgumentParser(description="Run the trained U-Net over a split")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--ckpt", type=Path, default=DEFAULT_CKPT,
                   help="Checkpoint to load. Must contain model_state_dict.")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--batch-size", type=int, default=4,
                   help="Whole 650x650 tiles need more VRAM than 512 crops.")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--save-png", action="store_true", default=True,
                   help="Write prediction PNGs (on by default).")
    p.add_argument("--no-save-png", dest="save_png", action="store_false",
                   help="Metrics only, skip writing PNGs.")
    return p.parse_args()


def load_model(ckpt_path, device):
    if not ckpt_path.exists():
        raise SystemExit(f"Checkpoint not found: {ckpt_path}\nTrain first: train_unet.py --epochs 15")

    # weights_only=False: checkpoints written before this session embedded
    # argparse Path objects. New ones store plain primitives and would load
    # under the safer default, but this keeps one code path.
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = smp.Unet(encoder_name="resnet34", encoder_weights=None, in_channels=3, classes=1)
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()

    meta = {
        "epoch": ckpt.get("epoch"),
        "val_iou": ckpt.get("val_iou"),
        "val_f1": ckpt.get("val_f1"),
    }
    return model, meta


def infer_split(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

    model, meta = load_model(args.ckpt, device)
    print(f"Checkpoint: {args.ckpt}")
    print(f"  trained epoch {meta['epoch']} | val IoU {meta['val_iou']:.4f} | val F1 {meta['val_f1']:.4f}")

    split_dir = args.data_dir / args.split
    out_dir = split_dir / "predictions"
    if args.save_png:
        out_dir.mkdir(parents=True, exist_ok=True)

    # Whole tiles: tile_size=None. augment=False so masks align with images.
    ds = SpaceNetDataset(
        image_dir=split_dir / "images",
        mask_dir=split_dir / "masks",
        tile_size=None,
        augment=False,
    )
    if not len(ds):
        raise SystemExit(f"No masks under {split_dir / 'masks'}. Run build_masks.py first.")
    if args.limit:
        from torch.utils.data import Subset
        ds = Subset(ds, range(min(args.limit, len(ds))))

    loader = torch.utils.data.DataLoader(
        ds, batch_size=args.batch_size, shuffle=False, num_workers=0
    )
    print(f"Inferring {len(ds)} tiles at whole-tile size (batch {args.batch_size})")

    metrics = ConfusionAccumulator()
    mask_names = sorted((split_dir / "masks").glob("*.png"))
    if args.limit:
        mask_names = mask_names[: args.limit]
    name_iter = iter(mask_names)

    with torch.no_grad():
        for images, masks in tqdm(loader, desc=f"[{args.split}]"):
            images = images.to(device, non_blocking=True)
            masks = masks.to(device, non_blocking=True)

            # bf16 autocast matches training; fp16 NaNs this model (see
            # train_unet.py resolve_amp).
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16,
                                enabled=device.type == "cuda"):
                logits = model(images)

            probs = torch.sigmoid(logits).float()
            metrics.update(probs > args.threshold, masks)

            if args.save_png:
                prob_np = (probs.cpu().numpy() * 255.0).clip(0, 255).astype(np.uint8)
                for i in range(prob_np.shape[0]):
                    name = next(name_iter, None)
                    if name is None:
                        break
                    Image.fromarray(prob_np[i, 0]).save(out_dir / name.name)

    result = {
        "split": args.split,
        "tiles": len(ds),
        "checkpoint": str(args.ckpt),
        "checkpoint_epoch": meta["epoch"],
        "checkpoint_val_iou": meta["val_iou"],
        "threshold": args.threshold,
        "norm_max": NORM_MAX,
        "tile_size": "whole (650x650)",
        "iou": round(metrics.iou, 6),
        "f1": round(metrics.f1, 6),
        "precision": round(metrics.precision, 6),
        "recall": round(metrics.recall, 6),
    }

    print(
        f"\n{args.split.upper()} | IoU {result['iou']:.4f} | F1 {result['f1']:.4f} | "
        f"P {result['precision']:.3f} | R {result['recall']:.3f} | {result['tiles']} tiles"
    )

    if args.save_png:
        metrics_path = out_dir / "metrics.json"
        metrics_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {len(mask_names)} prediction PNGs + {metrics_path}")
    else:
        print("(--no-save-png: metrics only)")

    return result


if __name__ == "__main__":
    infer_split(parse_args())
