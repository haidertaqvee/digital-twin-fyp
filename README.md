# Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin

**Department of Space Science, Institute of Space Technology (IST), Islamabad**  
**Authors / Team:** Haider Taqveen (Reg. No. 230601020), Mashaf Majeed (Reg. No. 230601017)  
**Supervisor:** Dr. Munawar Ali Shah  

---

## 🛰️ Project Overview

This repository hosts the official research codebase for the BS Space Science Final Year Project (FYP). The thesis develops an automated, end-to-end framework that converts high-resolution optical satellite imagery into geometrically faithful, simulation-ready 3D digital twins, providing the real-world operational environment for **Multi-Agent Deep Reinforcement Learning (MADRL)** autonomous UAV swarm navigation, target search, and collision avoidance.

### Research Workflow

```
[Raw Optical Satellite Imagery (SpaceNet 2)]
                    │
                    ▼
[Stage 1: Deep Semantic Segmentation (U-Net ResNet-34)]  ──► Test IoU: 0.8062 | F1: 0.8927
                    │
                    ▼
[Stage 2: Footprint Vectorization & Height Attribution] ──► Round-trip IoU: 0.994
                    │
                    ▼
[Stage 3: 3D Digital Twin Obstacle & Terrain Reconstruction] ──► AWS Terrarium DEM + OBJ Meshes
                    │
                    ▼
[Stage 4: Multi-Agent Deep Reinforcement Learning Simulation] ──► Cooperative Swarm Path Planning
```

---

## 📁 Academic Repository Architecture

The repository enforces a strict academic data science hierarchy:

```
digital-twin-fyp/
├── data/
│   ├── raw/                      # Raw SpaceNet 2 Las Vegas imagery & geojson labels
│   ├── interim/                  # Intermediate cached tensors & transformed rasters
│   └── processed/                # Normalized train/val/test splits, 3D meshes & exports
│       ├── stage3_3d/            # 3D building meshes (.obj / .mtl)
│       ├── test/                 # Test images, masks, vectors, predictions
│       ├── train/                # Train images, masks, labels
│       ├── unity_export/         # Unity URP 16-bit heightmaps & landcover masks
│       └── val/                  # Validation split
├── docs/
│   ├── FYP_Proposal.md           # Formal academic thesis proposal
│   ├── PRETRAINED_BASELINE.md    # Pretrained baseline evaluation report
│   └── THESIS_ARCHITECTURE.md    # Detailed architecture & simulation pipeline specification
├── notebooks/                    # Jupyter notebooks for EDA and swarm experiments
│   └── 01_dataset_exploration.ipynb
├── src/
│   ├── data_prep/                # Footprint rasterization, dataset splitting & vectorization
│   │   ├── build_masks.py
│   │   ├── build_subset.py
│   │   ├── dataset.py
│   │   ├── vectorize.py
│   │   ├── verify_alignment.py
│   │   ├── verify_masks.py
│   │   ├── verify_stage1.py
│   │   └── verify_stage2.py
│   ├── models/                   # Neural network architectures, training & evaluation
│   │   ├── evaluate.py
│   │   ├── inference.py
│   │   ├── model.py
│   │   ├── predict_pretrained.py
│   │   ├── train.py
│   │   └── train_unet.py
│   ├── geometry/                 # 3D spatial geometry & digital elevation models
│   │   ├── dem.py                # AWS Terrarium DEM elevation sampling engine
│   │   ├── heights.py            # Geometric building height heuristic
│   │   └── extrude_3d.py         # 3D polygon to Wavefront OBJ extrusion
│   └── physics_sim/              # Simulation environment generation & UAV dynamics
│       └── export_unity.py       # 16-bit terrain heightmap & landcover exporter
├── models/                       # Checkpoints & training logs
│   ├── unet_resnet34_best.pth    # Fine-tuned U-Net weights
│   └── unet_resnet34_history.json
├── results/                      # Quantitative evaluation reports and logs
├── terratwin_sos_archive/        # Isolated legacy hackathon assets & web server
├── run_sos_dashboards.bat        # Single-click launcher for archived SOS dashboards
├── environment.yml
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. Environment Setup

Activate the project's dedicated Conda environment:
```powershell
conda activate digital-twin
# or directly invoke: .\envs\digital-twin\python.exe
```

### 2. Verify Pipeline Stages

- **Verify Stage 1 Dataset Alignment & Reproducibility:**
  ```powershell
  python src/data_prep/verify_stage1.py --tiles 5 --tolerance 4
  ```

- **Verify Stage 2 Footprint Vectorization:**
  ```powershell
  python src/data_prep/verify_stage2.py --tiles 5 --source predictions
  ```

- **Run 3D Digital Twin Mesh Extrusion:**
  ```powershell
  python src/geometry/extrude_3d.py --tile AOI_2_Vegas_img4174
  ```

- **Export Unity URP Simulation Heightmap:**
  ```powershell
  python src/physics_sim/export_unity.py --tile AOI_2_Vegas_img4174
  ```

---

## 🏛️ Legacy Hackathon Project (TerraTwin SOS)

All assets, FastAPI backend code, client dashboards, and disaster hazard simulation engines from the AI Builders Hackathon 2026 submission have been cleanly isolated in `terratwin_sos_archive/` with zero cross-contamination.

To launch and explore the legacy dashboards:
1. Double-click **`run_sos_dashboards.bat`** in the repository root (or execute `.\run_sos_dashboards.bat` in PowerShell).
2. The script will automatically activate the Python environment and launch:
   - **3D Twin Explorer:** `http://localhost:8000/index.html`
   - **Citizen SOS Beacon:** `http://localhost:8000/sos.html`
   - **Rescuer Tactical HUD:** `http://localhost:8000/receiver.html`
