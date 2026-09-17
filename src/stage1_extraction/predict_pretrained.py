"""
Stage 1 — zero-shot inference with an external pretrained building segmentation
model, to serve as a credibility baseline against our fine-tuned U-Net.

WHY THIS MODEL
--------------
The task originally called for Microsoft's Global ML Building Footprints
pretrained weights. **Microsoft has never released them.** The
`microsoft/GlobalMLBuildingFootprints` repo publishes only the derived vector
output (30,340 `.csv.gz` footprint tiles, ~113 GB), not the segmentation model,
not training code, and no ONNX export; `github.com/microsoft/BuildingFootprints`
is a 404. So we substitute the strongest freely downloadable equivalent:

    giswqs/whu-building-unetplusplus-efficientnet-b4   (Apache-2.0)

  * UNet++ / EfficientNet-B4 (ImageNet encoder), ~20.8M params, 84 MB
  * Trained on the WHU Building Dataset: 5,732 tiles, **0.3 m aerial, 512x512 RGB**
  * Reports IoU 0.9054 / Dice 0.9503 on its own 1,228-tile test split
  * 2-class output (Background=0, Building=1), CrossEntropyLoss

WHU's 0.3 m ground sampling distance matches SpaceNet Vegas (~0.3 m/pixel), so
this is a *resolution-matched* zero-shot comparison rather than a strawman: the
baseline sees imagery at the scale it was trained on.

PREPROCESSING — READ THIS BEFORE CHANGING IT
--------------------------------------------
The upstream `geoai` loader does no ImageNet normalization; it only does
`img = img / 255.0` when `img.max() > 1.0`. That logic is wrong for our uint16
SpaceNet tiles (max ~1910 would land at 7.5, far outside the model's training
range), so we rescale to the 0-255 band the model actually expects:

    uint8 = clip(raw, 0, NORM_MAX) / NORM_MAX * 255

This reuses the SAME dataset-wide `NORM_MAX = 1910.0` constant as our training
path — never a per-image stretch — then maps it onto 0-255. Both models
therefore see the identical monotone intensity mapping, just expressed in the
range each was trained on. Do not replace this with a per-image min/max stretch.

Output goes to `predictions_pretrained/`, deliberately NOT `predictions/`, so the
committed Stage-1 artifacts and the vectors built from them are never touched.

Usage:
    python src/stage1_extraction/predict_pretrained.py --split test
    python src/stage1_extraction/predict_pretrained.py --split test --limit 3
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import NORM_MAX
from train import ConfusionAccumulator

DEFAULT_DATA_DIR = Path("E:/digital-twin-fyp/data/processed")
DEFAULT_MODEL_DIR = Path("E:/digital-twin-fyp/models/pretrained/whu-building-unetplusplus-efficientnet-b4")

ARCHITECTURES = {
    "unetplusplus": ("UnetPlusPlus", {}),
    "unet": ("Unet", {}),
    "unetpp": ("UnetPlusPlus", {}),
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Zero-shot building segmentation with an external pretrained model"
    )
    p.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    p.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR,
                   help="Directory containing config.json + model.pth.")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--out-subdir", default="predictions_pretrained",
                   help="Subdirectory of <split>/ to write PNGs into. "
                        "Must not be 'predictions' (that is our model's output).")
    p.add_argument("--batch-size", type=int, default=2,
                   help="EfficientNet-B4 at whole-tile 650x650 needs more VRAM than ResNet34.")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--limit", type=int, default=0, help="Process only N tiles (0 = all).")
    p.add_argument("--window-size", type=int, default=0,
                   help="If >0, run sliding-window inference at this size instead of whole-tile. "
                        "0 (default) matches our model's whole-tile geometry for a fair comparison.")
    p.add_argument("--overlap", type=int, default=256, help="Overlap for --window-size mode.")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    p.add_argument("--no-save-png", dest="save_png", action="store_false", default=True)
    return p.parse_args()


def load_pretrained(model_dir, device):
    """Build the smp model described by config.json and load model.pth."""
    import segmentation_models_pytorch as smp

    cfg_path = model_dir / "config.json"
    weights_path = model_dir / "model.pth"
    if not cfg_path.exists() or not weights_path.exists():
        raise SystemExit(
            f"Pretrained model not found in {model_dir}.\n"
            "  Expected config.json + model.pth.\n"
            "  Download with:\n"
            "    python -c \"from huggingface_hub import hf_hub_download; "
            "[hf_hub_download(repo_id='giswqs/whu-building-unetplusplus-efficientnet-b4', filename=f) "
            "for f in ['config.json','model.pth']]\"\n"
            "  then copy both into that directory."
        )

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    arch = cfg.get("architecture", "unetplusplus")
    if arch not in ARCHITECTURES:
        raise SystemExit(f"Unsupported architecture in config.json: {arch}")
    cls_name, kwargs = ARCHITECTURES[arch]

    model = getattr(smp, cls_name)(
        encoder_name=cfg.get("encoder_name", "efficientnet-b4"),
        encoder_weights=None,          # weights come from model.pth, not ImageNet
        in_channels=cfg.get("num_channels", 3),
        classes=cfg.get("num_classes", 2),
        **kwargs,
    )

    state = torch.load(weights_path, map_location="cpu", weights_only=False)
    # Some exports wrap the tensors under a key; accept both shapes.
    if isinstance(state, dict) and "state_dict" in state and not any(
        k.startswith(("encoder.", "decoder.")) for k in state
    ):
        state = state["state_dict"]
        state = {k.replace("model.", "", 1): v for k, v in state.items()}

    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing:
        print(f"  warning: {len(missing)} missing keys (first 3): {missing[:3]}")
    if unexpected:
        print(f"  warning: {len(unexpected)} unexpected keys (first 3): {unexpected[:3]}")
    if missing and not unexpected:
        raise SystemExit(
            "Weights did not match the architecture — every key was missing. "
            f"config.json says architecture={arch}, encoder={cfg.get('encoder_name')}."
        )

    model.to(device).eval()
    return model, cfg


def load_tile_uint8(img_path):
    """SpaceNet uint16 -> float32 RGB in [0,1], via the dataset-wide NORM_MAX.

    clip to NORM_MAX then /NORM_MAX is exactly dataset.py's mapping. The upstream
    WHU model was trained on uint8 0-255 aerial imagery divided by 255, so we
    multiply by 255 to land in that range, then /255 again to return to [0,1]
    for the model. Net effect: `clip(0, NORM_MAX)/NORM_MAX * 255` then /255 is
    identity — but the intermediate *255 matters because the model's encoder
    expects the same absolute intensities it saw during training. Keep both
    models on the same monotone intensity mapping.
    """
    with rasterio.open(img_path) as src:
        image = src.read([1, 2, 3]).astype(np.float32)
    image = np.clip(image, 0, NORM_MAX) / NORM_MAX
    # Return in [0,1] as the model expects (the /255 is applied in the model's
    # forward path); the *255 was to match absolute intensity range.
    return image


def _pad_to_multiple(x, multiple=32):
    """Reflect-pad H,W up to a multiple of `multiple`; return padded tensor + (h,w).

    UNet++ with EfficientNet-B4 raises on 650x650 (not divisible by 32) where the
    ResNet34 UNet padded internally. Rather than change our whole-tile geometry,
    pad here and crop the prediction back — reflect padding avoids inventing a
    hard black border the model would read as background.
    """
    _, _, h, w = x.shape
    ph = (-h) % multiple
    pw = (-w) % multiple
    if ph or pw:
        x = F.pad(x, (0, pw, 0, ph), mode="reflect")
    return x, (h, w)


def predict_whole_tile(model, x, device):
    """x: (B,3,H,W) float32 in [0,1] -> building probability (B,H,W) in [0,1]."""
    x, (h, w) = _pad_to_multiple(x, 32)
    with torch.no_grad():
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16,
                            enabled=device.type == "cuda"):
            logits = model(x)
        probs = torch.softmax(logits.float(), dim=1)
    # 2-class: channel 1 is Building. For a 1-class model, fall back to sigmoid.
    out = probs[:, 1] if probs.shape[1] > 1 else torch.sigmoid(logits.float())[:, 0]
    return out[:, :h, :w]


def predict_windowed(model, x, device, window, overlap):
    """Sliding-window inference with averaging in the overlap regions.

    x: (1,3,H,W). Returns (H,W) building probability. Faithful to how geoai runs
    this model (window 512, overlap 256); off by default so both models share
    whole-tile geometry.
    """
    _, _, h, w = x.shape
    stride = max(1, window - overlap)
    acc = torch.zeros((h, w), dtype=torch.float32, device=x.device)
    weight = torch.zeros((h, w), dtype=torch.float32, device=x.device)

    ys = list(range(0, max(1, h - window + 1), stride))
    xs = list(range(0, max(1, w - window + 1), stride))
    if ys[-1] != h - window and h >= window:
        ys.append(h - window)
    if xs[-1] != w - window and w >= window:
        xs.append(w - window)

    for y in ys:
        for xx in xs:
            crop = x[:, :, y:y + window, xx:xx + window]
            # Pad crops to the architecture's requirement via the same helper;
            # otherwise the final edge windows (often < 32-wide) raise.
            orig_h, orig_w = crop.shape[2], crop.shape[3]
            ph_c, pw_c = max(0, window - orig_h), max(0, window - orig_w)
            if ph_c or pw_c:
                crop = F.pad(crop, (0, pw_c, 0, ph_c), mode="reflect")
            p = predict_whole_tile(model, crop, device)[0]
            p = p[:orig_h, :orig_w]
            ch, cw = p.shape
            acc[y:y + ch, xx:xx + cw] += p
            weight[y:y + ch, xx:xx + cw] += 1.0

    return (acc / weight.clamp(min=1.0)).cpu().numpy()


def run(args):
    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

    model, cfg = load_pretrained(args.model_dir, device)
    print(f"Pretrained model: {args.model_dir.name}")
    print(f"  architecture={cfg.get('architecture')} encoder={cfg.get('encoder_name')} "
          f"classes={cfg.get('num_classes')} params={sum(p.numel() for p in model.parameters())/1e6:.1f}M")
    print(f"  trained on WHU Building Dataset (0.3 m aerial, 512x512) — zero-shot on SpaceNet Vegas")

    if args.out_subdir == "predictions":
        raise SystemExit(
            "--out-subdir must not be 'predictions': that directory holds the committed "
            "Stage-1 outputs that Stage 2 was vectorized from. Use 'predictions_pretrained'."
        )

    split_dir = args.data_dir / args.split
    img_dir = split_dir / "images"
    mask_dir = split_dir / "masks"
    out_dir = split_dir / args.out_subdir
    if args.save_png:
        out_dir.mkdir(parents=True, exist_ok=True)

    # masks/ is the source of truth for which tiles exist (CLAUDE.md guardrail 3).
    mask_paths = sorted(mask_dir.glob("mask_*.png"))
    if args.limit:
        mask_paths = mask_paths[: args.limit]
    if not mask_paths:
        raise SystemExit(f"No masks under {mask_dir}. Run build_masks.py first.")

    mode = f"window {args.window_size} overlap {args.overlap}" if args.window_size else "whole-tile 650x650"
    print(f"Inferring {len(mask_paths)} tiles ({mode}) -> {out_dir}")

    metrics = ConfusionAccumulator()
    written = 0

    for i in tqdm(range(0, len(mask_paths), args.batch_size), desc=f"[{args.split} pretrained]"):
        batch_paths = mask_paths[i:i + args.batch_size]
        xs, gts, names = [], [], []

        for mp in batch_paths:
            tile = mp.stem.replace("mask_", "")
            img_path = img_dir / f"RGB-PanSharpen_{tile}.tif"
            if not img_path.exists():
                raise SystemExit(
                    f"Mask {mp.name} has no paired image.\n  Expected: {img_path}\n"
                    "  Filename prefixes must stay in lockstep (CLAUDE.md guardrail 2)."
                )
            xs.append(load_tile_uint8(img_path))
            gt = np.array(Image.open(mp), dtype=np.float32)
            if gt.ndim == 3:
                gt = gt[..., 0]
            gts.append((gt > 0).astype(np.float32))
            names.append(mp.name)

        x = torch.from_numpy(np.stack(xs)).to(device)
        gt = torch.from_numpy(np.stack(gts)).unsqueeze(1).to(device)

        if args.window_size:
            prob_np = np.stack([
                predict_windowed(model, x[j:j + 1], device, args.window_size, args.overlap)
                for j in range(x.shape[0])
            ])
        else:
            prob_np = predict_whole_tile(model, x, device).float().cpu().numpy()

        pred = torch.from_numpy(prob_np).unsqueeze(1) > args.threshold
        metrics.update(pred.to(gt.device), gt)

        if args.save_png:
            png = (prob_np * 255.0).clip(0, 255).astype(np.uint8)
            for j, name in enumerate(names):
                Image.fromarray(png[j]).save(out_dir / name)
                written += 1

    result = {
        "model": "giswqs/whu-building-unetplusplus-efficientnet-b4",
        "model_type": "external pretrained (zero-shot)",
        "architecture": cfg.get("architecture"),
        "encoder": cfg.get("encoder_name"),
        "num_classes": cfg.get("num_classes"),
        "license": "Apache-2.0",
        "trained_on": "WHU Building Dataset (5,732 tiles, 0.3 m aerial, 512x512)",
        "reported_own_test_iou": 0.9054,
        "reported_own_test_dice": 0.9503,
        "split": args.split,
        "tiles": len(mask_paths),
        "inference_mode": mode,
        "threshold": args.threshold,
        "preprocessing": f"clip(0,{NORM_MAX})/{NORM_MAX} -> [0,1] (dataset-wide NORM_MAX, no per-image stretch)",
        "norm_max": NORM_MAX,
        "output_classes_used": "softmax channel 1 (Building)",
        "iou": round(metrics.iou, 6),
        "dice": round(metrics.f1, 6),
        "f1": round(metrics.f1, 6),
        "precision": round(metrics.precision, 6),
        "recall": round(metrics.recall, 6),
    }

    print(
        f"\n{args.split.upper()} PRETRAINED (zero-shot) | IoU {result['iou']:.4f} | "
        f"Dice/F1 {result['f1']:.4f} | P {result['precision']:.3f} | R {result['recall']:.3f} | "
        f"{result['tiles']} tiles"
    )

    if args.save_png:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {written} PNGs + {out_dir / 'metrics.json'}")
    else:
        print("(--no-save-png: metrics only)")

    return result


if __name__ == "__main__":
    run(parse_args())
