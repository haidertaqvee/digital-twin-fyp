# TerraTwin SOS — Devpost Project Submission

> **AI Builders Hackathon 2026** | **Category:** AI & Geospatial / Social Impact / Robotics  
> **Author:** Syed Muhammad Haider Taqvee (BS Space Science, Institute of Space Technology)  
> **Supervisor:** Dr. Sajid Ghuffar  

---

## Inspiration

When disasters strike—whether structural collapse after an earthquake, rapid urban fire, flash flooding, or medical emergency—first responders face a fatal bottleneck: **address blackouts**. In informal settlements, refugee settlements, or damaged peri-urban areas, traditional street numbers either do not exist or are obliterated.

A victim calling 911 might say *"I'm in a gray two-story building near the dirt corner, 2nd floor."* Coordinates like `(36.19141, -115.20194)` are meaningless to an ambulance driver trying to find an entrance or a fire ladder operator positioning a bucket.

Inspired by Pokémon GO's mechanic of anchoring digital entities to precise real-world physical locations, **TerraTwin SOS** reverses the concept for disaster survival: **anyone can drop an emergency beacon that instantly snaps to an AI-reconstructed 3D digital twin, generating an exact human-readable address, building structure ID, and floor level.**

---

## What It Does

TerraTwin SOS is an end-to-end pipeline and emergency dispatch ecosystem:

1. **Satellite Imagery to AI Segmentation:** Ingests raw sub-meter satellite imagery (SpaceNet 2) and segments building footprints using an optimized PyTorch ResNet34 U-Net (**IoU 0.8062**).
2. **Algorithmic Address Generation:** Clusters structures into neighborhood sectors and blocks using DBSCAN, assigns reading-order structure IDs, and measures proximity to OpenStreetMap road networks to produce addresses like:  
   `"Block 7-A, Structure 1, 20m north of Oxley Lane"`.
3. **Multi-Hazard Vulnerability Scoring:** Automatically scores every structure from 0 to 1 based on spatial density, footprint area, morphological variance, and road remoteness to prioritize dispatch triage.
4. **Mobile Citizen Beacon (PWA):** A one-tap emergency web app (`demo/sos.html`) allowing trapped individuals to broadcast an SOS with their estimated floor level and emergency type (`Medical`, `Fire`, `Structural Collapse`, `General`).
5. **Live Incident Pins on 3D Twin Explorer:** Active emergencies pulse in real time on a MapLibre 3D satellite twin map (`demo/index.html`), color-coded by recency and hazard category.
6. **Tactical Rescuer Navigation HUD (`demo/receiver.html`):** Turn-by-turn GPS routing paired with an in-browser tactical compass HUD pointing directly to the target building perimeter and highlighting the target floor.
7. **Privacy-First (Zero PII):** No names, phone numbers, or identity tracking. All emergency records automatically expire and purge after 24 hours.
8. **Unity URP Simulation Export:** Exports 16-bit heightmaps, vulnerability landcover masks, and georeference metadata for autonomous vehicle and robotic rescue simulation.

---

## Technical Validation: Model Metrics & Pretrained Baseline

To prove the credibility of the segmentation pipeline, our fine-tuned model was evaluated on a held-out test split of 146 SpaceNet tiles (never seen during training or tuning) against a zero-shot pretrained baseline (WHU Building Dataset EfficientNet-B4 UNet++):

| Model / Pipeline | Test Split IoU | F1 Score (Dice) | Precision | Recall | Parameters |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pretrained Baseline (WHU EfficientNet-B4)** | `0.0200` | `0.0388` | `0.0271` | `0.0707` | 24.5 M |
| **TerraTwin SOS (Ours: smp.Unet ResNet34)** | **`0.8062`** | **`0.8927`** | **`0.9101`** | **`0.8760`** | 24.4 M |

> **Domain Gap Finding:** The 40× performance gap demonstrates that off-the-shelf building models trained on aerial imagery from New Zealand or East Asia fail completely when transferred to arid, high-albedo Southwestern desert environments. Specialized satellite fine-tuning with fixed dataset-wide normalization (`NORM_MAX = 1910.0`) was essential.

---

## How We Built It

- **Computer Vision & Training:** PyTorch 2.5, `segmentation_models_pytorch`, `timm`, CUDA 12.1 on an NVIDIA GeForce GTX 1660 SUPER. Trained with combined BCE + Dice loss and `bf16` mixed-precision autocast.
- **Geospatial & Vectorization:** `rasterio`, `geopandas`, `shapely`, `pyproj`, `scikit-learn` (DBSCAN), and `osmnx` for OpenStreetMap drive network caching and nearest-edge snapping.
- **Real-Time Backend:** FastAPI server with thread-safe in-memory spatial indexing, sub-10 millisecond reverse geocoding, and automated 24-hour incident expiration.
- **Interactive 3D Web Interfaces:** MapLibre GL JS with Esri World Imagery (zero proprietary token dependencies), GPU-accelerated `fill-extrusion` 3D building rendering, and responsive glassmorphism ("Orbital" UI theme).
- **Simulation Export:** Procedural 16-bit `uint16` heightmaps and landcover texture generation for Unity URP terrain importing.

---

## Challenges We Overcame

1. **The `fp16` Autocast NaN Bug:** Standard PyTorch float16 autocast caused immediate NaN forward logits with this ResNet34 encoder. We identified the numerical instability and transitioned to `bf16` autocast without gradient scaling.
2. **Checkpoint Preservation:** Engineered automated backup logic preventing fresh training runs from silently overwriting previous top-performing checkpoints.
3. **Domain Shift & Weight Availability:** When Microsoft's building footprint model weights proved unreleased, we sourced and evaluated the WHU building benchmark to rigorously validate domain transfer.
4. **Resilient GIS Processing:** Addressed GeoJSON CRS84 dictionary validation issues in GeoPandas, normalized OSM road name structures across irregular array shapes, and implemented zero-failure fallbacks for network drops.

---

## What's Next for TerraTwin

- **Autonomous Drone Path Planning:** Utilizing the Unity URP digital twin to train autonomous UAV agents for obstacle avoidance and survivors scouting in collapsed building rubble.
- **Satellite Change Detection:** Comparing pre-disaster and post-disaster satellite passes to automatically flag collapsed structures and blocked roads.
- **Indoor Sub-Meter Localization:** Integrating smartphone barometric pressure sensors and WiFi/Bluetooth beacons to pinpoint exact room-level positions within multi-story complexes.

---

## Video Shot List (2:30 Demo Walkthrough)

- **[0:00 - 0:20] The Problem Hook:** Aerial footage of disaster-damaged city. Audio: *"In an emergency, coordinates don't tell rescuers which building or floor you're trapped in."*
- **[0:20 - 0:50] Mobile SOS Trigger (Citizen Flow):** User opens `demo/sos.html` on a mobile phone, taps the hazard pill (`Fire`), selects `Floor 2`, and hits the giant pulsing SOS orb. Screen instantly displays verified address: *"Block 7-A, Structure 1, 20m north of Oxley Lane — Floor 1"*. User taps "Share Rescue Link".
- **[0:50 - 1:30] Operations Center (Twin Explorer):** Cut to dual-monitor dispatcher view (`demo/index.html`). The live incident pin pulses on the 3D MapLibre map. Dispatcher clicks the pin, camera smoothly swoops in with 3D pitch/bearing, revealing the highlighted building extrusion and vulnerability rating.
- **[1:30 - 1:55] AI Architecture & Radar Sweep:** Dispatcher clicks "Run AI Live"—cyan radar beam sweeps across the screen. Cut to metrics screen highlighting **0.8062 IoU** vs **0.0200** pretrained baseline.
- **[1:55 - 2:20] Rescuer Tactical HUD (Field Flow):** Rescuer opens the shared link on their smartphone (`demo/receiver.html`). Shows high-contrast address banner, floor badge, Google Maps navigation button, and live tactical compass HUD rotating to point directly at the target building.
- **[2:20 - 2:30] Call to Action:** Closing title card: TerraTwin SOS — Space Science meets AI for life-saving digital twins.

---

## Open Source Repositories & Resources Used

- SpaceNet 2 Las Vegas Building Footprints Dataset (AWS Open Data)
- MapLibre GL JS & Esri World Imagery
- `segmentation_models_pytorch` (Pavel Yakubovskiy, MIT)
- WHU Building Dataset Pretrained Weights (`giswqs`, Apache-2.0)
