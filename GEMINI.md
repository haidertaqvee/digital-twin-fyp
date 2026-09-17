# TerraTwin SOS — Antigravity Workspace Environment

## 1. Project Overview
TerraTwin SOS is an end-to-end 3D Geospatial Digital Twin & Multi-Hazard Emergency Dispatch System.
- **Backend:** FastAPI, GeoPandas, Shapely, PyProj, Pillow, Requests (Python 3.10).
- **Frontend:** HTML5, Vanilla JavaScript, MapLibre GL JS (v4.7.1), Three.js (r128), OrbitControls.
- **Topography & Hazards:** AWS Open Data Terrarium DEM raster elevation, USGS real-time seismic feed, 3D Flood Inundation Simulator.
- **Target Hardware / Sim-to-Real:** NVIDIA Jetson Orin Nano, MAVLink telemetry protocol, Nebius AI Cloud / Token Factory.

## 2. Antigravity Environment Setup
- **Python Environment:** `E:\digital-twin-fyp\envs\digital-twin\python.exe`
- **Primary Server Command:**
  ```powershell
  & E:\digital-twin-fyp\envs\digital-twin\python.exe src/server.py --port 8000 --host 0.0.0.0
  ```
- **Batch Launcher:** `start_offline.bat`

## 3. Core Endpoints & Web Apps
- **3D Twin Explorer:** `http://localhost:8000/index.html` (or `https://haidertaqvee.github.io/terratwin-sos/index.html`)
- **Citizen SOS Beacon:** `http://localhost:8000/sos.html` (or `https://haidertaqvee.github.io/terratwin-sos/sos.html`)
- **Rescuer Tactical HUD:** `http://localhost:8000/receiver.html` (or `https://haidertaqvee.github.io/terratwin-sos/receiver.html`)
- **Tile Manifest:** `GET /api/tiles`
- **Building Vector Tiles:** `GET /api/tile/{id}` or `GET /api/buildings/all`
- **SOS Incident Registration:** `POST /api/sos`
- **Live Active Incidents:** `GET /api/sos/active`
- **DEM Ground Elevation:** `GET /api/dem/elevation?lat={lat}&lon={lon}`
- **USGS Seismic Hazards:** `GET /api/hazards/earthquakes?lat={lat}&lon={lon}`
- **Hydrological Flood Simulation:** `GET /api/hazards/flood?lat={lat}&lon={lon}`

## 4. Coding & Architecture Guidelines
- Preserve client-side standalone fallbacks in all web applications so that they function both with the Python backend server AND in static hosting environments (GitHub Pages / Vercel).
- Keep relative paths (`index.html`, `sos.html`, `receiver.html`) without leading slashes to prevent subpath breakages.
- Maintain high precision: Ground elevation calculations must use exact DEM datum offsets.
