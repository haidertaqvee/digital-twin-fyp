# Thesis Architecture & Research Pipeline Specification

**Degree:** BS Space Science  
**Department:** Space Science, Institute of Space Technology (IST), Islamabad  
**Thesis Title:** *Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin*  
**Authors / Team:** Haider Taqveen (Reg. No. 230601020), Mashaf Majeed (Reg. No. 230601017)  
**Supervisor:** Dr. Munawar Ali Shah  

---

## 1. System Overview

This repository implements an end-to-end framework for autonomous UAV swarm navigation operating within high-fidelity geospatial digital twins reconstructed from Earth observation data:

```
[Satellite Optical Imagery (SpaceNet 2)]
                  │
                  ▼
[1. Deep Semantic Segmentation (U-Net)] ──► Building Footprint Probability Maps
                  │
                  ▼
[2. Vectorization & Attribute Enrichment] ──► Georeferenced Polygons & Estimated Heights
                  │
                  ▼
[3. 3D Digital Twin Mesh Reconstruction] ──► 3D Obstacles + AWS Terrarium DEM Terrain
                  │
                  ▼
[4. Multi-Agent Reinforcement Learning] ──► Swarm Cooperative Trajectory & Collision Avoidance
```

---

## 2. Directory Hierarchy

The repository adheres strictly to the academic data science standard:

```
digital-twin-fyp/
├── data/
│   ├── raw/                      # SpaceNet 2 Vegas raw satellite imagery & vectors
│   ├── interim/                  # Intermediate processed tensors & resampled rasters
│   └── processed/                # Normalized train/val/test splits, 3D meshes & exports
│       ├── stage3_3d/            # OBJ/MTL extruded building meshes
│       ├── test/                 # Test images, masks, vectors, predictions
│       ├── train/                # Train images, masks, labels
│       ├── unity_export/         # Unity URP 16-bit heightmaps & landcover masks
│       └── val/                  # Val images, masks, labels
├── docs/
│   ├── FYP_Proposal.md           # Formal academic thesis proposal
│   ├── PRETRAINED_BASELINE.md    # Baseline model evaluation report
│   └── THESIS_ARCHITECTURE.md    # System design & MADRL pipeline specification
├── notebooks/                    # Jupyter notebooks for exploratory data analysis
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
│   │   ├── dem.py                # AWS Terrarium DEM elevation query engine
│   │   ├── heights.py            # Geometric building height heuristic
│   │   └── extrude_3d.py         # 3D polygon to Wavefront OBJ extrusion
│   └── physics_sim/              # Simulation environment generation & dynamics
│       └── export_unity.py       # 16-bit terrain heightmap & landcover exporter
├── models/                       # Model weights and training history
│   ├── unet_resnet34_best.pth    # Fine-tuned U-Net weights (Test IoU: 0.8062)
│   └── unet_resnet34_history.json
├── results/                      # Quantitative evaluation reports and logs
├── terratwin_sos_archive/        # Isolated legacy hackathon assets & web server
├── run_sos_dashboards.bat        # Single-click launcher for archived dashboards
├── environment.yml
└── requirements.txt
```

---

## 3. Core Modules & Usage

### 3.1 Data Preparation & Semantic Segmentation
- **Dataset Verification:**
  ```powershell
  python src/data_prep/verify_stage1.py --tiles 5 --tolerance 4
  ```
- **Polygon Vectorization Benchmark:**
  ```powershell
  python src/data_prep/verify_stage2.py --tiles 5 --source predictions
  ```
- **Model Training:**
  ```powershell
  python src/models/train_unet.py --epochs 15 --batch-size 8
  ```

### 3.2 3D Digital Twin Geometry
- **Building Mesh Extrusion:**
  ```powershell
  python src/geometry/extrude_3d.py --tile AOI_2_Vegas_img4174
  ```
- **Unity URP Simulation Terrain Export:**
  ```powershell
  python src/physics_sim/export_unity.py --tile AOI_2_Vegas_img4174
  ```

### 3.3 Archived Hackathon Dashboards
To launch the legacy TerraTwin SOS web dashboards:
Double-click `run_sos_dashboards.bat` from the root directory or run:
```powershell
.\run_sos_dashboards.bat
```
