# TerraTwin SOS — Project Context & Memory

## The Mission
**TerraTwin SOS** is an automated geospatial digital twin and emergency dispatch platform that converts high-resolution satellite imagery into simulation-ready 3D environments, reverse-geocodes physical structures, simulates multi-hazard events (floods, earthquakes), and coordinates tactical search and rescue.

* **Dual Purpose:** Final Year Project for BS in Space Science at Institute of Space Technology (supervised by Dr. Sajid Ghuffar) and solo student submission for the **AI Builders Hackathon** on Devpost.
* **Hard Deadline:** September 15, 2026, 11:00 PM EDT.
* **GitHub Repositories:**
  - Official Project: `https://github.com/haidertaqvee/terratwin-sos`
  - Academic FYP: `https://github.com/haidertaqvee/digital-twin-fyp`

---

## Pipeline & Tech Stack
1. **Stage 1 (Complete):** Satellite image building footprint segmentation (PyTorch 2.5, `segmentation_models_pytorch` U-Net with ResNet34 backbone, BCE+Dice loss).
   - Test IoU: **0.8062** | F1 Score: **0.8927** | Precision: **0.9101** | Recall: **0.8760** on 146 held-out test tiles.
   - Outperforms WHU zero-shot pretrained baseline (0.0200 IoU) by 40x.
2. **Stage 2 (Complete):** Vectorize raster masks to EPSG:4326 polygons (Rasterio, GeoPandas, Shapely), DBSCAN address clustering, and multi-hazard vulnerability scoring.
3. **Stage 3 (Complete):** 3D building extrusion with discrete interactable habitable floors and concrete structural slabs, dynamic explosion sliders, and Three.js Volumetric Floor Studio (Standard, FLIR Thermal, X-Ray Wireframe).
4. **Stage 4 (Complete):** Multi-hazard disaster engines:
   - 3D Flood Inundation Simulator with graduated vertical hydraulic tube meter.
   - USGS real-time seismic feed + active tectonic fault line overlays + MMI shakemap scale.
   - AWS Terrarium DEM topographic ground elevation with sub-millisecond LRU memoization (1.07 ms).
5. **Stage 5 (Complete):** Dual client applications:
   - Mobile SOS Beacon (`demo/sos.html`) with Web Audio API Acoustic Rescue Locator Beacon chirp (`880Hz / 1320Hz`) and haptics.
   - Tactical Rescuer HUD (`demo/receiver.html`) with military corner reticles, distance & ETA countdown, and operational status cycling.
   - Unity URP export pipeline (16-bit heightmaps, landcover masks, metadata).

---

## Server & Performance Optimizations
- `GZipMiddleware(minimum_size=1000)` reduces payloads by 86% (`/api/buildings/all`: 1,783 KB -> 250 KB).
- In-memory GeoJSON pre-cache eliminates disk reads.
- Point DEM elevation cached via LRU dictionary (`1.07 ms`).
- Pre-warmed USGS earthquake feed.
- Zero PII guarantee with automated 24-hour incident expiration.

---

## Hardware & Environment
- Environment: `envs/digital-twin/` (Python 3.10) with `torch 2.5.1+cu121` on NVIDIA GeForce GTX 1660 SUPER (6 GB).
- OS: Windows (PowerShell).
- Branch: `sos-hackathon` (tracking `origin/sos-hackathon` and pushed to `terratwin/main`).
