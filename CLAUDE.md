# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**TerraTwin** — automated pipeline from satellite imagery → AI segmentation → vectorized 3D → Unity. See [CONTEXT.md](CONTEXT.md) for the authoritative mission, stack, rules, and current status.

- **FYP** "AI-Driven Semantic Digital Twins for Autonomous Systems Simulation" (BS Space Science, IST, Dr. Sajid Ghuffar), **and** solo submission to the **AI Builders Hackathon (Devpost)** — **deadline Sept 15, 2026 11:00 PM EDT**.
- **Pipeline (TerraTwin, 4 stages; the `src/stage1..5_*` folder names are historical):**
  1. `stage1_extraction` — semantic feature extraction (building segmentation from SpaceNet imagery)
  2. `stage2_enrichment` — attribute enrichment (vectorize masks → georeferenced polygons + height heuristic)
  3. `stage3_reconstruction` — 3D extrusion
  4. `stage4_change_detection` / `stage5_simulation` — originally Isaac Sim/Gazebo in the FYP framing; for TerraTwin the simulation target is **Unity URP** (heightmap + landcover). Stages 1–2 are active; `stage3`–`stage5` are empty scaffolds.
- **Current status:** Stage 1 is **trained and evaluated** — `smp.Unet(ResNet34)`, best epoch 11, **val IoU 0.8040 / F1 0.8913**, **test IoU 0.8062 / F1 0.8927** (146 tiles, never used for model selection). Checkpoint at `models/unet_resnet34_best.pth`. Stage 2 vectorization is built and verified (round-trip IoU 0.992–0.996 vs original SpaceNet labels). See CONTEXT.md "Current Project Status" for the full record.

## Environment & running

### Dependency manifests

Reproducible installs live at the repo root (added 2026-09-08; previously only the `envs/` prefix env existed, which is gitignored and machine-local):

- [requirements.txt](requirements.txt) — `pip install -r requirements.txt` (CPU default; for CUDA/ROCm see the comments inside the file).
- [environment.yml](environment.yml) — `conda env create -f environment.yml`.

The **prefix conda env checked into the working tree** at `envs/digital-twin/` (Python 3.10) is the active local env: **torch 2.5.1+cu121, torchvision 0.20.1+cu121** (installed 2026-09-09 from the `cu121` index, running on the GTX 1660 Super), rasterio 1.4.4, geopandas 1.1.4, shapely 2.1.2, `segmentation_models_pytorch` 0.5.0, `timm` 1.0.29, sympy 1.13.1, plus numpy, Pillow, tqdm, matplotlib. `requirements.txt` / `environment.yml` were re-frozen to these versions on 2026-09-09 — **the cu121 index does not publish torch 2.13.0**, which the manifests previously pinned.

Note `torch` was **absent** from this env until 2026-09-09 despite the manifests claiming 2.13.0 — verify with an import before trusting a manifest:

```powershell
conda activate E:\digital-twin-fyp\envs\digital-twin
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
# -> 2.5.1+cu121 True NVIDIA GeForce GTX 1660 SUPER
```

To reinstall (CPU/CUDA/ROCm):

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --upgrade
```

### Training surfaces (the important distinction)

- **Primary:** [train_unet.py](src/stage1_extraction/train_unet.py) — `smp.Unet(ResNet34, encoder_weights="imagenet")`. Accepts `--data-dir` / `--ckpt-dir` / `--epochs` / `--batch-size` / `--tile-size` / `--num-workers` / `--lr` / `--pos-weight` / `--patience` / `--amp {off,bf16,fp16}` / `--resume` / `--limit` / `--seed`. Defaults preserve the local `E:/...` layout so `python src/stage1_extraction/train_unet.py` with no flags still works. Keep `--epochs 15` for the hackathon. First run downloads `timm` weights (needs internet, then caches).
- **Inference:** [inference.py](src/stage1_extraction/inference.py) — `--split test` loads `models/unet_resnet34_best.pth`, runs whole-tile (650×650) prediction, and writes `<split>/predictions/mask_*.png` plus `metrics.json`.
- **Fallback:** [train.py](src/stage1_extraction/train.py) + [model.py](src/stage1_extraction/model.py) — hand-written UNet from scratch (AMP, `--resume`, scheduler, split-wide confusion metrics). Left in repo as a fallback; does not use `smp`. **The primary trainer imports `ConfusionAccumulator` and `DiceLoss` from `train.py`**, so both compute IoU/F1 identically — do not fork these helpers.

### Two hard-won facts about this training setup

1. **`fp16` autocast NaNs this model.** The *forward pass alone* returns NaN logits (no gradient step
   involved) — a run would silently train on nothing and report loss `nan`. `bf16` and fp32 are clean, so
   `--amp bf16` is the default and `--amp fp16` should not be used. bf16 wants autocast **on** but the
   `GradScaler` **off** (its exponent range matches fp32, so gradients cannot underflow); `resolve_amp()`
   in `train_unet.py` encodes that pairing — don't infer autocast state from `scaler.is_enabled()`.
2. **A fresh run silently overwrote the previous best checkpoint.** A new run starts at `best_val_iou=0.0`,
   so its first epoch always "wins" and writes straight over the old file — and `models/` is gitignored, so
   the loss is unrecoverable. `archive_existing_best()` now moves any existing best to
   `models/archive/unet_resnet34_best_<timestamp>.pth` first. The unvalidated Sept-8 checkpoint was lost
   this way before the guard existed.

### Stage-1 data pipeline (run in order; each script consumes the previous one's output under `data/processed/`)

1. `build_subset.py` — samples 999 tiles from raw SpaceNet, splits 70/15/15, copies images+labels into `data/processed/{train,val,test}/{images,labels}`. Top-level work is now guarded behind `if __name__ == "__main__":`.
2. `build_masks.py` — rasterizes the geojson footprints into 0/255 PNG masks under `.../masks/`
3. `dataset.py` — run directly as a smoke test of the `SpaceNetDataset` dataloader; also supports `--data-dir` overrides and fails fast if a mask's `.tif` is missing.
4. Train: `python src/stage1_extraction/train_unet.py --epochs 15 --batch-size 8 --num-workers 0` (primary) or `train.py` with its own argparse.
5. Infer + vectorize: `python src/stage1_extraction/inference.py --split test` then `python src/stage2_enrichment/vectorize.py --split test --source predictions`.

Quick checks:
```powershell
python src/stage1_extraction/train_unet.py --help     # flags without a GPU
python src/stage1_extraction/train_unet.py --epochs 1 --limit 4 --num-workers 0   # smoke test, needs GPU
```

### Stage 2 — enrichment (vectorize + heights)

`src/stage2_enrichment/` turns masks into georeferenced polygons with heights. See its [README.md](src/stage2_enrichment/README.md) for the full record.

- `vectorize.py` is the **exact inverse of `build_masks.py`**: it reads each tile's affine transform off the paired `.tif` and runs `rasterio.features.shapes`, so polygons land back in **EPSG:4326**. Accepts `--source masks` (ground truth) or `--source predictions` (model output, thresholded). Verified round-trip **IoU 0.992–0.996** against the original SpaceNet labels.
- `heights.py` is the **only place heights are invented**, and it must stay explicit: SpaceNet Vegas has **no height data** (all `POLYGON Z` have Z=0; `AREA`/`Shape_Leng`/`SISL` are all zero; `Shape_Le_3` is square *degrees*). The area→levels→metres table is a documented heuristic with thresholds derived from the observed footprint distribution. Swap `estimate_levels()` for a DSM or OSM `building:levels` join when one exists — it is the only symbol `vectorize.py` imports.
- **Never present `height_m` as measured.** The README and `describe_heuristic()` exist so the assumption stays visible in any report or demo.

`check_pixel_stats` (a one-off; **note: no `.py` extension** despite its docstring — run `python src/stage1_extraction/check_pixel_stats`) derived the normalization ceiling and rarely needs re-running. `verify_masks.py`, `check_rotation.py`, `visualize_sample.py`, and `visualize_samples_grid.py` are diagnostic/visualization scripts.

## Architecture & conventions

**Data source:** SpaceNet SN2 buildings, `AOI_2_Vegas`. Raw data (`data/raw/`), `data/processed/`, and `models/` are gitignored and not present in a fresh clone — the stage-1 scripts assume they exist locally.

**Paths:** `build_subset.py`, `build_masks.py`, and `dataset.py` still hardcode `E:/digital-twin-fyp/...` constants; `train_unet.py` now externalizes them via `--data-dir`/`--ckpt-dir` argparse defaults so the bundle runs on Linux/ROCm without editing. `train.py` already had `--data-dir`/`--ckpt-dir`. When moving data, update these together; don't assume CWD-relative behaviour.

**Parallel filename conventions** tie the three artifact types together, and scripts map between them with string `.replace()` (not a shared helper):
- image `RGB-PanSharpen_AOI_2_Vegas_img{N}.tif` ↔ label `buildings_AOI_2_Vegas_img{N}.geojson` ↔ mask `mask_AOI_2_Vegas_img{N}.png`

Keep these three names in lockstep; changing one prefix breaks the lookups in `dataset.py`, `build_masks.py`, and the verify/visualize scripts.

**Fixed dataset-wide normalization (`NORM_MAX = 1910.0` in `dataset.py`):** images are clipped to `NORM_MAX` and divided by it — the same constant for every tile. This is deliberate (see the comment): normalization must NOT be computed per-image, or the model sees inconsistent brightness for the same material. `NORM_MAX` is the 95th percentile of per-tile maxima from `check_pixel_stats`. The visualization scripts use per-image min/max stretch instead — that is only for display, not for the training path.

**Tile filtering:** `build_masks.py` skips tiles whose no-data (all-zero) pixel fraction exceeds 15%, and reprojects building geometries to the image CRS before rasterizing. `dataset.py` lists `masks/` (not `images/`) as the source of truth, so only tiles that survived mask generation are seen during training.

**Deployment bundle:** `terratwin_deployment.tar.gz` at the repo root (regenerated 2026-09-08, 1.5 GB, includes `src` + `data/processed` + `requirements.txt` + `environment.yml` + `CONTEXT.md`, no `__pycache__`). Primary training is local on the GTX 1660 Super now; the bundle is the AMD MI300X fallback (SCP → extract → `python src/stage1_extraction/train_unet.py --data-dir ./data/processed`).

## Guardrails

- **TerraTwin is Unity only.** Do not suggest Isaac Sim, Gazebo, ROS, or Sat-NeRF (Sat-NeRF / `satnerf` and `sat-bundleadjust` are future work; `satnerf/` and `sat-bundleadjust/` are separate vendored clones — their own `.git`, don't refactor).
- **Do not re-normalize per-image.** `NORM_MAX = 1910.0` is dataset-wide and fixed.
- **Dead hackathons:** Arm AI Optimization Challenge and Google Cloud AI Builder Cup are not in scope — only AI Builders Hackathon.
- **Contributing when unsure:** prefer asking over "helpfully" recomputing normalization or renaming filename prefixes. Phase D adds `.claude/commands/` and guardrails for session bootstrap.

## Vendored upstream repos

`satnerf/` and `sat-bundleadjust/` are **separate git clones** (from github.com/centreborelli), not submodules and not part of this repo's own history — they are untracked and have their own `.git`, `README.md`, `requirements.txt`, and setup scripts (e.g. `satnerf/setup_satnerf_env.sh`). They are upstream reference/dependency code for the future stage-3 reconstruction and use their own environments and conventions. Treat them as third-party: read their own docs before touching them, and don't refactor them to match project code.
