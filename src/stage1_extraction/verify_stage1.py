"""
Stage 1 reproducibility check — re-run inference on a few test tiles and confirm
the freshly produced probability maps match the ones already committed under
`data/processed/<split>/predictions/`.

This exists because `inference.py` writes PNGs straight into the predictions
directory, so re-running it to "just check" would silently overwrite the
artifacts Stage 2 was vectorized from. This script writes to a separate output
directory and compares, leaving the originals untouched.

bf16 autocast on CUDA is not bit-exact across runs, so the comparison is a
tolerance check rather than a hash equality: mean/median absolute difference in
0-255 PNG units, plus the thresholded-binary agreement that actually matters
downstream (vectorize.py thresholds at 0.5).

Usage:
    python src/stage1_extraction/verify_stage1.py
    python src/stage1_extraction/verify_stage1.py --tiles 5 --tolerance 4
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import NORM_MAX
from inference import load_model
from train import ConfusionAccumulator

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
DEFAULT_CKPT = Path("E:/digital-twin-fyp/models/unet_resnet34_best.pth")
DEFAULT_OUT_DIR = Path("E:/digital-twin-fyp/results/verify_stage1")


def parse_args():
    p = argparse.ArgumentParser(description="Verify Stage-1 inference reproduces existing predictions")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--ckpt", type=Path, default=DEFAULT_CKPT)
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--tiles", type=int, default=3, help="How many test tiles to re-run.")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                   help="Where to write the fresh PNGs. Never the predictions dir.")
    p.add_argument("--threshold", type=float, default=0.5)
    # bf16 + CUDA reduction order gives small run-to-run jitter; 4/255 is well
    # below anything that would move a thresholded polygon boundary meaningfully.
    p.add_argument("--tolerance", type=float, default=4.0,
                   help="Max mean abs PNG difference (0-255 units) that still counts as a match.")
    return p.parse_args()


def load_tile(img_path):
    """Same load/normalize path as SpaceNetDataset, for a single tile."""
    import rasterio

    with rasterio.open(img_path) as src:
        image = src.read([1, 2, 3]).astype(np.float32)
    image = np.clip(image, 0, NORM_MAX) / NORM_MAX
    return torch.from_numpy(image).unsqueeze(0)


def main():
    args = parse_args()

    pred_dir = args.data_dir / args.split / "predictions"
    img_dir = args.data_dir / args.split / "images"
    mask_dir = args.data_dir / args.split / "masks"

    if not pred_dir.exists():
        raise SystemExit(f"No existing predictions at {pred_dir}. Run inference.py --split {args.split} first.")

    # Guard: refuse to write anywhere that could clobber the originals.
    if args.out_dir.resolve() == pred_dir.resolve():
        raise SystemExit("--out-dir must not be the predictions directory.")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

    model, meta = load_model(args.ckpt, device)
    print(f"Checkpoint: {args.ckpt}")
    print(f"  epoch {meta['epoch']} | val IoU {meta['val_iou']:.4f} | val F1 {meta['val_f1']:.4f}")

    existing = sorted(pred_dir.glob("mask_*.png"))
    selected = existing[: args.tiles]
    if not selected:
        raise SystemExit(f"No mask_*.png in {pred_dir}.")

    print(f"\nVerifying {len(selected)} tiles: " + ", ".join(p.stem for p in selected))

    results = []
    all_match = True

    for ref_path in tqdm(selected, desc="verify"):
        tile = ref_path.stem.replace("mask_", "")
        img_path = img_dir / f"RGB-PanSharpen_{tile}.tif"
        mask_path = mask_dir / f"mask_{tile}.png"
        if not img_path.exists():
            raise SystemExit(f"Missing image for {tile}: {img_path}")

        ref = np.array(Image.open(ref_path), dtype=np.float32)
        if ref.ndim == 3:
            ref = ref[..., 0]

        x = load_tile(img_path).to(device)
        with torch.no_grad():
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16,
                                enabled=device.type == "cuda"):
                logits = model(x)
            probs = torch.sigmoid(logits).float()[0, 0].cpu().numpy()

        fresh = (probs * 255.0).clip(0, 255).astype(np.uint8)
        Image.fromarray(fresh).save(args.out_dir / ref_path.name)

        fresh_f = fresh.astype(np.float32)
        mean_abs = float(np.abs(fresh_f - ref).mean())
        max_abs = float(np.abs(fresh_f - ref).max())

        # What actually matters downstream: does thresholding agree?
        ref_bin = ref >= args.threshold * 255.0
        fresh_bin = fresh_f >= args.threshold * 255.0
        agree = float((ref_bin == fresh_bin).mean())

        # And vs ground truth, for a sanity read on this tile.
        tile_iou = None
        if mask_path.exists():
            gt = np.array(Image.open(mask_path), dtype=np.float32)
            if gt.ndim == 3:
                gt = gt[..., 0]
            gt_bin = gt > 0
            inter = float((fresh_bin & gt_bin).sum())
            union = float((fresh_bin | gt_bin).sum())
            tile_iou = inter / union if union > 0 else None

        match = mean_abs <= args.tolerance
        all_match &= match

        results.append({
            "tile": tile,
            "shape": list(ref.shape),
            "mean_abs_diff": round(mean_abs, 4),
            "max_abs_diff": round(max_abs, 1),
            "binary_agreement": round(agree, 6),
            "tile_iou_vs_gt": round(tile_iou, 4) if tile_iou is not None else None,
            "match": match,
        })
        print(f"  {tile}: mean|Δ|={mean_abs:.3f} max|Δ|={max_abs:.0f} "
              f"binary_agree={agree:.5f}" + (f" IoU={tile_iou:.4f}" if tile_iou is not None else "")
              + f"  -> {'MATCH' if match else 'MISMATCH'}")

    # Split-wide metrics on just these tiles, as a cross-check that the fresh
    # predictions score the same as the committed ones.
    acc_fresh = ConfusionAccumulator()
    acc_ref = ConfusionAccumulator()
    for ref_path, r in zip(selected, results):
        mask_path = mask_dir / f"mask_{r['tile']}.png"
        if not mask_path.exists():
            continue
        gt = np.array(Image.open(mask_path), dtype=np.float32)
        if gt.ndim == 3:
            gt = gt[..., 0]
        gt_t = torch.from_numpy((gt > 0).astype(np.float32)).unsqueeze(0).unsqueeze(0)
        ref_t = torch.from_numpy(np.array(Image.open(ref_path), dtype=np.float32)).unsqueeze(0).unsqueeze(0)
        fresh_t = torch.from_numpy(
            np.array(Image.open(args.out_dir / ref_path.name), dtype=np.float32)
        ).unsqueeze(0).unsqueeze(0)
        acc_ref.update(ref_t >= args.threshold * 255.0, gt_t)
        acc_fresh.update(fresh_t >= args.threshold * 255.0, gt_t)

    summary = {
        "split": args.split,
        "tiles_verified": len(results),
        "checkpoint": str(args.ckpt),
        "checkpoint_epoch": meta["epoch"],
        "tolerance_mean_abs": args.tolerance,
        "threshold": args.threshold,
        "norm_max": NORM_MAX,
        "device": str(device),
        "all_match": bool(all_match),
        "iou_existing": round(acc_ref.iou, 6),
        "iou_fresh": round(acc_fresh.iou, 6),
        "f1_existing": round(acc_ref.f1, 6),
        "f1_fresh": round(acc_fresh.f1, 6),
        "per_tile": results,
    }
    out_json = args.out_dir / "verification.json"
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nExisting-prediction IoU {summary['iou_existing']:.4f} | fresh IoU {summary['iou_fresh']:.4f}")
    print(f"VERDICT: {'PASS — Stage 1 verified' if all_match else 'FAIL — predictions do not reproduce'}")
    print(f"Wrote {out_json}")
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
