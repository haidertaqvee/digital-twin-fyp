# Digital Twin FYP — Antigravity Workspace Environment

## 1. Project Overview
**BS Space Science Final Year Project Thesis**
- **Thesis Title:** Multi-Agent Deep Reinforcement Learning for UAV Swarm Navigation in a Geospatial Digital Twin
- **Authors / Team:**
  - Haider Taqveen (Reg. No. 230601020)
  - Mashaf Majeed (Reg. No. 230601017)
- **Supervisor:** Dr. Munawar Ali Shah
- **Institution:** Institute of Space Technology (IST), Islamabad
- **Core Pipeline:**
  1. Satellite semantic feature extraction & instance segmentation (`src/data_prep/`, `src/models/`)
  2. 3D digital twin mesh reconstruction & DEM ground elevation (`src/geometry/`)
  3. Real-time physics simulation & Unity URP export (`src/physics_sim/`)
  4. Multi-agent reinforcement learning (MADRL) for cooperative UAV swarm navigation

## 2. Antigravity Environment Setup
- **Python Environment:** `E:\digital-twin-fyp\envs\digital-twin\python.exe`
- **Working Directory:** `E:\digital-twin-fyp`
- **Archived SOS Launcher:** `.\run_sos_dashboards.bat`

## 3. Strict Academic Architecture
- `data/` (`raw/`, `interim/`, `processed/`)
- `docs/` (`FYP_Proposal.md`, `PRETRAINED_BASELINE.md`, `THESIS_ARCHITECTURE.md`)
- `src/` (`data_prep/`, `models/`, `geometry/`, `physics_sim/`)
- `notebooks/` (Exploratory analysis and swarm experiments)
- `terratwin_sos_archive/` (Isolated read-only legacy hackathon dashboards)

## 4. Coding & Architecture Guidelines
- Preserve modularity: All data preparation logic belongs in `src/data_prep/`, model training in `src/models/`, 3D geometry in `src/geometry/`, and simulation dynamics in `src/physics_sim/`.
- Maintain absolute separation from `terratwin_sos_archive/` — no code in `src/` should import from or depend on `terratwin_sos_archive/`.
- Ensure high geographic precision: DEM ground elevation queries must account for datum offsets and exact geographic bounding coordinates.
