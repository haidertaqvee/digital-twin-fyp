---
name: terratwin-ops
description: Operational workflows and management commands for the TerraTwin SOS 3D Geospatial Digital Twin platform, including starting/stopping the server, testing telemetry, and validating hazard simulations.
---

# TerraTwin Operations Skill

Use this skill when managing the TerraTwin SOS platform in the Antigravity environment.

## 1. Starting the Server
Run the FastAPI backend server using the project's dedicated conda environment:
```powershell
& E:\digital-twin-fyp\envs\digital-twin\python.exe src/server.py --port 8000 --host 0.0.0.0
```

## 2. Health Verification
Verify all local endpoints are responding with HTTP 200:
```powershell
@("http://localhost:8000/index.html", "http://localhost:8000/sos.html", "http://localhost:8000/receiver.html", "http://localhost:8000/api/tiles") | ForEach-Object {
    $code = (curl.exe -s -o /dev/null -w "%{http_code}" $_)
    Write-Host "$_ -> $code"
}
```

## 3. Reverse Geocoding & DEM Tests
Test reverse geocoding and DEM elevation for any coordinate:
```powershell
& E:\digital-twin-fyp\envs\digital-twin\python.exe src/stage2_enrichment/reverse_geocode.py --lat 36.1648 --lon -115.1385 --baro-floor 3
```

## 4. Multi-Hazard Simulation Check
Query real-time USGS seismic events:
```powershell
curl.exe -s "http://localhost:8000/api/hazards/earthquakes?lat=36.1648&lon=-115.1385"
```
