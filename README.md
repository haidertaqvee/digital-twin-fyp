# TerraTwin SOS — 3D Multi-Hazard Digital Twin Platform

**Automated satellite imagery pipeline → AI building footprint segmentation → vectorized 3D digital twin with generated addresses, live incident beacons, multi-hazard simulation, and tactical rescue navigation.**

- **Official Repository:** [https://github.com/haidertaqvee/terratwin-sos](https://github.com/haidertaqvee/terratwin-sos)
- **Academic FYP Repository:** [https://github.com/haidertaqvee/digital-twin-fyp](https://github.com/haidertaqvee/digital-twin-fyp)
- **Final Year Project (FYP):** BS Space Science, Institute of Space Technology, Islamabad (Supervised by Dr. Sajid Ghuffar)
- **Hackathon Submission:** AI Builders Hackathon (Devpost, Deadline: September 15, 2026)
- **Target Environments:** Web / Mobile (FastAPI + MapLibre GL 3D + Three.js + PWA) & Simulation (Unity URP)

---

## ⚡ Quick Start (One Command Run)

Launch the full multi-hazard stack (FastAPI backend + 3D Twin Explorer + Mobile SOS Beacon + Rescuer HUD):

```powershell
# Using the project conda environment
E:\digital-twin-fyp\envs\digital-twin\python.exe src/server.py --port 8000
```

Open your browser:
- **3D Twin Explorer (Dispatcher Map):** [http://localhost:8000/demo/index.html](http://localhost:8000/demo/index.html)
- **Mobile SOS Beacon (Citizen PWA):** [http://localhost:8000/demo/sos.html](http://localhost:8000/demo/sos.html)
- **Rescuer Navigation HUD:** [http://localhost:8000/demo/receiver.html](http://localhost:8000/demo/receiver.html)

### Testing on a Mobile Phone (Same LAN or ngrok)

1. **Find your machine's LAN IP:**
   ```powershell
   ipconfig | findstr IPv4
   # Example: 192.168.1.50
   ```
2. **On your mobile phone browser:** Navigate to `http://192.168.1.50:8000/demo/sos.html`.
3. Alternatively, expose via ngrok:
   ```bash
   ngrok http 8000
   ```

---

## 🌟 Major Capabilities & Innovations

### 1. AI Building Footprint Segmentation (`src/stage1_extraction/`)
- Architecture: `segmentation_models_pytorch` U-Net with ImageNet-pretrained ResNet34 backbone.
- Evaluated on a held-out test split of 146 SpaceNet tiles (never seen during training):
  - **IoU: 0.8062** | **F1 Score: 0.8927** | **Precision: 0.9101** | **Recall: 0.8760**
- **40× Domain Adaptation Gain:** Outperforms zero-shot WHU building baseline (0.0200 IoU) by 40× in desert urban terrain.

### 2. AWS Open Data Terrarium DEM Topographic Precision
- Real-world Digital Elevation Models (30m/10m resolution) anchored to Mean Sea Level (MSL).
- Sub-millisecond point elevation lookups (1.07 ms) via LRU memoization.
- Dual-regional support: Islamabad (IST Campus ~530.7m MSL) and Las Vegas (Sector 7 ~685m MSL).

### 3. Interactive 3D Multi-Floor Building Slices
- Discrete interactable floors + 18cm concrete structural slabs.
- Dynamic 3D Floor Explosion Slider (floors float apart in mid-air).
- Three.js Volumetric Studio with **Standard 3D**, **🔥 FLIR Thermal Heatmap**, and **📐 Architectural X-Ray Wireframe** modes.

### 4. 3D Hydraulic Flood Inundation Simulator
- Dynamic water surge slider (`0.0m` to `+10.0m`).
- Vertical hydraulic water stage tube meter visualizer.
- Submergence metrics and automated vertical refuge advisories.

### 5. USGS Real-Time Seismic & Tectonic Fault Monitor
- Live USGS earthquake feed (M2.5+ events) with 10-tier Modified Mercalli Intensity (MMI) shakemaps.
- Active fault overlays (Margalla Thrust, Rawat Fault, Las Vegas Valley faults).
- Structural shear failure advisories.

### 6. Mobile Citizen SOS Beacon (`demo/sos.html`)
- One-tap emergency broadcast with floor level and hazard type.
- Haptic vibration feedback on buttons and transmission.
- **Acoustic Rescue Locator Beacon:** Web Audio API high-frequency dual-tone chirp (`880Hz / 1320Hz`) pulsing every 2.2s to guide search dogs and rescue crews under debris.

### 7. Tactical Rescuer HUD Navigation (`demo/receiver.html`)
- Military corner crosshair reticles.
- Live proximity countdown (meters + walking/vehicle ETA).
- Interactive operational status stepper (`Target SOS` -> `En Route` -> `On Scene` -> `Evacuating`).

### 8. Performance Speedup (86% Payload Savings)
- GZipMiddleware enabled on FastAPI server.
- In-memory GeoJSON pre-caching for sub-millisecond API responses.

---

## 🏛️ Repository Architecture

```
digital-twin-fyp/
├── demo/
│   ├── index.html       # 3D Twin Explorer, Flood Sim, Seismic Monitor & Three.js Studio
│   ├── sos.html         # Citizen SOS Beacon PWA with Acoustic Chirp
│   └── receiver.html    # Tactical Rescuer Navigation HUD
├── src/
│   ├── server.py        # FastAPI high-speed backend with GZip & In-Memory Caches
│   ├── stage1_extraction/   # PyTorch U-Net training, inference & evaluation
│   ├── stage2_enrichment/   # Vectorization, address generation & vulnerability index
│   └── export_unity.py      # Unity URP 16-bit heightmaps and textures
├── models/
│   └── unet_resnet34_best.pth  # Trained checkpoint (IoU 0.8062)
├── DEVPOST.md           # Official Hackathon Project Submission Dossier
├── README.md            # Comprehensive project documentation
└── CONTEXT.md           # Authoritative project memory and technical context
```

---

## 🎓 Academic & Hackathon Metadata

- **Author:** Syed Muhammad Haider Taqvee
- **Institution:** Institute of Space Technology (IST), Islamabad, Pakistan
- **Degree:** BS Space Science
- **Supervisor:** Dr. Sajid Ghuffar
- **Submission:** AI Builders Hackathon (Devpost, September 2026)
