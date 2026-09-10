# AI-Driven Semantic Digital Twins for Autonomous Systems Simulation

### FYP Proposal — BS Space Science, Institute of Space Technology
**Student:** TerraTwin (solo submission) · **Supervisor:** Dr. Sajid Ghuffar  
**Date:** 10 September 2026 · **Version:** 1.1 — revised after Stages 1–2 were implemented and measured  
**Repository:** `E:\digital-twin-fyp` · **Pipeline code:** `src/stage1_extraction/`, `src/stage2_enrichment/`

> **Note on dual context.** This proposal is written for the FYP examination. The same codebase is entered as a solo student submission to the **AI Builders Hackathon on Devpost** (deadline 15 September 2026, 11:00 PM EDT). The hackathon serves as an external milestone for completing the Stage 1–4 MVP; it does not alter the academic scope or evaluation criteria. The hackathon is not discussed further except where it constrains the MVP timeline.

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Introduction & Problem Statement](#2-introduction--problem-statement)
3. [Aims & Objectives](#3-aims--objectives)
4. [Literature & Related Work](#4-literature--related-work)
5. [System Overview & Pipeline Architecture](#5-system-overview--pipeline-architecture)
6. [Stage 1 — Semantic Feature Extraction](#6-stage-1--semantic-feature-extraction-building-footprint-segmentation)
7. [Stage 2 — Attribute Enrichment](#7-stage-2--attribute-enrichment-vectorization--height-estimation)
8. [Stage 3 — 3D Reconstruction](#8-stage-3--3d-reconstruction-mesh-extrusion--export)
9. [Stage 4 — Unity Integration & Simulation Environment](#9-stage-4--unity-integration--simulation-environment)
10. [Data & Environment](#10-data--environment)
11. [Evaluation Plan](#11-evaluation-plan)
12. [Risks, Limitations & Mitigations](#12-risks-limitations--mitigations)
13. [Work Plan & Timeline](#13-work-plan--timeline)
14. [Long-Term Roadmap (Post-MVP — Out of Scope)](#14-long-term-roadmap-post-mvp--out-of-scope)
15. [Expected Contributions & Deliverables](#15-expected-contributions--deliverables)
16. [Ethical Considerations](#16-ethical-considerations)
17. [References](#17-references)
18. [Appendices](#appendices)

---

## 1. Abstract

Autonomous systems — ground robots, delivery drones, and urban air mobility platforms — require high-fidelity, semantically rich simulation environments for safe development and testing. Manually modelling cities is slow and does not scale; existing procedural tools lack grounding in real-world geography. **TerraTwin** addresses this gap by building an automated pipeline that converts high-resolution optical satellite imagery into simulation-ready 3D environments, bridging remote sensing/GIS and game-engine-based simulation.

The pipeline has four MVP stages: (1) deep-learning-based building-footprint segmentation from SpaceNet imagery, (2) vectorization of masks to georeferenced polygons with height attribution, (3) extrusion to 3D meshes, and (4) integration into a Unity URP scene via heightmap and land-cover textures that drive procedural terrain and building placement. The MVP is evaluated on SpaceNet 2 (Las Vegas) with quantitative segmentation metrics (IoU, F1) and a qualitative Unity demo neighbourhood. Longer-term extensions — temporal change detection, photorealistic neural rendering (Sat-NeRF), and Isaac Sim / Gazebo / ROS integration — are scoped as post-MVP future work.

**Stages 1 and 2 are now implemented and measured, not merely designed.** The Stage 1 segmentation model was trained on a single local GPU (GTX 1660 Super, 6 GB) and reaches **0.8062 IoU / 0.8927 F1 on the held-out test split** (146 tiles, never used for model selection), exceeding the O1 target of IoU ≥ 0.60 by a wide margin. Stage 2 vectorization is implemented and **round-trip validated against the original SpaceNet labels at IoU 0.992–0.996**, exceeding the O2 target. Applied to the model's own predictions, it yields 3,621 georeferenced building polygons across 140 of 146 test tiles with heights attached by a documented heuristic. The remaining MVP work is Stage 3 (extrusion to mesh/glTF) and Stage 4 (Unity URP demo neighbourhood). The AMD Developer Cloud path was **not needed** and remains an untested fallback.

---

## 2. Introduction & Problem Statement

### 2.1 Motivation

Simulation is to autonomy what a wind tunnel is to aerodynamics: the place where failure is cheap. Yet the environments in which we simulate autonomous behaviour are often the weakest link. Hand-modelled urban scenes are labour-intensive, quickly outdated, and rarely geographically faithful. Procedural city generators produce plausible geometry but without semantic correspondence to any real place on Earth, limiting their utility for mission rehearsal, geospatial planning, and sim-to-real transfer.

Satellite imagery, by contrast, is abundant, current, and globally available at sub-metre resolution. If the semantic content of that imagery — *where are the buildings, how large are they, how are they arranged?* — can be extracted automatically and lifted into 3D, then any imaged neighbourhood can become a simulation environment on demand.

### 2.2 Problem Statement

There is no open, reproducible, end-to-end pipeline that:

- takes raw high-resolution satellite imagery as input,
- extracts dense semantic features (building footprints) with quantified accuracy,
- enriches those features with geometric attributes (height, footprint regularity),
- reconstructs simulation-grade 3D geometry, and
- delivers that geometry into a real-time engine where autonomous agents can be exercised.

Existing efforts solve isolated fragments — segmentation benchmarks, 3D reconstruction demos, or hand-crafted simulation maps — but do not connect them into a single automated chain grounded in real geography.

### 2.3 Research Questions

1. How accurately can building footprints be segmented from 30–50 cm RGB-PanSharpen imagery using a compact, transfer-learned segmentation model trained on a modest (sub-1k tile) subset?
2. What is the minimum geometric enrichment (footprint polygon + height estimate) required to produce a Unity environment that is both visually convincing and useful for basic autonomous navigation tasks?
3. Can the pipeline be made sufficiently automated and reproducible that a new geographic tile can be processed end-to-end without manual modelling?

---

## 3. Aims & Objectives

### 3.1 Aim

To design, implement, and evaluate **TerraTwin**, an AI-driven pipeline that automates the conversion of high-resolution satellite imagery into semantically accurate, simulation-ready 3D environments.

### 3.2 Objectives

| # | Objective | Maps to | Success criterion | Status (10 Sep 2026) |
|---|-----------|---------|-------------------|----------------------|
| O1 | Build a reproducible building-footprint segmentation model from SpaceNet 2 imagery | Stage 1 | Val IoU ≥ 0.60, F1 ≥ 0.70 on held-out split; full training completes on MI300X | **MET and exceeded** — val IoU 0.8040 / F1 0.8913; **test IoU 0.8062 / F1 0.8927**. Trained locally on the GTX 1660 Super; the MI300X path was not required (see §10.2). |
| O2 | Vectorize predicted masks to georeferenced polygons and assign per-building heights | Stage 2 | ≥ 95% of predicted masks produce valid, CRS-consistent polygons; heights within a defensible heuristic or learned range | **MET** — 140/146 test tiles produced polygons (the 6 empty tiles legitimately contain no buildings); **0 null and 0 invalid geometries**, CRS-consistent in EPSG:4326; round-trip IoU 0.992–0.996 vs source labels. Heights via documented heuristic (§7.3). |
| O3 | Extrude polygons to watertight 3D meshes and export in an engine-agnostic format | Stage 3 | Meshes import into Unity without manual repair; per-building mesh validity ≥ 98% | **Not started** — on the critical path. |
| O4 | Integrate geometry into a Unity URP scene driven by `heightmap.png` + `landcover.png` | Stage 4 | Walkable / flyable demo neighbourhood; Unity accepts 513×513 heightmap and RGB land-cover without resampling artefacts | **Not started** — no Unity project exists yet. |
| O5 | Evaluate end-to-end and document for FYP examination and reproducibility | All | Proposal, codebase, trained weights, and demo are examinable and rerunnable from documented steps | **Partial** — Stages 1–2 documented and rerunnable; dependency manifests re-frozen to the versions that actually produced the results. |

---

## 4. Literature & Related Work

### 4.1 Building Footprint Segmentation

SpaceNet (CosmiQ Works / DigitalGlobe) remains the reference benchmark for building extraction from overhead imagery. Early SpaceNet baselines used vanilla U-Nets; subsequent winners introduced ensembles, polyline-aware losses, and orientation-aware heads. The U-Net (Ronneberger et al., 2015) with an ImageNet-pretrained encoder remains the strongest *small-data* baseline — directly relevant here, where the training set is ~673 tiles. `segmentation_models_pytorch` (Yakubovskiy, 2020) packages this pattern cleanly (ResNet-34 encoder, BCE+Dice loss), which is the choice adopted for TerraTwin's primary training script (`train_unet.py`). A from-scratch U-Net (`model.py` + `train.py`) is retained as a fallback and for ablation.

### 4.2 From Masks to Vector Geometry

Raster-to-vector conversion is well-trodden in GIS (rasterio / GDAL polygonize, shapely simplification). The challenge is not polygonization itself but maintaining CRS fidelity and handling noisy predictions (holes, fragmented footprints). Prior work shows that morphological post-processing (closing, area filtering) materially improves polygon regularity before extrusion.

### 4.3 3D Reconstruction & Digital Twins

City-scale digital twins have been pursued via LiDAR-driven extrusion, photogrammetric mesh reconstruction, and more recently neural rendering (NeRF, 3D Gaussian Splatting). Sat-NeRF (Marí et al., 2022; vendored in `satnerf/`) is relevant as a future photorealistic path but is explicitly out of MVP scope — it requires multi-view RPC imagery and bundle adjustment (`sat-bundleadjust/`), which the current single-image-per-tile dataset does not support.

**This constraint was verified empirically rather than assumed (10 September 2026), and the evidence is recorded in §12.1 because it determines what the MVP can claim.** Across all 999 sampled tiles there are **999 distinct ground footprints and no overlapping coverage** — no ground area is observed twice. No RPC camera model is present in any tile (no `.rpc` sidecar files in `data/raw/`, no `rpc` GeoTIFF tag, no GCPs). `satnerf/create_satellite_dataset.py` requires `rpcm.rpc_from_geotiff()` per image, so the vendored pipeline cannot ingest this dataset at all. Recent single-view 3DGS methods (SVG3D, MonoSplat; shadow-aware splatting for multi-view satellite) reconstruct from one image only by invoking diffusion or monocular-depth priors — that is, they *hallucinate* vertical structure — and remain an active research frontier rather than a deliverable engineering step. Presenting such output as a reconstruction of Las Vegas would misrepresent the result, so it is deferred to §14 with an explicit statement of what data it would require.

### 4.4 Simulation Integration

Gazebo and Isaac Sim are the dominant simulators for robotics autonomy, both supporting USD/SDF import. Unity URP is chosen for the MVP because it offers the fastest path to a polished, demonstrable neighbourhood with procedural terrain tooling, and because the project's GIS-to-graphics bridge is more clearly demonstrated in a game engine than in a robotics simulator. Migration to Isaac Sim / Gazebo is reserved for the long-term roadmap.

### 4.5 Gap

No open pipeline connects all four MVP stages with a single geographic dataset, a documented normalization and tiling regime, and a reproducible training-to-Unity path. TerraTwin's contribution is that integration, not a novel segmentation architecture.

---

## 5. System Overview & Pipeline Architecture

```
 SpaceNet SN2 (Las Vegas)                TerraTwin Pipeline                     Outputs
 ─────────────────────────        ──────────────────────────────────        ────────────────
 Raw tiles (RGB-PanSharpen        Stage 1  Segmentation (U-Net)              Masks (PNG)
  + GeoJSON footprints)    ───►   Stage 2  Vectorize + height attribution    Polygons (GeoJSON/SHP)
         │                       Stage 3  Extrude + mesh export              Meshes (OBJ/FBX/glTF)
         │                       Stage 4  Unity URP terrain + population     heightmap.png
         │                                                                + landcover.png
         └────────────────────►  Demo neighbourhood (Unity)  ◄────────────  + building prefabs
```

**Repository layout** (`src/stage{1..5}_*` mirrors the pipeline):

- `stage1_extraction` — **implemented, trained, and evaluated** (see §6)
- `stage2_enrichment` — **implemented and verified** (see §7)
- `stage3_reconstruction` — **not started** (on the critical path)
- `stage4_change_detection` / `stage5_simulation` — **empty scaffolds** that become the Unity MVP

**Design principles:**

- *Automation over manual modelling.* Every stage consumes the previous stage's file output; no hand-editing of geometry.
- *Reproducibility.* Fixed random seed (42) for subset/split, fixed `NORM_MAX`, deterministic CRS handling.
- *Graceful degradation.* Each stage validates its inputs and skips corrupt tiles rather than failing the batch.
- *Engine-agnostic intermediate formats* (GeoJSON, OBJ/glTF) so the Unity choice does not lock out future simulators.

---

## 6. Stage 1 — Semantic Feature Extraction (Building Footprint Segmentation)

> **Status: COMPLETE — trained and evaluated. Test IoU 0.8062 / F1 0.8927 on 146 held-out tiles.**

### 6.1 Data Preparation

| Step | Script | Input | Output | Key decision |
|------|--------|-------|--------|--------------|
| Subset & split | `build_subset.py` | `data/raw/AOI_2_Vegas_Train/` | `data/processed/{train,val,test}/{images,labels}` | 999 tiles, seed 42, 70/15/15 |
| Mask rasterization | `build_masks.py` | images + GeoJSON | `…/masks/mask_*.png` (0/255) | Skip tiles with >15% no-data; reproject geometries to image CRS |
| Normalization ceiling | `check_pixel_stats` | 100-tile sample | `NORM_MAX = 1910.0` | 95th percentile of per-tile maxima; dataset-wide, not per-image |
| Dataloader | `dataset.py` | images + masks | `SpaceNetDataset` (PyTorch) | Fixed `/1910.0` scaling; lists `masks/` as source of truth; optional 512-px crops + flips/rot90 |

**Verification performed:** `verify_masks.py` (mask coverage), `verify_alignment.py` / `check_rotation.py` (CRS and orientation), `visualize_sample.py` / `visualize_samples_grid.py` (qualitative checks, outputs in `notebooks/`). Raster CRS matches GeoJSON CRS after reprojection.

**Filename contract** (must stay in lockstep; scripts use string `.replace()`):

- Image: `RGB-PanSharpen_AOI_2_Vegas_img{N}.tif`
- Label: `buildings_AOI_2_Vegas_img{N}.geojson`
- Mask: `mask_AOI_2_Vegas_img{N}.png`

### 6.2 Model

**Primary:** `train_unet.py` — `segmentation_models_pytorch` U-Net, ResNet-34 encoder, ImageNet weights, 3-channel input, 1-class logit output, BCEWithLogits + soft Dice compound loss, AdamW (lr 1e-4, wd 1e-4), 512-px crops, batch 8, augmentation (flips + 90° rotations — valid for nadir imagery).

**Fallback / ablation:** `model.py` + `train.py` — from-scratch U-Net (DoubleConv / Down / Up blocks, bilinear upsampling, padding for odd 650-px tiles), same loss, AMP + resume + ReduceLROnPlateau. Retained for comparison and for environments where `smp` is unavailable.

Both scripts share `SpaceNetDataset` and the fixed `NORM_MAX` regime. Normalization is intentionally *not* per-image: per-image stretching would give the same rooftop different brightnesses across tiles, harming generalization.

### 6.3 Training Regime

- **Smoke test (local, CPU):** `python src/stage1_extraction/train_unet.py --epochs 1 --limit 4` — verified.
- **Full run:** `python src/stage1_extraction/train_unet.py --epochs 15` — ~1–1.5 h on GTX 1660 Super (batch 8, 6 GB VRAM) or faster on MI300X. Checkpoint: `models/unet_resnet34_best.pth` (best val IoU).
- **Deployment to AMD Developer Cloud:** bundle with `tar -czf terratwin_deployment.tar.gz src data/processed`, SCP to instance, extract, run. Scripts accept `--data-dir` / `--ckpt-dir` so cloud paths need no code edits.

### 6.4 Outputs

Binary masks (0/1, threshold 0.5) at tile resolution, plus training curves and best checkpoint for downstream stages.

---

## 7. Stage 2 — Attribute Enrichment (Vectorization & Height Estimation)

> **Status: Scaffolded. Design finalized; implementation follows Stage 1 training.**

1. **Polygonization.** Raster masks → polygons via `rasterio.features.shapes` / GDAL polygonize, filtered by minimum area, simplified (Douglas-Peucker), and written as GeoJSON/Shapefile in the source CRS.
2. **Regularization.** Orthogonalize near-right angles, remove spurious holes — improves extrusion quality.
3. **Height attribution.** MVP heuristic: per-building height sampled from a plausible distribution conditioned on footprint area (e.g., small residential vs. large commercial), clamped to a defensible range. Documented as a heuristic; a learned height head is future work. Heights stored as a polygon attribute.
4. **Validation.** CRS round-trip check, polygon validity (`is_valid`), and overlay against source imagery for a sample of tiles.

*Tools:* Rasterio, GeoPandas, Shapely. No new training required for the MVP heuristic.

---

## 8. Stage 3 — 3D Reconstruction (Mesh Extrusion & Export)

> **Status: Scaffolded.**

1. **Extrusion.** Each polygon extruded to a prismatic mesh of its attributed height. Footprint triangulation via earcut; vertical walls generated from boundary edges.
2. **UVs & materials.** Simple planar UVs; placeholder PBR material (roof vs. wall) sufficient for the demo. Photorealistic texturing is future work.
3. **Export.** Engine-agnostic formats (OBJ + MTL, glTF/FBX) with a manifest mapping mesh → georeferenced origin. Meshes kept watertight and manifold for simulator import.
4. **Validation.** Automated checks: manifoldness, non-zero volume, import test into Unity.

*Note on `satnerf/` and `sat-bundleadjust/`.* These vendored upstream clones are **not** part of the MVP. They are retained as reference for the long-term neural-rendering roadmap and should be treated as third-party code with their own environments.

---

## 9. Stage 4 — Unity Integration & Simulation Environment

> **Status: Scaffolded to accept pipeline products. Demo neighbourhood is the MVP deliverable.**

1. **Terrain.** `heightmap.png` (513×513, grayscale, Unity Terrain heightmap convention) and `landcover.png` (RGB, semantic colour per class) drive procedural terrain generation and texturing. Both are produced from the processed tiles / DEM alignment step.
2. **Building population.** Imported meshes placed at georeferenced positions; batching / instancing for performance.
3. **Scene.** Unity URP template, walkable / flyable first-person or drone-like controller, basic lighting and occlusion culling. No autonomy stack is required for the MVP — the contribution is the *environment*, not the agent.
4. **Deliverable.** A standalone Unity build + editor project demonstrating a contiguous neighbourhood (on the order of dozens to low hundreds of buildings) that is recognizably the source geography.

---

## 10. Data & Environment

### 10.1 Dataset

- **Source:** SpaceNet 2 — Buildings in Las Vegas (`AOI_2_Vegas`), AWS Open Data. Chosen for its permissive licence, sub-metre resolution, and building-only focus (cleaner than multi-class land-cover datasets for this task).
- **Working subset:** 999 tiles sampled with seed 42, split 70/15/15 (train/val/test) by `build_subset.py`.
- **Valid training masks:** 673 after no-data filtering and rasterization — the effective training set size.
- **Licence & attribution:** SpaceNet data used under its original licence; attribution retained in documentation and demo credits.
- **Raw data location:** `data/raw/` (gitignored; not present in a fresh clone).

### 10.2 Compute

| Environment | Purpose | Spec |
|-------------|---------|------|
| Local (Windows, E: drive) | Development, smoke tests, visualization | Conda env `envs/digital-twin` (Python 3.10, torch 2.13, torchvision 0.28, rasterio 1.4, geopandas 1.1), GTX 1660 Super 6 GB |
| AMD Developer Cloud (MI300X) | Full training | ROCm via `torch.cuda` (same code path as CUDA); `--num-workers` raised on Linux |

The conda environment is checked into the repo at `envs/digital-twin/` and activated with `conda activate E:\digital-twin-fyp\envs\digital-twin`. All stage-1 scripts hardcode `E:/digital-twin-fyp/...` absolute paths — they run from any CWD but only on this layout. Cloud runs override via CLI flags.

### 10.3 Reproducibility

Fixed seed, fixed `NORM_MAX`, deterministic CRS reprojection, and version-pinned dependencies. The deployment bundle is `src` + `data/processed` only; raw data and `models/` are excluded.

---

## 11. Evaluation Plan

### 11.1 Quantitative (Stage 1)

- **Primary metrics:** Intersection over Union (IoU) and F1/Dice on the held-out val and test splits, computed with a global confusion accumulator (not per-image averaging, which is skewed by sparse tiles).
- **Targets:** Val IoU ≥ 0.60, F1 ≥ 0.70 — competitive for a 673-tile, single-city, compact-model regime; reported with precision/recall.
- **Ablations:** `train_unet.py` (pretrained ResNet-34) vs. `train.py` (from-scratch U-Net); with/without augmentation; 512-px crops vs. full 650-px tiles.
- **Curves:** Train/val loss and IoU per epoch; best checkpoint retained.

### 11.2 Qualitative (Stages 2–4)

- Visual overlay of predicted masks / polygons on source imagery (sample tiles in `notebooks/`).
- Mesh validity and import success rate.
- Unity demo walkthrough — geographic fidelity judged by side-by-side satellite vs. scene screenshots.

### 11.3 Failure Analysis

Document systematic failure modes: small / dense buildings, shadow-adjacent footprints, no-data border artefacts, and height-heuristic errors. These directly motivate future work.

---

## 12. Risks, Limitations & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Overfitting on 673 tiles / single city (Las Vegas) | Poor generalization | Transfer learning (ImageNet encoder), aggressive augmentation (flips/rot90), 512-px crops for more steps/epoch; report generalization limits honestly |
| Cloud training disruption (session drop, quota) | Lost time | `train.py` writes `last.pt` every epoch with `--resume`; `train_unet.py` saves best checkpoint; bundle is small and redeployable via SCP |
| Hardcoded absolute paths break on cloud | Scripts fail to find data | Both training scripts accept `--data-dir` / `--ckpt-dir`; update constants together if layout moves |
| Height heuristic is crude | Unrealistic skyline | Documented as MVP heuristic; demo scoped to flat-roof, low-rise neighbourhoods where error is least visible |
| Sat-NeRF / multi-view data not available | Photorealism goal unmet | Explicitly out of MVP scope; single-image pipeline is the evaluated contribution |
| Unity terrain resolution mismatch | Artefacts at tile seams | Fixed 513×513 heightmap convention; validate import before demo capture |

**Known limitations to state in the final report:** single-city, RGB-only (no multispectral / DSM), no temporal dimension, heuristic heights, and no closed-loop autonomy evaluation in the MVP.

---

## 13. Work Plan & Timeline

*Proposal date: 8 September 2026. Hard external milestone: 15 September 2026 (hackathon submission). FYP examination follows on the academic calendar.*

| Window | Milestone | Exit criterion |
|--------|-----------|----------------|
| **8–9 Sep** | Deploy to AMD MI300X and complete Stage 1 training | `models/unet_resnet34_best.pth` exists; val IoU/F1 logged; training curves saved |
| **9–11 Sep** | Stages 2–3: vectorize, attribute heights, extrude meshes | Polygon GeoJSON + mesh exports for ≥ 1 demo neighbourhood; validity checks pass |
| **11–13 Sep** | Stage 4: Unity integration + demo capture | Playable URP scene; screenshots / short video for submission |
| **13–15 Sep** | Submission polish: documentation, reproducibility notes, demo build | Hackathon submission + FYP progress artefacts ready |
| **Post-15 Sep** | FYP write-up, expanded evaluation, failure analysis, viva preparation | Final report and presentation |

The 15 September date is treated as an MVP freeze, not a project end. Work after that refines evaluation and writing for the academic examination.

---

## 14. Long-Term Roadmap (Post-MVP — Out of Scope)

> **This section is explicitly not part of the MVP, not on the 15 September critical path, and not evaluated for the hackathon submission.** It is included to show the academic trajectory of the work and to justify retaining `satnerf/` and `sat-bundleadjust/` in the repository.

**Stage 5 — Simulation integration (Isaac Sim / Gazebo / ROS).** Export glTF/USD/SDF from Stage 3 into Isaac Sim and Gazebo; expose the environment via ROS topics so navigation and perception stacks can be exercised. Requires simulator-specific material and physics tuning.

**Photorealistic reconstruction (Sat-NeRF / Gaussian Splatting).** Leverage the vendored `satnerf/` and `sat-bundleadjust/` for multi-view, RPC-aware neural rendering where multi-date imagery is available. This replaces heuristic extrusion with view-consistent, textured geometry — a research-grade extension, not an MVP requirement.

**Temporal change detection (Stage 4 in the original five-stage plan).** Multi-date acquisitions over the same AOI, differencing predicted footprints/meshes to detect new construction, demolition, or land-cover change. Depends on acquiring a time series and on a stable Stage 1 model.

**Generalization.** Multi-city training (beyond Las Vegas), multispectral inputs (beyond RGB-PanSharpen), and DSM-conditioned height regression to replace the heuristic.

Each roadmap item is gated on a completed, evaluated MVP. The MVP's value does not depend on any of them.

---

## 15. Expected Contributions & Deliverables

**Academic contributions:**

- An open, reproducible pipeline connecting satellite imagery to simulation-ready 3D via documented data, code, and normalization choices.
- A quantified small-data segmentation baseline on SpaceNet 2 (Las Vegas) with ablations.
- A Unity demo that makes the GIS-to-simulation bridge concrete and examinable.

**Deliverables for examination:**

- This proposal (revised after supervisor feedback).
- Codebase (`src/`), training configuration, and best checkpoint.
- Processed dataset manifest and verification artefacts (`notebooks/`).
- Unity demo neighbourhood (editor project + build + capture).
- Final report and viva presentation.

---

## 16. Ethical Considerations

- **Privacy.** Sub-metre imagery can resolve individual structures. The demo uses publicly released SpaceNet imagery under its licence; no private or restricted imagery is used. No attempt is made to identify occupants or infer sensitive attributes.
- **Dual use.** High-fidelity geospatial twins have legitimate civilian uses (urban planning, disaster rehearsal) and potential misuse. The project does not develop or evaluate targeting, surveillance, or other harmful applications.
- **Environmental cost.** Training is kept modest (15 epochs, compact model) and cloud compute is used judiciously.
- **Attribution.** SpaceNet, `segmentation_models_pytorch`, and vendored upstream repos are credited; licences respected.

---

## 17. References

- Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. *MICCAI*.
- Yakubovskiy, P. (2020). Segmentation Models PyTorch. GitHub: `qubvel/segmentation_models.pytorch`.
- SpaceNet Dataset (CosmiQ Works / DigitalGlobe) — SpaceNet 2: Buildings in Las Vegas (AOI 2). AWS Open Data.
- Derksen, D., & Izzo, D. (2021). Shadow Neural Radiance Fields for Multi-view Satellite Photogrammetry. *CVPR Workshops* — Sat-NeRF.
- Centre Borelli — `satnerf` and `sat-bundleadjust` (vendored in `satnerf/`, `sat-bundleadjust/`).
- Unity Technologies — Universal Render Pipeline (URP) documentation.

*Additional references to be added as the literature review is expanded for the final report.*

---

## Appendices

### A. Deployment to AMD Developer Cloud (MI300X)

```powershell
# 1. Bundle (from E:\digital-twin-fyp, PowerShell)
tar -czf terratwin_deployment.tar.gz src data/processed

# 2. Copy to instance (replace <host> / <user>)
scp terratwin_deployment.tar.gz <user>@<host>:~/

# 3. On the instance (Linux)
tar -xzf terratwin_deployment.tar.gz
pip install segmentation_models_pytorch tqdm  # plus torch/rocm as per instance image

# 4. Train (paths may differ — override via flags, no code edit needed)
python src/stage1_extraction/train_unet.py --epochs 15 --batch-size 8 --num-workers 4

# 5. Retrieve checkpoint
scp <user>@<host>:~/models/unet_resnet34_best.pth E:/digital-twin-fyp/models/
```

`train.py` additionally supports `--resume` from `models/last.pt` for interrupted sessions.

### B. Key Scripts & Their Order

1. `build_subset.py` → 2. `build_masks.py` → 3. `dataset.py` (smoke test) → 4. `train_unet.py` (or `train.py`) → 5. Stages 2–4.

`check_pixel_stats` is a one-off (run `python src/stage1_extraction/check_pixel_stats` — no `.py` extension) that produced `NORM_MAX`.

### C. Glossary

| Term | Meaning |
|------|---------|
| AOI | Area of Interest (here, AOI 2 — Las Vegas) |
| CRS | Coordinate Reference System |
| DSM | Digital Surface Model |
| IoU | Intersection over Union |
| PanSharpen | Pansharpened imagery (pan + multispectral fusion) |
| RPC | Rational Polynomial Coefficients (satellite camera model) |
| URP | Universal Render Pipeline (Unity) |

---

*End of proposal — prepared 8 September 2026 for Dr. Sajid Ghuffar (IST). Feedback welcome; revision will be versioned in `docs/`.*
