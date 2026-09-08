# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

FYP "AI-Driven Semantic Digital Twins for Autonomous Systems Simulation" (BS Space Science, Institute of Space Technology, supervised by Dr. Sajid Ghuffar). Full methodology is in `docs/FYP_Proposal.docx`.

The intended pipeline is five stages, mirrored by `src/stage{1..5}_*`:
1. `stage1_extraction` — semantic feature extraction (building segmentation from SpaceNet imagery)
2. `stage2_enrichment` — attribute enrichment
3. `stage3_reconstruction` — 3D reconstruction
4. `stage4_change_detection` — change detection
5. `stage5_simulation` — simulation integration (Isaac Sim / Gazebo)

**Only stage 1 currently has code; `stage2`–`stage5` are empty directory scaffolds.** Stage 1 today is data preparation for building-footprint segmentation — building the train/val/test dataset and PyTorch dataloader. No model/training code exists yet.

## Environment & running

There is no root `requirements.txt`, `environment.yml`, or build/lint/test tooling. Dependencies live in a **prefix conda env checked into the repo** at `envs/digital-twin/` (Python 3.10; pip-installed torch 2.13, torchvision 0.28, rasterio 1.4, geopandas 1.1, plus numpy, Pillow, matplotlib):

```powershell
conda activate E:\digital-twin-fyp\envs\digital-twin
```

Scripts are run directly, e.g. `python src/stage1_extraction/dataset.py`. The stage-1 data pipeline must run in this order, since each script consumes the previous one's output under `data/processed/`:

1. `build_subset.py` — samples 999 tiles from raw SpaceNet, splits 70/15/15, copies images+labels into `data/processed/{train,val,test}/{images,labels}`
2. `build_masks.py` — rasterizes the geojson footprints into 0/255 PNG masks under `.../masks/`
3. `dataset.py` — run directly as a smoke test of the `SpaceNetDataset` dataloader

`check_pixel_stats` (a one-off; **note: no `.py` extension** despite its docstring — run `python src/stage1_extraction/check_pixel_stats`) derived the normalization ceiling and rarely needs re-running. `verify_masks.py`, `check_rotation.py`, `visualize_sample.py`, and `visualize_samples_grid.py` are diagnostic/visualization scripts.

## Architecture & conventions

**Data source:** SpaceNet SN2 buildings, `AOI_2_Vegas`. Raw data (`data/raw/`), `data/processed/`, and `models/` are gitignored and not present in a fresh clone — the stage-1 scripts assume they exist locally.

**Hardcoded absolute paths:** Every stage-1 script hardcodes `E:/digital-twin-fyp/...` paths as module-level constants rather than taking arguments or using paths relative to the repo. Scripts therefore run from any CWD but only on this machine's layout. Preserve/update these constants together when moving data; don't assume CWD-relative behavior.

**Parallel filename conventions** tie the three artifact types together, and scripts map between them with string `.replace()` (not a shared helper):
- image `RGB-PanSharpen_AOI_2_Vegas_img{N}.tif` ↔ label `buildings_AOI_2_Vegas_img{N}.geojson` ↔ mask `mask_AOI_2_Vegas_img{N}.png`

Keep these three names in lockstep; changing one prefix breaks the lookups in `dataset.py`, `build_masks.py`, and the verify/visualize scripts.

**Fixed dataset-wide normalization (`NORM_MAX = 1910.0` in `dataset.py`):** images are clipped to `NORM_MAX` and divided by it — the same constant for every tile. This is deliberate (see the comment): normalization must NOT be computed per-image, or the model sees inconsistent brightness for the same material. `NORM_MAX` is the 95th percentile of per-tile maxima from `check_pixel_stats`. The visualization scripts use per-image min/max stretch instead — that is only for display, not for the training path.

**Tile filtering:** `build_masks.py` skips tiles whose no-data (all-zero) pixel fraction exceeds 15%, and reprojects building geometries to the image CRS before rasterizing. `dataset.py` lists `masks/` (not `images/`) as the source of truth, so only tiles that survived mask generation are seen during training.

## Vendored upstream repos

`satnerf/` and `sat-bundleadjust/` are **separate git clones** (from github.com/centreborelli), not submodules and not part of this repo's own history — they are untracked and have their own `.git`, `README.md`, `requirements.txt`, and setup scripts (e.g. `satnerf/setup_satnerf_env.sh`). They are upstream reference/dependency code for the future stage-3 reconstruction and use their own environments and conventions. Treat them as third-party: read their own docs before touching them, and don't refactor them to match project code.
