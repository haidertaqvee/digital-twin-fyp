# Pretrained baseline model

Zero-shot baseline for the Stage-1 head-to-head comparison
(`src/stage1_extraction/evaluate.py`).

## Model

`giswqs/whu-building-unetplusplus-efficientnet-b4` — Apache-2.0.

UNet++ / EfficientNet-B4 (ImageNet encoder), ~20.8M params, 84 MB. Trained on
the WHU Building Dataset (5,732 tiles, **0.3 m aerial**, 512x512 RGB); reports
IoU 0.9054 / Dice 0.9503 on its own test split. Resolution-matched to SpaceNet
Vegas (~0.3 m/pixel), so the zero-shot score is credible cross-dataset transfer
rather than a strawman.

## Why not Microsoft

The task called for Microsoft's Global ML Building Footprints pretrained weights.
**Microsoft has never released them.** `microsoft/GlobalMLBuildingFootprints`
publishes only the derived vector output (~113 GB of `.csv.gz` footprint tiles),
not the segmentation model, training code, or an ONNX export.
`github.com/microsoft/BuildingFootprints` is a 404. So we substitute the
strongest freely downloadable equivalent.

## Files

This directory is **gitignored** (`models/` in `.gitignore`). Re-download with:

```powershell
E:\digital-twin-fyp\envs\digital-twin\python.exe -c "from huggingface_hub import hf_hub_download; import shutil, pathlib; d=pathlib.Path('models/pretrained/whu-building-unetplusplus-efficientnet-b4'); d.mkdir(parents=True, exist_ok=True); [shutil.copy(hf_hub_download(repo_id='giswqs/whu-building-unetplusplus-efficientnet-b4', filename=f), d/f) for f in ['config.json','model.pth','README.md']]"
```

## Usage

```powershell
# Zero-shot predictions -> data/processed/<split>/predictions_pretrained/
E:\digital-twin-fyp\envs\digital-twin\python.exe src/stage1_extraction/predict_pretrained.py --split test

# Head-to-head table + figures -> results/metrics_comparison.{json,md}
E:\digital-twin-fyp\envs\digital-twin\python.exe src/stage1_extraction/evaluate.py
```

## Preprocessing note

The upstream `geoai` loader does `img/255.0` when `img.max() > 1.0` — wrong for
our uint16 SpaceNet tiles (max ~1910 would land at 7.5). We instead use
`clip(0, NORM_MAX)/NORM_MAX`, the same dataset-wide constant as our training
path (`NORM_MAX = 1910.0`, never per-image). Both models see the identical
monotone intensity mapping, so the measured gap reflects domain transfer, not
normalization differences.

UNet++/EfficientNet-B4 requires H,W divisible by 32; 650x650 tiles are
reflect-padded to 672x672 and cropped back (`_pad_to_multiple`).
