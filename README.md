# TerraTwin SOS — 3D City Twin & Multi-Hazard Rescue Dispatch

**Automated satellite imagery pipeline → AI building footprint segmentation → vectorized 3D digital twin with generated addresses, live incident beacons, and tactical rescue navigation.**

- **Final Year Project (FYP):** BS Space Science, Institute of Space Technology (Supervised by Dr. Sajid Ghuffar)
- **Hackathon Submission:** AI Builders Hackathon (Devpost, Deadline: September 15, 2026)
- **Target Environments:** Web / Mobile (FastAPI + MapLibre GL 3D + PWA) & Simulation (Unity URP)

---

## Quick Start (One Command Run)

Launch the full stack (FastAPI backend + 3D Twin Explorer + Mobile SOS Beacon):

```powershell
# Using the project conda environment
E:\digital-twin-fyp\envs\digital-twin\python.exe src/server.py --port 8000
```

Open your browser:
- **3D Twin Explorer (Dispatcher Map):** [http://localhost:8000/demo/index.html](http://localhost:8000/demo/index.html)
- **Mobile SOS Beacon (Citizen PWA):** [http://localhost:8000/demo/sos.html](http://localhost:8000/demo/sos.html)
- **Rescuer Navigation HUD:** [http://localhost:8000/r/demo_fir_4ba1](http://localhost:8000/r/demo_fir_4ba1)

### Testing on a Mobile Phone (Same LAN or ngrok)

1. **Find your machine's LAN IP:**
   ```powershell
   ipconfig | findstr IPv4
   # Example: 192.168.1.50
   ```
2. **On your mobile phone browser:** Navigate to `http://192.168.1.50:8000/demo/sos.html`.
3. Alternatively, expose the port via ngrok:
   ```bash
   ngrok http 8000
   ```

---

## Core Pipeline Architecture

```
[SpaceNet Satellite Imagery (0.3m RGB)]
                 │
                 ▼ (Stage 1: PyTorch smp.Unet ResNet34)
    [Building Footprint Masks (IoU 0.8062)]
                 │
                 ▼ (Stage 2: Rasterio + GeoPandas + OSMnx)
    [Georeferenced 3D Polygons + Addresses + Vulnerability Index]
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[FastAPI Live Hub]   [Unity URP Export]
 - POST /api/sos      - 16-bit Heightmap
 - GET /api/sos/active - Landcover Texture
 - 3D MapLibre Web    - Metadata JSON
 - Mobile SOS PWA
```

### 1. AI Building Footprint Segmentation (`src/stage1_extraction/`)
- Architecture: `segmentation_models_pytorch` U-Net with ImageNet-pretrained ResNet34 backbone.
- Trained on SpaceNet 2 (Las Vegas) 650×650 pan-sharpened satellite tiles.
- **Evaluation on held-out test split (146 tiles, never used for tuning):**
  - **IoU: 0.8062** | **F1 Score: 0.8927** | **Precision: 0.910** | **Recall: 0.876**
- **Pretrained Baseline Comparison:** Evaluated zero-shot WHU building model (`giswqs` EfficientNet-B4 UNet++):
  - Our model: **0.8062 IoU** vs Pretrained baseline: **0.0200 IoU** (40× domain adaptation gain).

### 2. Semantic Enrichment, Addresses & Vulnerability (`src/stage2_enrichment/`)
- **Vectorization (`vectorize.py`):** Inverts raster masks to EPSG:4326 polygons (round-trip IoU > 0.992).
- **Address Generation (`generate_addresses.py`):** DBSCAN clustering into blocks (`7-A`, `7-B`), reading-order structure numbering (`7-A-01`), and OSM road proximity (`Block 7-A, Structure 1, 20m north of Oxley Lane`).
- **Vulnerability Scoring (`vulnerability.py`):** Normalized 4-component index combining density (0.35), structure area (0.25), size variance (0.20), and road access (0.20).
- **Spatial Reverse Geocoding (`reverse_geocode.py`):** Millisecond spatial indexing resolving `(lat, lon, baro_floor)` to exact building footprints, indoor/outdoor offsets, and floor levels.

### 3. Real-Time Emergency Backend (`src/server.py`)
- FastAPI service with in-memory thread-safe incident database.
- Multi-hazard incident triage: `Medical`, `Fire`, `Structural Collapse`, and `General Emergency`.
- **Zero-PII & 24h Expiry:** Only coordinates, floor, timestamp, and incident type are recorded. All records auto-purge after 24 hours.
- **Live SOS Pins (`GET /api/sos/active`):** Broadcasts active unexpired incidents directly onto the shared Twin Explorer map with recency status (`critical`, `recent`, `aged`).

### 4. Client Surfaces (`demo/`)
- **Twin Explorer (`demo/index.html`):** MapLibre GL JS + Esri World Imagery (no API keys required). 3D fill-extrusion polygons colored by vulnerability risk, live pulsing SOS beacons, dispatcher metrics, and "Run AI Live" radar sweep scan.
- **Mobile SOS Beacon (`demo/sos.html`):** Responsive dark-glassmorphic PWA featuring a giant pulsing emergency orb, hazard type picker, floor level selector, instant digital-twin address card, and 1-tap link sharing.
- **Rescuer Tactical HUD (`demo/receiver.html`):** High-contrast navigation card, target floor badge, 3D building target view, direct Google Maps turn-by-turn routing, and client-side AR compass heading HUD.

### 5. Unity Simulation Export (`src/export_unity.py`)
- Generates 16-bit grayscale heightmaps (`uint16`), vulnerability landcover textures, and `metadata.json` for Unity URP procedural terrain generation.

---

## Attributions & Acknowledgments

- **SpaceNet Dataset:** SpaceNet 2 Las Vegas building footprints dataset provided by SpaceNet on AWS Open Data.
- **Microsoft Building Footprints:** Inspiration for algorithmic building extraction and address mapping.
- **WHU Pretrained Baseline:** `giswqs` pretrained building footprint model (Apache-2.0) used for zero-shot domain evaluation.
- **Map & GIS Libraries:** MapLibre GL JS (BSD 3-Clause), Esri World Imagery, GeoPandas, Shapely, Rasterio, OSMnx / OpenStreetMap contributors.
- **Deep Learning:** PyTorch, `segmentation_models_pytorch` by Pavel Yakubovskiy, `timm` by Ross Wightman.

---

## Academic & Hackathon Metadata

- **Author:** Syed Muhammad Haider Taqvee
- **Institution:** Institute of Space Technology (IST), Islamabad, Pakistan
- **Degree:** BS Space Science
- **Supervisor:** Dr. Sajid Ghuffar
- **Submission:** AI Builders Hackathon (Devpost, 2026)
