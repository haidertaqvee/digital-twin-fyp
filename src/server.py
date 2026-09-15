"""
TerraTwin SOS — FastAPI Backend Server

Serves:
  1. Demo tile GeoJSON vectors and manifest (/api/tiles, /api/tile/{id})
  2. SOS incident registration with reverse-geocoding (/api/sos)
  3. Live active incident pins for Twin Explorer (/api/sos/active)
  4. Single incident retrieval and rescuer routing (/api/sos/{id}, /r/{id})
  5. Static web applications (/demo/*)

Usage:
    python src/server.py
    python src/server.py --port 8000 --host 0.0.0.0
"""

import argparse
import json
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project and src are in path
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stage2_enrichment.reverse_geocode import ReverseGeocoder
from stage2_enrichment.dem import get_dem_elevation
from hazards import (
    get_earthquake_hazard_data,
    get_flood_hazard_data,
    calculate_building_flood_impact,
)

DEFAULT_DEMO_DIR = ROOT_DIR / "data" / "processed" / "demo_tiles"
DEFAULT_WEB_DIR = ROOT_DIR / "demo"
EXPIRY_SECONDS = 86400  # 24 hours

app = FastAPI(
    title="TerraTwin SOS API",
    description="Multi-hazard emergency registration and 3D digital twin explorer backend",
    version="1.0.0",
)

# Enable CORS for local testing, LAN access, and PWA clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure demo directory exists
DEFAULT_WEB_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/demo", StaticFiles(directory=str(DEFAULT_WEB_DIR), html=True), name="demo")

# State
geocoder: Optional[ReverseGeocoder] = None
incidents_db = {}  # incident_id -> dict


class SOSRequest(BaseModel):
    lat: float = Field(..., description="WGS84 latitude")
    lon: float = Field(..., description="WGS84 longitude")
    baro_floor: Optional[int] = Field(None, description="Optional phone barometer-estimated floor")
    emergency_type: Optional[str] = Field("general", description="medical, fire, collapse, flood, earthquake, general")
    notes: Optional[str] = Field(None, description="Optional short emergency note")


def purge_expired_incidents():
    """Remove incidents older than 24h to respect zero-retention privacy."""
    now = time.time()
    expired = [k for k, v in incidents_db.items() if now > v.get("expires_at_epoch", 0)]
    for k in expired:
        del incidents_db[k]


def seed_demo_incidents():
    """Seed sample active incidents for instant reviewer visualization."""
    if not geocoder or len(geocoder.gdf) == 0:
        return

    now = time.time()
    seeds = [
        {"tile": "AOI_2_Vegas_img4174", "floor": 1, "type": "fire", "age_min": 4},
        {"tile": "AOI_2_Vegas_img4059", "floor": 2, "type": "flood", "age_min": 14},
        {"tile": "AOI_2_Vegas_img4906", "floor": 3, "type": "earthquake", "age_min": 26},
        {"tile": "AOI_2_Vegas_img4174", "floor": 2, "type": "medical", "age_min": 39},
        {"tile": "AOI_2_Vegas_img4059", "floor": 1, "type": "collapse", "age_min": 51},
    ]

    for seed in seeds:
        matching = geocoder.gdf[geocoder.gdf["tile"] == seed["tile"]]
        if len(matching) == 0:
            continue
        poly = matching.iloc[min(2, len(matching) - 1)]
        c = poly.geometry.centroid
        lat, lon = float(c.y), float(c.x)

        inc_id = f"demo_{seed['type'][:3]}_{secrets.token_hex(2)}"
        fix = geocoder.lookup(lat, lon, baro_floor=seed["floor"])
        created_epoch = now - (seed["age_min"] * 60)

        incidents_db[inc_id] = {
            "id": inc_id,
            "emergency_type": seed["type"],
            "notes": f"Pre-seeded active incident ({seed['type']}) for visualization",
            "created_at": datetime.fromtimestamp(created_epoch, tz=timezone.utc).isoformat(),
            "created_at_epoch": created_epoch,
            "expires_at_epoch": created_epoch + EXPIRY_SECONDS,
            **fix,
        }


@app.on_event("startup")
def startup_event():
    global geocoder
    demo_dir = getattr(app.state, "demo_dir", DEFAULT_DEMO_DIR)
    print(f"Loading ReverseGeocoder from {demo_dir} ...")
    geocoder = ReverseGeocoder(demo_dir=demo_dir)
    print(f"ReverseGeocoder ready with {len(geocoder.gdf)} structures across {geocoder.gdf['tile'].nunique()} tiles.")
    if not getattr(app.state, "no_seed", False):
        seed_demo_incidents()
        print(f"Pre-seeded {len(incidents_db)} demo incidents for testing.")


@app.get("/")
def root():
    return RedirectResponse(url="/demo/index.html")


@app.get("/api/health")
def health():
    purge_expired_incidents()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "structures_indexed": len(geocoder.gdf) if geocoder else 0,
        "tiles_available": geocoder.gdf["tile"].nunique() if geocoder else 0,
        "active_incidents": len(incidents_db),
    }


@app.get("/api/tiles")
def list_tiles():
    demo_dir = getattr(app.state, "demo_dir", DEFAULT_DEMO_DIR)
    manifest_path = demo_dir / "_manifest.json"
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read manifest: {e}")

    # Fallback if manifest is missing
    files = sorted(demo_dir.glob("tile_*.geojson"))
    return {
        "sector": "7",
        "tiles": [{"tile": f.stem.replace("tile_", ""), "file": f.name} for f in files],
    }


@app.get("/api/tile/{tile_id}")
def get_tile_geojson(tile_id: str):
    demo_dir = getattr(app.state, "demo_dir", DEFAULT_DEMO_DIR)
    if tile_id in ["all", "tile_all", "all.geojson", "tile_all.geojson"]:
        all_path = demo_dir / "all_demo_buildings.geojson"
        if all_path.exists():
            return json.loads(all_path.read_text(encoding="utf-8"))

    clean_id = tile_id if tile_id.startswith("tile_") else f"tile_{tile_id}"
    if not clean_id.endswith(".geojson"):
        clean_id += ".geojson"
    path = demo_dir / clean_id
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Tile {tile_id} not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading tile: {e}")


@app.get("/api/buildings/all")
def get_all_demo_buildings():
    demo_dir = getattr(app.state, "demo_dir", DEFAULT_DEMO_DIR)
    all_path = demo_dir / "all_demo_buildings.geojson"
    if not all_path.exists():
        raise HTTPException(status_code=404, detail="all_demo_buildings.geojson not found")
    try:
        return json.loads(all_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading all buildings: {e}")


@app.get("/api/buildings/predicted")
def get_all_predicted_buildings():
    pred_path = ROOT_DIR / "data" / "processed" / "test" / "vectors" / "buildings_predictions.geojson"
    if not pred_path.exists():
        raise HTTPException(status_code=404, detail="buildings_predictions.geojson not found")
    try:
        return json.loads(pred_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading predicted buildings: {e}")


@app.get("/api/mesh/{tile_id}")
def get_tile_3d_mesh(tile_id: str):
    mesh_dir = ROOT_DIR / "data" / "processed" / "stage3_3d"
    clean_id = tile_id.replace(".obj", "").replace("tile_", "")
    if not clean_id.endswith("_buildings"):
        clean_id += "_buildings"
    path = mesh_dir / f"{clean_id}.obj"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"3D mesh for {tile_id} not found")
    return FileResponse(path, media_type="text/plain", filename=f"{clean_id}.obj")


@app.post("/api/sos")
def register_sos(req: SOSRequest, request: Request):
    if geocoder is None:
        raise HTTPException(status_code=503, detail="Geocoder not initialized")

    purge_expired_incidents()

    # Generate 8-character url-safe token ID
    inc_id = secrets.token_hex(4)
    fix = geocoder.lookup(req.lat, req.lon, baro_floor=req.baro_floor)
    now = time.time()

    etype = (req.emergency_type or "general").lower()
    if etype not in ["medical", "fire", "collapse", "flood", "earthquake", "general"]:
        etype = "general"

    record = {
        "id": inc_id,
        "emergency_type": etype,
        "notes": req.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_at_epoch": now,
        "expires_at_epoch": now + EXPIRY_SECONDS,
        **fix,
    }
    incidents_db[inc_id] = record

    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/r/{inc_id}"

    return {
        "incident_id": inc_id,
        "share_url": share_url,
        "receiver_path": f"/r/{inc_id}",
        **record,
    }


@app.get("/api/hazards/earthquakes")
def get_earthquakes(lat: Optional[float] = None, lon: Optional[float] = None, radius_km: float = 1500.0):
    """Retrieve USGS live earthquakes and regional fault lines with MMI calculation."""
    return get_earthquake_hazard_data(center_lat=lat, center_lon=lon, max_radius_km=radius_km)


@app.get("/api/hazards/flood")
def get_flood_info(lat: Optional[float] = None, lon: Optional[float] = None):
    """Retrieve hydrological stations, floodplain zones, and inundation simulation parameters."""
    return get_flood_hazard_data(center_lat=lat, center_lon=lon)


@app.get("/api/hazards/flood/simulate")
def simulate_building_flood(
    dem_elevation_m: float,
    building_height_m: float,
    floors: int = 1,
    surge_water_level_m: float = 527.0
):
    """Calculate structure submersion depth, safe dry upper floors, and evacuation guidance."""
    return calculate_building_flood_impact(
        dem_ground_m=dem_elevation_m,
        building_height_m=building_height_m,
        floors=floors,
        surge_water_level_m=surge_water_level_m
    )


@app.get("/api/dem/elevation")
def get_dem_point(lat: float, lon: float):
    """Query ground elevation in meters above sea level from AWS Open Data Terrarium DEM."""
    elev = get_dem_elevation(lat, lon)
    return {
        "lat": lat,
        "lon": lon,
        "elevation_m": elev,
        "source": "AWS Open Data Terrarium DEM (30m/10m resolution)",
        "unit": "meters above sea level (MSL)"
    }


@app.get("/api/sos/active")
def list_active_sos():
    """Return active unexpired incidents for live map pins (zero PII beyond coords/floor)."""
    purge_expired_incidents()
    now = time.time()
    results = []
    for inc_id, item in incidents_db.items():
        age_min = round((now - item["created_at_epoch"]) / 60.0, 1)
        results.append({
            "id": inc_id,
            "lat": item["lat"],
            "lon": item["lon"],
            "emergency_type": item.get("emergency_type", "general"),
            "address": item["address"],
            "block_id": item["block_id"],
            "structure_id": item["structure_id"],
            "est_floor": item["est_floor"],
            "floors": item["floors"],
            "height_m": item["height_m"],
            "dem_elevation_m": item.get("dem_elevation_m"),
            "roof_elevation_m": item.get("roof_elevation_m"),
            "floor_elevation_m": item.get("floor_elevation_m"),
            "vuln_class": item["vuln_class"],
            "inside": item["inside"],
            "created_at": item["created_at"],
            "age_minutes": age_min,
            "recency": "critical" if age_min < 15 else ("recent" if age_min < 60 else "aged"),
        })

    # Newest incidents first
    results.sort(key=lambda x: x["age_minutes"])
    return {"count": len(results), "incidents": results}


@app.get("/api/sos/{incident_id}")
def get_sos(incident_id: str):
    purge_expired_incidents()
    if incident_id not in incidents_db:
        raise HTTPException(status_code=404, detail="Incident not found or expired (24h limit)")
    return incidents_db[incident_id]


@app.get("/r/{incident_id}")
def rescuer_page(incident_id: str):
    purge_expired_incidents()
    receiver_path = getattr(app.state, "web_dir", DEFAULT_WEB_DIR) / "receiver.html"
    if receiver_path.exists():
        return FileResponse(receiver_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Receiver template not found")


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Run TerraTwin SOS FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR, help="Path to demo_tiles directory")
    parser.add_argument("--web-dir", type=Path, default=DEFAULT_WEB_DIR, help="Path to demo/ static directory")
    parser.add_argument("--no-seed", action="store_true", help="Do not pre-seed demo incidents")
    args = parser.parse_args()

    app.state.demo_dir = args.demo_dir
    app.state.web_dir = args.web_dir
    app.state.no_seed = args.no_seed

    # Ensure static directory exists
    args.web_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting TerraTwin SOS on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
