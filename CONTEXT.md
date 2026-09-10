# TerraTwin — Project Context & Memory

## The Mission
I am developing **TerraTwin**, a geospatial digital twin pipeline that converts high-resolution satellite imagery into simulation-ready 3D environments. This bridges GIS/remote sensing with game development.
* **Dual Purpose:** This is my Final Year Project for my BS in Space Science at the Institute of Space Technology (supervised by Dr. Sajid Ghuffar), and my solo student submission for the **AI Builders Hackathon** on Devpost.
* **Hard Deadline:** September 15, 2026, 11:00 PM EDT.
* **Goal:** A working automated pipeline (Phase 1-4) and a polished Unity demo neighborhood.

## The Pipeline & Tech Stack
1. **Stage 1 (Current):** Satellite image building footprint segmentation (PyTorch, `segmentation_models_pytorch` U-Net with ResNet34 backbone, BCE+Dice loss).
2. **Stage 2 (built):** Vectorize masks to georeferenced polygons and attach a documented height heuristic (Rasterio, GeoPandas, Shapely).
3. **Stage 3:** Extrude 3D meshes and export.
4. **Stage 4:** Unity URP integration (using `heightmap.png` and `landcover.png` to drive procedural terrain generation and building population).

## The Data (Fully Prepared & Verified)
* **Dataset:** SpaceNet 2 (Las Vegas), downloaded from AWS Open Data.
* **Status:** 999-tile subset completely prepared and verified (**673 train / 144 val / 146 test = 963 masks**; the 699/149/151 figures are pre-filter image counts). Raster CRS matches GeoJSON CRS perfectly (EPSG:4326).
* **Environment:** `envs/digital-twin/` (Conda prefix env, Python 3.10) running locally on Windows (E: drive), with **torch 2.5.1+cu121 on the GTX 1660 Super (6 GB)** — CUDA verified working and used for the Stage-1 training run. Dependencies pinned in `requirements.txt` + `environment.yml` (re-frozen 2026-09-09). The AMD MI300X (ROCm) path remains the untested fallback.

## Training Scripts
* **Primary:** `src/stage1_extraction/train_unet.py` — `smp.Unet(ResNet34, encoder_weights="imagenet")`. Accepts `--data-dir` / `--ckpt-dir` / `--epochs` / `--batch-size` / `--tile-size` / `--amp {off,bf16,fp16}` / `--pos-weight` / `--patience` / `--resume` / `--limit` / `--seed` (defaults preserve local `E:/...` behaviour). Defaults to **bf16** autocast — fp16 NaNs this model. Writes `best.pth` (on val-IoU improvement), `last.pt` (every epoch, resumable), and `unet_resnet34_history.json`; archives any pre-existing best checkpoint to `models/archive/`.
* **Inference:** `src/stage1_extraction/inference.py --split test` — whole-tile (650×650) prediction PNGs + `metrics.json` with split-wide IoU/F1/P/R.
* **Fallback:** `src/stage1_extraction/train.py` + `model.py` (hand-written UNet from scratch) — richer loop (`--resume`, scheduler, split-wide confusion metrics). Its `ConfusionAccumulator` and `DiceLoss` are **imported by the primary trainer**, so both score metrics identically. Does not use `smp`.

## Current Project Status (2026-09-09)

### Stage 1 — segmentation model TRAINED (this is the real result)
* **`smp.Unet(ResNet34, ImageNet)` trained for 15 epochs on the GTX 1660 Super.** Best epoch **11**:
  * **Val (144 tiles): IoU 0.8040 | F1 0.8913 | P 0.907 | R 0.876**
  * **Test (146 tiles, never used for model selection): IoU 0.8062 | F1 0.8927 | P 0.910 | R 0.876**
  * Test ≈ val (marginally higher), so the model generalizes rather than overfitting the val split.
* **Checkpoint:** `models/unet_resnet34_best.pth` (~293 MB, epoch 11). `models/last.pt` holds epoch 15.
  Per-epoch curve in `models/unet_resnet34_history.json`; full console log in `models/train_unet_full.log`.
* Val IoU plateaued from epoch 8 (0.7904) onward while train loss kept falling (0.43 → 0.32) — mild
  overfitting on a 673-tile set. `best.pth` correctly retains epoch 11, not the final epoch.
* **Environment:** torch **2.5.1+cu121** / torchvision **0.20.1+cu121** (the cu121 index does not publish
  the 2.13.0 that `requirements.txt` previously pinned — manifests now record what actually ran).
  `requirements.txt` and `environment.yml` re-frozen 2026-09-09.

### Two bugs found and fixed while getting training to run
1. **`fp16` autocast produces NaN logits** with this smp ResNet34 (reproduced: the *forward pass* alone
   returns NaN, before any gradient step — a 15-epoch run would have silently trained on nothing).
   `bf16` and fp32 are clean. `train_unet.py` now defaults to **bf16** with `--amp {off,bf16,fp16}`.
2. **A fresh run silently overwrote the previous best checkpoint.** A new run starts at `best_val_iou=0.0`,
   so its first epoch always "wins" and writes straight over the old file — and `models/` is gitignored, so
   an overwritten checkpoint is unrecoverable. `archive_existing_best()` now moves any existing best into
   `models/archive/unet_resnet34_best_<timestamp>.pth` first. (The unvalidated Sept-8 checkpoint was lost
   this way before the guard existed; it had never been loaded or scored.)

### Stage 2 — vectorization BUILT AND VERIFIED
* `src/stage2_enrichment/vectorize.py` inverts `build_masks.py` exactly: reads each tile's affine transform
  off the paired `.tif` and runs `rasterio.features.shapes`, so polygons land back in **EPSG:4326**.
* **Round-trip validated against the original SpaceNet labels: IoU 0.992–0.996** on sampled test tiles,
  polygon counts within ≤1 per tile, median areas agreeing within ~5 m².
* **Predicted masks → vectors:** 3,621 polygons over 140 tiles (vs 3,987 GT = ratio 0.908), and
  **vector-vs-vector IoU mean 0.7944 / median 0.8134** across all 140 tiles (98.6% of tiles ≥ 0.5) —
  consistent with the 0.8062 pixel IoU.
* `src/stage1_extraction/inference.py` runs whole-tile (650×650) inference, writing prediction PNGs plus
  `metrics.json` computed with the *same* `ConfusionAccumulator` used in training.
* **Heights are a documented heuristic, not a measurement.** Verified over 1,561 features / 40 tiles that
  SpaceNet Vegas carries no height signal: all geometries are `POLYGON Z` with **Z exactly 0.0**, and
  `AREA`/`Shape_Leng`/`Shape_Le_1`/`SISL` are all zero (`Shape_Le_3` is square *degrees*). `heights.py` maps
  footprint area → levels (1/2/3/4 capped) → metres at 3.0 m/level, with the thresholds derived from the
  observed distribution (median 164 m², p95 417 m², ~29.7 buildings/tile). See `src/stage2_enrichment/README.md`.
* Data counts confirmed on disk: **673 train / 144 val / 146 test masks** (999 sampled tiles; the 699/149/151
  figures are pre-filter *image* counts). Tiles: EPSG:4326, 650×650, uint16, ~0.3 m/pixel (~195×195 m on the ground).

### Still to be created
* **Stage 3** (extrude the vectors into 3D meshes / glTF) and **Stage 4** (Unity URP scene) — the demo
  centerpiece. Note `data/processed/test/vectors/buildings_predictions.geojson` is ready to drive it.
* Known rough edge: **3.7% of polygons are under 5 m²** (24.7% under 50 m²) — mostly raster speckle on
  *predicted* masks. Raise `--min-area-px` before feeding Unity rather than trusting every polygon.
* **Dead hackathons to ignore:** Arm AI Optimization Challenge, Google Cloud AI Builder Cup.
  **No Sat-NeRF / Isaac Sim / Gazebo** in scope for the MVP.

## Immediate Next Steps
1. **Stage 3:** extrude `buildings_predictions.geojson` using its `height_m` column → glTF/OBJ per tile.
2. **Stage 4:** Unity URP scene for one demo neighborhood (Cesium for Unity for georeferencing).
3. **Optional Stage-1 improvements** (only if time allows before Sept 15): longer schedule with early
   stopping, `--pos-weight >1` to trade precision for recall, or TTA at inference. The current 0.806 test IoU
   is already strong enough to drive the pipeline — per the deadline, Stage 2/4 quality matters more than
   squeezing another IoU point.
4. **Devpost submission:** the test metrics above plus a predicted-vs-GT overlay figure are the headline numbers.

## Strict Rules for AI Assistance
1. **No feature creep:** Do not suggest Isaac Sim, Gazebo, ROS, or Satellite Gaussian Splatting (Sat-NeRF) right now. Those are long-term stretch goals. Focus purely on the Unity MVP.
2. **No dead hackathons:** Ignore previous plans for the Arm AI Optimization Challenge or Google Cloud AI Builder Cup.
3. **Code style:** Provide practical, working code to unblock the immediate next step. Assume Windows PowerShell for local terminal commands. Explain new concepts before asking the user to choose.

## Immediate Next Steps
1. **Hardware:** Install the GTX 1660 Super, verify `nvidia-smi` sees it and the GeForce driver is installed.
2. **CUDA torch:** In `envs/digital-twin`:
   `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --upgrade`
   then confirm `python -c "import torch; print(torch.cuda.is_available())"` is `True`.
3. **Smoke test:** `python src/stage1_extraction/train_unet.py --epochs 1 --limit 4` (first run downloads `timm` ImageNet weights once, then caches).
4. **Full run:** `python src/stage1_extraction/train_unet.py --epochs 15 --batch-size 8` (~1–1.5h, fits in one sitting; drop to batch 4 on OOM). Output: `models/unet_resnet34_best.pth`.
5. **AMD fallback (only if needed):** `tar` bundle is already correct; SCP and run `python src/stage1_extraction/train_unet.py --data-dir ./data/processed --ckpt-dir ./models`.
6. **After training:** Stage 2 (vectorize masks → heights → 3D) and Stage 4 (Unity). Building-height source must be a documented heuristic — never silently invented.
