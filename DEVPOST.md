# TerraTwin SOS — 3D Multi-Hazard Digital Twin for Emergency Rescue & Disaster Simulation

> **AI Builders Hackathon 2026** | **Category:** AI & Geospatial / Social Impact / Robotics & Simulation  
> **Author:** Syed Muhammad Haider Taqvee (BS Space Science, Institute of Space Technology, Islamabad)  
> **Supervisor:** Dr. Sajid Ghuffar  
> **Official Code Repository:** [https://github.com/haidertaqvee/terratwin-sos](https://github.com/haidertaqvee/terratwin-sos)  
> **Academic FYP Repository:** [https://github.com/haidertaqvee/digital-twin-fyp](https://github.com/haidertaqvee/digital-twin-fyp)

---

## 🌟 Inspiration

When catastrophic disasters strike—whether structural collapse following a severe earthquake, sudden monsoon flash flooding, urban conflagrations, or medical trauma—first responders and trapped survivors face a fatal bottleneck: **address blackouts and spatial blindness**. 

In informal settlements, refugee encampments, rural fringe corridors, or war/disaster-damaged zones, traditional street addresses either do not exist or are physically obliterated. A survivor calling dispatch might whisper:
> *"I'm in a four-story building near the highway corner, 3rd floor trapped in the hallway, water is rising."*

Raw GPS coordinates like `(33.5198, 73.1761)` or `(36.1914, -115.2019)` are virtually useless to an incident commander trying to determine if ground egress is flooded, which stairwell collapsed, or where a fire ladder bucket must reach.

Inspired by spatial anchors that pin digital entities to physical space, **TerraTwin SOS** reverses the concept for disaster survival:
**Anyone can drop an emergency beacon that instantly snaps to an AI-reconstructed 3D digital twin—anchored to real-world Digital Elevation Models (DEM), calculating exact human-readable addresses, building structure IDs, discrete floor levels, and real-time flood/seismic hazard risks.**

---

## 🚀 What It Does

TerraTwin SOS is an end-to-end multi-hazard digital twin pipeline and emergency dispatch ecosystem:

1. **Satellite Imagery to AI Segmentation:** Ingests raw sub-meter satellite imagery (SpaceNet 2) and extracts crisp building footprints using an optimized PyTorch ResNet34 U-Net (**Test IoU: 0.8062**, **F1 Score: 0.8927**).
2. **Algorithmic Address & Block Generation:** Automatically clusters structures into neighborhood blocks via DBSCAN, numbers structures in natural reading order, and snaps to OpenStreetMap road vectors to generate human-readable physical addresses (e.g. `"Block 7-A, Structure 1, 20m north of Oxley Lane"`).
3. **Multi-Hazard Vulnerability Scoring:** Automatically evaluates every structure from 0.0 to 1.0 based on structural density, footprint area, shape variance, and road remoteness to prioritize dispatch triage.
4. **AWS Terrarium DEM Topographic Precision:** Integrates real-world AWS Open Data Terrarium Digital Elevation Models (30m/10m resolution) using bilinear interpolation and sub-millisecond LRU memoization (1.07 ms) to establish true Mean Sea Level (MSL) ground datum and exact floor altitudes across Islamabad (IST Campus ~530.7m MSL) and Las Vegas (Sector 7 ~685m MSL).
5. **Interactive 3D Multi-Floor Building Slices:** Extrudes structures into discrete, interactable habitable floors and concrete floor slabs. Features a dynamic **3D Floor Explosion Slider** allowing floors to float apart in mid-air for interior void inspection.
6. **Three.js Volumetric Floor Studio:** Provides interactive 3D inspection with three specialized vision modes:
   - **Standard 3D:** True risk-rated materials with directional lighting.
   - **🔥 FLIR Thermal:** False-color infrared heatmap gradient simulating internal heat and smoke accumulation.
   - **📐 X-Ray Wire:** Architectural blueprint wireframe mode revealing internal floor plates.
7. **3D Hydraulic Flood Inundation Simulator:** Real-time water stage simulator with dynamic surge control (`0.0m` to `+10.0m`), graduated vertical hydraulic gauge tube visualizer, live building submergence percentages, and automated vertical refuge protocols.
8. **USGS Real-Time Seismic & Tectonic Fault Monitor:** Live USGS earthquake feed (M2.5+ events) integrated with 10-tier Modified Mercalli Intensity (MMI) shakemaps, active tectonic fault line overlays (Margalla Thrust, Rawat Fault, Las Vegas Valley fault system), and stairwell shear failure advisories.
9. **Mobile Emergency SOS Beacon (PWA):** One-tap citizen web app (`demo/sos.html`) with tactile haptic vibration feedback, floor selector, RTK satellite certainty badge, and a **Web Audio API Acoustic Rescue Locator Beacon** that pulses a dual-tone chirp (`880Hz / 1320Hz`) to guide SAR dogs and search teams under rubble.
10. **Tactical Rescuer Navigation HUD (`demo/receiver.html`):** Military-grade HUD with corner reticles, turn-by-turn routing, live distance countdown and walking/vehicle ETA, and an interactive operational status stepper (`Target SOS` -> `En Route` -> `On Scene` -> `Evacuating`).
11. **Zero PII & 24h Privacy Purge:** Absolute zero personal identifiable information (no names, phone numbers, or hardware IDs collected). All active emergency incidents automatically expire and purge after 24 hours.
12. **Unity URP Simulation Export:** Exports 16-bit heightmaps, vulnerability landcover masks, and georeference metadata for autonomous UAV and ground rescue robotics simulation.

---

## 📊 Technical Validation: Model Metrics & Pretrained Baseline

To prove the credibility of the segmentation pipeline, our fine-tuned model was evaluated on a held-out test split of 146 SpaceNet tiles (never seen during training or tuning) against a zero-shot pretrained baseline (WHU Building Dataset EfficientNet-B4 UNet++):

| Model / Pipeline | Test Split IoU | F1 Score (Dice) | Precision | Recall | Parameters |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pretrained Baseline (WHU EfficientNet-B4)** | `0.0200` | `0.0388` | `0.0271` | `0.0707` | 24.5 M |
| **TerraTwin SOS (Ours: smp.Unet ResNet34)** | **`0.8062`** | **`0.8927`** | **`0.9101`** | **`0.8760`** | 24.4 M |

> **Domain Gap Finding:** The **40× performance gap** demonstrates that off-the-shelf building models trained on aerial imagery from New Zealand or East Asia fail completely when transferred to arid, high-albedo Southwestern desert environments. Specialized satellite fine-tuning with fixed dataset-wide normalization (`NORM_MAX = 1910.0`) was essential.

---

## ⚡ Performance Benchmarks & Optimizations

To deliver a smooth 60fps experience even on mobile field networks:
- **GZip Compression:** Attached `GZipMiddleware(minimum_size=1000)` reducing `/api/buildings/all` payload from 1,783.2 KB -> **250.0 KB** (**86% network bandwidth savings**).
- **In-Memory GeoJSON Pre-Cache:** Pre-loads all 20 demo tile files, predicted layers, and manifests into memory at boot, slashing disk I/O.
- **DEM Elevation LRU Memoization:** Point elevation lookups cached with 5-decimal coordinate rounding, cutting latency from 1,530 ms -> **1.07 ms** (**>1,400× speedup**).
- **Pre-Warmed Seismic Feeds:** USGS earthquake feed pre-fetched at server launch for sub-20ms responsiveness.

| Endpoint | Original Size | Compressed Size | Reduction | Latency | Speedup |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/buildings/all` | 1,783.2 KB | **250.0 KB** | **-86.0%** | **410 ms** | **~3× faster** |
| `/api/dem/elevation` | 0.1 KB | 0.1 KB | N/A | **1.07 ms** | **>1,400× faster** |
| `/api/hazards/flood` | 3.0 KB | **1.3 KB** | **-56.7%** | **2.1 ms** | **>20× faster** |
| `/api/hazards/earthquakes`| 9.7 KB | **2.5 KB** | **-74.2%** | **19.9 ms** | **>34× faster** |
| `/demo/index.html` | 119.5 KB | **26.0 KB** | **-78.2%** | **10.2 ms** | **~8× faster** |
| `/demo/sos.html` | 24.3 KB | **6.6 KB** | **-72.8%** | **4.7 ms** | **~7× faster** |
| `/demo/receiver.html` | 31.1 KB | **8.4 KB** | **-73.0%** | **4.8 ms** | **~8× faster** |

---

## 🛠️ How We Built It

- **Computer Vision & Deep Learning:** PyTorch 2.5, `segmentation_models_pytorch`, `timm`, CUDA 12.1 on an NVIDIA GeForce GTX 1660 SUPER. Trained with combined BCE + Dice loss and `bf16` mixed-precision autocast.
- **Geospatial & Vectorization:** `rasterio`, `geopandas`, `shapely`, `pyproj`, `scikit-learn` (DBSCAN), and `osmnx` for OpenStreetMap road network caching and nearest-edge snapping.
- **Real-Time Backend:** FastAPI server with thread-safe in-memory spatial indexing, sub-millisecond reverse geocoding, and automated 24-hour incident expiration.
- **3D Graphics & Visual Interfaces:**
  - MapLibre GL JS with Google Hybrid, Google Satellite, and Esri World Imagery.
  - Three.js WebGL volumetric studio with custom extrusion shaders for interactive multi-floor analysis.
  - Responsive dark-glassmorphic "Orbital" tactical mission-control theme.
- **Audio & Haptic Synthesis:** Web Audio API oscillator synthesis generating tactical acoustic beacon sweeps without external audio assets.

---

## 🧗 Challenges We Overcame

1. **The `fp16` Autocast NaN Bug:** Standard PyTorch float16 autocast caused immediate NaN forward logits with this ResNet34 encoder. We identified the numerical instability and transitioned to `bf16` autocast without gradient scaling.
2. **DEM Ground Elevation Discrepancies:** Early iterations lacked true topographic anchoring. Integrating AWS Open Data Terrarium DEM with bilinear interpolation resolved ground heights to ±1.0m accuracy across both Islamabad (Zone V) and Las Vegas (Sector 7).
3. **Multi-Floor 3D Separation:** Standard 2D footprints cannot isolate individual floors. We built a custom geometry engine that extrudes separate habitable floors and 18cm concrete structural slabs, enabling dynamic explosion and selective floor inspection.
4. **Resilient GIS Processing:** Handled GeoJSON CRS84 dictionary validation issues in GeoPandas, normalized OSM road name structures across irregular array shapes, and implemented zero-failure fallbacks for network drops.

---

## 🔮 What's Next for TerraTwin

- **Autonomous Drone Path Planning:** Utilizing the Unity URP digital twin to train autonomous UAV agents for obstacle avoidance and survivors scouting in collapsed building rubble.
- **Satellite Change Detection:** Comparing pre-disaster and post-disaster satellite passes to automatically flag collapsed structures and blocked roads.
- **Indoor Sub-Meter Localization:** Integrating smartphone barometric pressure sensors and WiFi/Bluetooth beacons to pinpoint exact room-level positions within multi-story complexes.

---

## 🎬 Video Shot List (2:30 Demo Walkthrough)

- **[0:00 - 0:25] The Problem Hook:** Aerial footage of disaster-damaged city. Audio: *"In an emergency, coordinates don't tell rescuers which building or floor you're trapped in—or whether ground ingress is submerged under floodwaters."*
- **[0:25 - 0:55] Mobile SOS Beacon (Citizen Flow):** User opens `demo/sos.html`, selects `🌊 Flood`, picks `Floor 3`, and taps the pulsing SOS orb. Screen displays verified address, DEM ground MSL, floor altitude, and begins emitting the **Tactical Acoustic Locator Chirp**. User taps "Share Rescue Link".
- **[0:55 - 1:35] Mission Control Center (Twin Explorer):** Dispatcher view (`demo/index.html`). Active incident pulses in real time. Dispatcher activates the **3D Flood Simulator**, slides surge to `+3.5m`, watching water engulf the ground floors while the vertical hydraulic gauge visualizes water stage.
- **[1:35 - 1:55] Volumetric Floor Studio & Seismic Monitor:** Dispatcher opens the building in 3D Volumetric Studio, slides the explode control to separate floor slabs, switches to **FLIR Thermal Vision**, and inspects the live USGS seismic fault proximity.
- **[1:55 - 2:20] Rescuer Tactical HUD (Field Flow):** Rescuer opens `demo/receiver.html`. Shows tactical corner reticles, live proximity countdown (`240m • ~3 min walking`), target floor highlight, and AR compass bearing.
- **[2:20 - 2:30] Call to Action:** Closing title card: TerraTwin SOS — Space Science & AI for life-saving digital twins.

---

## 📚 Open Source Repositories & Resources Used

- **Code Repositories:**
  - Official Project: [https://github.com/haidertaqvee/terratwin-sos](https://github.com/haidertaqvee/terratwin-sos)
  - Academic FYP: [https://github.com/haidertaqvee/digital-twin-fyp](https://github.com/haidertaqvee/digital-twin-fyp)
- **Datasets & APIs:** SpaceNet 2 (AWS Open Data), AWS Terrarium DEM, USGS Earthquake API, OpenStreetMap.
- **Frameworks:** MapLibre GL JS, Three.js, PyTorch, `segmentation_models_pytorch` by Pavel Yakubovskiy, FastAPI.
