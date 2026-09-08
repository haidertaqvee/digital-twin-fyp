# TerraTwin — Domain Guardrails

These five invariants must not be "helpfully" broken. Read them before editing
any stage-1 file, especially `dataset.py`, `build_masks.py`, `build_subset.py`,
`train.py`, or `train_unet.py`.

## 1. `NORM_MAX = 1910.0` is dataset-wide and FIXED

In `src/stage1_extraction/dataset.py`, every tile is clipped to `NORM_MAX` and
divided by the **same constant**. This is deliberate: per-image normalization
would make the model see inconsistent brightness for the same real material
across tiles, hurting generalization.

`NORM_MAX` is the 95th percentile of per-tile maxima from `check_pixel_stats`
(a one-off; no `.py` extension — run `python src/stage1_extraction/check_pixel_stats`).
Do **not** recompute it from new data without explicit user approval.

The visualization scripts (`verify_masks.py`, `visualize_sample.py`,
`visualize_samples_grid.py`, `verify_alignment.py`) use **per-image min/max stretch
for display only** — that is *not* the training path. Don't confuse the two.

## 2. Keep the three filename prefixes in lockstep

Every stage-1 script maps between these three names with string `.replace()`,
not a shared helper. Break one prefix and you silently break lookups in
`dataset.py`, `build_masks.py`, and all verify/visualize scripts:

| Type | Pattern |
|------|---------|
| image | `RGB-PanSharpen_AOI_2_Vegas_img{N}.tif` |
| label | `buildings_AOI_2_Vegas_img{N}.geojson` |
| mask  | `mask_AOI_2_Vegas_img{N}.png` |

If a prefix must change, change it in **all** files together — and re-run the
verify scripts to confirm the alignment still holds.

## 3. `masks/` is the source of truth, not `images/`

`dataset.py` lists `masks/` (not `images/`) when building the dataset. Only
tiles that survived `build_masks.py` (no-data ≤ 15%, label file present) are
seen during training. Do not switch the source to `images/` without also
re-running the mask filter.

## 4. TerraTwin is Unity only — no Isaac Sim, Gazebo, ROS, or Sat-NeRF

The simulation target is **Unity URP** (heightmap + landcover). Sat-NeRF and
change detection are explicitly **future work** recorded in
`~/.claude/projects/e--digital-twin-fyp/memory/product-direction-gis-to-game.md`.

`satnerf/` and `sat-bundleadjust/` are **separate git clones** (from
github.com/centreborelli), not submodules, not part of this repo's history.
They are untracked and have their own `.git`, `README.md`, `requirements.txt`,
and setup scripts. Treat them as third-party: read their own docs before
touching them; **do not refactor them to match project code**.

Do not suggest Isaac Sim, Gazebo, ROS, or Sat-NeRF as the next step.

## 5. `train_unet.py` is primary; `train.py` is fallback — don't silently switch

- **Primary:** `src/stage1_extraction/train_unet.py` — `smp.Unet(ResNet34,
  encoder_weights="imagenet")`. Accepts `--data-dir`/`--ckpt-dir`/`--epochs`/
  `--batch-size`/`--tile-size`/`--limit`/`--seed`/`--lr` with defaults that
  preserve the local `E:/...` layout. Pretrained encoder learns building
  footprints faster on the small (673-tile) training set. Keep `--epochs 15`
  for the hackathon.
- **Fallback:** `src/stage1_extraction/train.py` + `model.py` (hand-written
  UNet from scratch; AMP, `--resume`, scheduler, split-wide confusion metrics).
  Left in repo for local fallback training; does **not** use `smp`.

`train_unet.py`'s per-batch averaged IoU/F1 is weaker than `train.py`'s
split-wide confusion accumulation, but the pretrained encoder is worth it on
this dataset size. If the user wants to switch primary/fallback, ask first.
