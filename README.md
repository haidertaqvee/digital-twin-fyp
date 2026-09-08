# TerraTwin — AI-Driven Semantic Digital Twins for Autonomous Systems Simulation

**FYP** — BS Space Science, Institute of Space Technology · Dr. Sajid Ghuffar
**Hackathon** — AI Builders Hackathon (Devpost), deadline **Sept 15, 2026**
**Goal** — satellite imagery → AI building-footprint segmentation → vectorized 3D → **Unity URP** demo neighborhood.

## Pipeline

1. **Stage 1 — Segmentation** (`src/stage1_extraction/`) — SpaceNet-trained `smp.Unet` (ResNet34, BCE+Dice)
2. **Stage 2 — Vectorization + heights** (next) — masks → georeferenced polygons, building-height heuristic
3. **Stage 3 — Extrusion** — 2D polygons → 3D meshes
4. **Stage 4 — Unity** — `heightmap.png` + `landcover.png` drive procedural terrain + building population (Unity URP)

The on-disk `src/stage1..5_*` layout uses the original 5-stage FYP numbering
(`stage4_change_detection` / `stage5_simulation` pre-date the TerraTwin scope);
for TerraTwin the target is Unity, not Isaac Sim / Gazebo.

## Getting started

```powershell
conda env create -f environment.yml              # or: pip install -r requirements.txt
conda activate E:\digital-twin-fyp\envs\digital-twin

# data pipeline (once)
python src/stage1_extraction/build_subset.py     # sample 999 tiles, split 70/15/15
python src/stage1_extraction/build_masks.py      # rasterize geojson → PNG masks
python src/stage1_extraction/dataset.py          # smoke-test dataloader

# smoke test (CPU) + local GPU run
python src/stage1_extraction/train_unet.py --help
python src/stage1_extraction/train_unet.py --epochs 1 --limit 4   # needs CUDA
python src/stage1_extraction/train_unet.py --epochs 15 --batch-size 8
```

See [docs/FYP_Proposal.md](docs/FYP_Proposal.md) for the full project proposal —
methodology, objectives, data & environment, evaluation plan, risks, timeline,
and the long-term roadmap (Isaac Sim / Gazebo / Sat-NeRF are post-MVP future
work, not on the Sept 15 critical path). See [CONTEXT.md](CONTEXT.md) for
operating notes and strict rules (Unity-only MVP).
