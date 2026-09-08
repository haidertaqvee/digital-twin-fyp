# TerraTwin — Project Context & Memory

## The Mission
I am developing **TerraTwin**, a geospatial digital twin pipeline that converts high-resolution satellite imagery into simulation-ready 3D environments. This bridges GIS/remote sensing with game development.
* **Dual Purpose:** This is my Final Year Project for my BS in Space Science at the Institute of Space Technology (supervised by Dr. Sajid Ghuffar), and my solo student submission for the **AI Builders Hackathon** on Devpost.
* **Hard Deadline:** September 15, 2026, 11:00 PM EDT.
* **Goal:** A working automated pipeline (Phase 1-4) and a polished Unity demo neighborhood.

## The Pipeline & Tech Stack
1. **Stage 1 (Current):** Satellite image building footprint segmentation (PyTorch, `segmentation_models_pytorch` U-Net with ResNet34 backbone, BCE+Dice loss).
2. **Stage 2:** Vectorize masks to georeferenced polygons and estimate building heights (Rasterio, GeoPandas).
3. **Stage 3:** Extrude 3D meshes and export.
4. **Stage 4:** Unity URP integration (using `heightmap.png` and `landcover.png` to drive procedural terrain generation and building population).

## The Data (Fully Prepared & Verified)
* **Dataset:** SpaceNet 2 (Las Vegas), downloaded from AWS Open Data.
* **Status:** 999-tile subset completely prepared and verified (673 train / 144 val / 146 test = 963 masks). Raster CRS matches GeoJSON CRS perfectly.
* **Environment:** `envs/digital-twin/` (Conda, Python 3.10) running locally on Windows (E: drive). Dependencies pinned in `requirements.txt` + `environment.yml`. Primary training hardware: GTX 1660 Super (6 GB VRAM, CUDA) installed locally — also tested/sized for the AMD MI300X (ROCm) fallback path.

## Training Scripts
* **Primary:** `src/stage1_extraction/train_unet.py` — `smp.Unet(ResNet34, encoder_weights="imagenet")`. Accepts `--data-dir` / `--ckpt-dir` / `--epochs` / `--limit` / `--seed` (defaults preserve local `E:/...` behaviour). Pretrained encoder → faster convergence on 673 tiles. Keep `--epochs 15` for the hackathon submission.
* **Fallback:** `src/stage1_extraction/train.py` + `model.py` (hand-written UNet from scratch) — richer loop (AMP, `--resume`, scheduler, split-wide confusion metrics). Left in repo as a local-training fallback; does not use `smp`.

## Current Project Status (2026-09-08)
* `build_subset.py`, `build_masks.py`, and `dataset.py` (with `NORM_MAX = 1910.0`) are fully complete.
* `train_unet.py` has been reworked with `argparse` (`--data-dir`/`--ckpt-dir` etc.), seeding, `import os` removed, and `MODEL_SAVE_DIR.mkdir()` guarded behind `__main__`. Verified: `python src/stage1_extraction/train_unet.py --help` works locally without GPU. Next: install GTX 1660 Super → CUDA torch → `--epochs 1 --limit 4` smoke test → full 15-epoch run.
* `requirements.txt` and `environment.yml` (CPU default; CUDA via `cu121`, ROCm via `rocm6.2`) now exist so the environment is reproducible.
* `terratwin_deployment.tar.gz` (1.5 GB, 2995 entries, includes `data/processed` + `requirements.txt` + `environment.yml` + `CONTEXT.md`, no `__pycache__`) regenerated; ready as the AMD cloud fallback bundle.
* **Still to be created:** Unity project (Stage 4), and building-height estimation for Stage 2 (SpaceNet Vegas has no `building:levels`/DSM — documented heuristic needed).
* **Dead hackathons to ignore:** Arm AI Optimization Challenge, Google Cloud AI Builder Cup. **No Sat-NeRF / Isaac Sim / Gazebo** in scope for the MVP.

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
