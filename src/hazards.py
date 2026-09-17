"""
TerraTwin SOS — Multi-Hazard Engine (Earthquake & Flood)

Provides:
  1. Live USGS real-time seismic feed integration + regional tectonic fault lines.
  2. Earthquake ground motion estimation (epicenter distance, MMI intensity, collapse risk).
  3. Hydrological monitoring stations (Soan River / Rawal Basin & Las Vegas Wash CCRFCD).
  4. 3D Flood Inundation Simulator engine with dynamic building submersion calculations.
"""

import json
import math
import time
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# In-memory cache for USGS earthquake feed
_QUAKE_CACHE = {
    "timestamp": 0.0,
    "data": None,
    "ttl": 300.0,  # 5 minutes cache
}

USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

# Tectonic Fault Lines GeoJSON (Islamabad & Las Vegas)
FAULT_LINES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        # Islamabad - Rawalpindi Faults
        {
            "type": "Feature",
            "properties": {
                "id": "fault_mbt_margalla",
                "name": "Main Boundary Thrust (MBT) - Margalla Segment",
                "region": "Islamabad Capital Territory",
                "type": "Thrust Fault",
                "slip_rate_mm_yr": 15.0,
                "seismic_risk": "High (Capable of M7.0+)",
                "color": "#ef4444",
                "dashArray": "6, 4"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [72.880, 33.795],
                    [72.960, 33.770],
                    [73.025, 33.745],
                    [73.110, 33.730],
                    [73.190, 33.715],
                    [73.280, 33.690],
                    [73.350, 33.660]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": "fault_rawat",
                "name": "Rawat Thrust Fault (IST Campus Adjacent)",
                "region": "Islamabad / Rawalpindi",
                "type": "Reverse Thrust Fault",
                "slip_rate_mm_yr": 4.5,
                "seismic_risk": "Moderate-High (Adjacent to Expressway & Soan Basin)",
                "color": "#f97316",
                "dashArray": "8, 3"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [73.080, 33.590],
                    [73.125, 33.555],
                    [73.175, 33.525],
                    [73.220, 33.490],
                    [73.265, 33.450],
                    [73.310, 33.410]
                ]
            }
        },
        # Las Vegas Valley Fault System
        {
            "type": "Feature",
            "properties": {
                "id": "fault_lv_decatur",
                "name": "Decatur Fault Zone",
                "region": "Las Vegas Valley, NV",
                "type": "Normal Fault (Quaternary)",
                "slip_rate_mm_yr": 0.2,
                "seismic_risk": "Moderate (Scarp formation, ground fissure hazard)",
                "color": "#ef4444",
                "dashArray": "6, 4"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-115.228, 36.270],
                    [-115.222, 36.240],
                    [-115.215, 36.210],
                    [-115.208, 36.175],
                    [-115.200, 36.140]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": "fault_lv_eglington",
                "name": "Eglington Fault Scarp",
                "region": "Las Vegas Valley, NV",
                "type": "Normal Fault (Quaternary)",
                "slip_rate_mm_yr": 0.15,
                "seismic_risk": "Moderate (Structural differential settlement)",
                "color": "#f97316",
                "dashArray": "8, 3"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-115.185, 36.255],
                    [-115.170, 36.220],
                    [-115.155, 36.185],
                    [-115.145, 36.150]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": "fault_lv_west_charleston",
                "name": "West Charleston Fault Section",
                "region": "Las Vegas Valley, NV",
                "type": "Normal Fault",
                "slip_rate_mm_yr": 0.1,
                "seismic_risk": "Low-Moderate",
                "color": "#eab308",
                "dashArray": "5, 5"
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [-115.295, 36.185],
                    [-115.265, 36.160],
                    [-115.240, 36.135],
                    [-115.225, 36.110]
                ]
            }
        }
    ]
}

# Regional baseline seismic events (Potohar/Margalla & Nevada Intermountain)
REGIONAL_HISTORIC_EVENTS = [
    {
        "id": "reg_isb_01",
        "properties": {
            "title": "M 5.4 - 24 km N of Islamabad (Margalla Foothills)",
            "mag": 5.4,
            "place": "24 km N of Islamabad, Pakistan",
            "time": int(time.time() * 1000) - 7200000,
            "updated": int(time.time() * 1000) - 3600000,
            "url": "https://earthquake.usgs.gov/",
            "detail": "Margalla Thrust activation",
            "felt": 420,
            "cdi": 5.8,
            "mmi": 5.6,
            "alert": "yellow",
            "status": "reviewed",
            "tsunami": 0,
            "sig": 480,
            "type": "earthquake"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [73.055, 33.785, 12.4]
        }
    },
    {
        "id": "reg_isb_02",
        "properties": {
            "title": "M 4.2 - 12 km SE of Rawalpindi (Rawat Fault Zone)",
            "mag": 4.2,
            "place": "12 km SE of Rawalpindi, Pakistan",
            "time": int(time.time() * 1000) - 28800000,
            "updated": int(time.time() * 1000) - 14400000,
            "url": "https://earthquake.usgs.gov/",
            "detail": "Shallow crustal strike-slip",
            "felt": 95,
            "cdi": 4.2,
            "mmi": 4.1,
            "alert": "green",
            "status": "reviewed",
            "tsunami": 0,
            "sig": 270,
            "type": "earthquake"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [73.180, 33.515, 8.1]
        }
    },
    {
        "id": "reg_nv_01",
        "properties": {
            "title": "M 3.8 - 18 km NW of Las Vegas (Cheyenne Fault Trace)",
            "mag": 3.8,
            "place": "18 km NW of Las Vegas, NV",
            "time": int(time.time() * 1000) - 18000000,
            "updated": int(time.time() * 1000) - 7200000,
            "url": "https://earthquake.usgs.gov/",
            "detail": "Basin & Range extensional event",
            "felt": 64,
            "cdi": 3.5,
            "mmi": 3.6,
            "alert": "green",
            "status": "reviewed",
            "tsunami": 0,
            "sig": 220,
            "type": "earthquake"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [-115.240, 36.230, 9.2]
        }
    }
]

# Hydrological Stations
HYDRO_STATIONS = [
    {
        "id": "station_soan_ist",
        "name": "Soan River Basin - IST Expressway Hydrological Gauge",
        "region": "Islamabad / Rawalpindi",
        "lat": 33.5215,
        "lon": 73.1685,
        "elevation_datum_m": 510.5,
        "current_stage_m": 513.2,
        "normal_stage_m": 511.0,
        "warning_stage_m": 514.0,
        "flood_stage_m": 516.5,
        "discharge_m3_s": 420.5,
        "trend": "RISING (Monsoon Runoff Catchment)",
        "status": "WARNING",
        "upstream_reservoirs": ["Rawal Dam Spillway: 2 Gates Open (1,200 cfs)"],
        "critical_infrastructure": "Islamabad Expressway Bridge, IST Access Causeway"
    },
    {
        "id": "station_lv_cheyenne",
        "name": "CCRFCD West Cheyenne Wash Detention Basin #4",
        "region": "Las Vegas Valley, NV",
        "lat": 36.2185,
        "lon": -115.2150,
        "elevation_datum_m": 688.0,
        "current_stage_m": 689.1,
        "normal_stage_m": 688.0,
        "warning_stage_m": 691.5,
        "flood_stage_m": 694.0,
        "discharge_m3_s": 35.0,
        "trend": "STABLE",
        "status": "NORMAL",
        "upstream_reservoirs": ["Gowan Detention System"],
        "critical_infrastructure": "Cheyenne Ave Culverts, N. Decatur Outfall"
    }
]

# Flood Risk GeoJSON Polygons (Floodplain Extents)
FLOOD_ZONES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        # Islamabad - Soan River Corridor & Low-lying terraces
        {
            "type": "Feature",
            "properties": {
                "id": "floodzone_soan_100yr",
                "name": "Soan River 100-Year Floodplain (Islamabad Expressway)",
                "zone_type": "High Hazard / Inundation Zone A",
                "base_elevation_m": 515.0,
                "surge_depth_m": 4.5,
                "color": "#0284c7",
                "fillOpacity": 0.35
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.140, 33.535],
                    [73.165, 33.528],
                    [73.195, 33.510],
                    [73.230, 33.485],
                    [73.245, 33.475],
                    [73.235, 33.468],
                    [73.190, 33.495],
                    [73.155, 33.515],
                    [73.130, 33.528],
                    [73.140, 33.535]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "id": "floodzone_soan_flash",
                "name": "IST Low-Lying Drainage Basin",
                "zone_type": "Rapid Inundation Depressional Area",
                "base_elevation_m": 528.5,
                "surge_depth_m": 1.8,
                "color": "#38bdf8",
                "fillOpacity": 0.45
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [73.172, 33.523],
                    [73.181, 33.522],
                    [73.184, 33.517],
                    [73.176, 33.515],
                    [73.170, 33.519],
                    [73.172, 33.523]
                ]]
            }
        },
        # Las Vegas - West Cheyenne / Gowan Wash Channel
        {
            "type": "Feature",
            "properties": {
                "id": "floodzone_lv_wash",
                "name": "West Cheyenne Regional Wash Inundation Channel",
                "zone_type": "Flash Flood Rapid Confluence Corridor",
                "base_elevation_m": 692.0,
                "surge_depth_m": 2.2,
                "color": "#0284c7",
                "fillOpacity": 0.35
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-115.228, 36.219],
                    [-115.205, 36.216],
                    [-115.185, 36.208],
                    [-115.165, 36.198],
                    [-115.168, 36.192],
                    [-115.190, 36.202],
                    [-115.210, 36.210],
                    [-115.230, 36.213],
                    [-115.228, 36.219]
                ]]
            }
        }
    ]
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points in kilometers."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def estimate_mmi(mag: float, depth_km: float, dist_km: float) -> Dict[str, Any]:
    """
    Estimate Modified Mercalli Intensity (MMI) and Peak Ground Acceleration (PGA)
    using standard empirical ground-motion attenuation.
    """
    hypo_dist = math.sqrt(dist_km ** 2 + max(depth_km, 5.0) ** 2)
    # Empirical Atkinson-Kaka relationship
    raw_mmi = 1.15 * mag - 3.25 * math.log10(max(hypo_dist, 5.0)) + 4.2
    mmi = max(1.0, min(10.0, round(raw_mmi, 1)))

    if mmi < 3.0:
        label = "I-II: Instrumental / Weak"
        color = "#10b981"
        alert = "green"
        desc = "Imperceptible or felt by very few on upper floors. No structural damage."
        stairwell_risk = "Negligible"
    elif mmi < 4.5:
        label = "III-IV: Light to Moderate"
        color = "#84cc16"
        alert = "green"
        desc = "Noticeable indoor vibrations like passing truck. Hanging objects swing."
        stairwell_risk = "Minimal - Clear for use"
    elif mmi < 6.0:
        label = "V: Strong Shaking"
        color = "#eab308"
        alert = "yellow"
        desc = "Felt by nearly all. Windows rattle, glassware breaks. Minor non-structural cracks."
        stairwell_risk = "Low - Exercise caution"
    elif mmi < 7.5:
        label = "VI-VII: Very Strong (Damage Possible)"
        color = "#f97316"
        alert = "orange"
        desc = "Furniture shifted, plaster falls. Moderate damage to vulnerable unreinforced masonry."
        stairwell_risk = "Elevated - Inspect stair treads and emergency exits"
    else:
        label = "VIII-X: Destructive to Violent"
        color = "#ef4444"
        alert = "red"
        desc = "Considerable damage in ordinary buildings with partial collapse. Severe chimney/parapet failure."
        stairwell_risk = "CRITICAL - Stairwell shear collapse risk. Evacuate via verified structural paths"

    return {
        "mmi": mmi,
        "label": label,
        "color": color,
        "alert": alert,
        "description": desc,
        "stairwell_risk": stairwell_risk,
        "hypo_dist_km": round(hypo_dist, 1)
    }


def fetch_usgs_live_earthquakes() -> List[Dict[str, Any]]:
    """Fetch live 2.5+ earthquake GeoJSON from USGS with caching."""
    now = time.time()
    if _QUAKE_CACHE["data"] is not None and (now - _QUAKE_CACHE["timestamp"]) < _QUAKE_CACHE["ttl"]:
        return _QUAKE_CACHE["data"]

    try:
        req = urllib.request.Request(
            USGS_FEED_URL,
            headers={"User-Agent": "TerraTwin-SOS-DigitalTwin/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            features = data.get("features", [])
            _QUAKE_CACHE["data"] = features
            _QUAKE_CACHE["timestamp"] = now
            return features
    except Exception as e:
        print(f"Warning: USGS feed fetch failed ({e}). Using regional baseline events.")
        if _QUAKE_CACHE["data"] is not None:
            return _QUAKE_CACHE["data"]
        return []


def get_earthquake_hazard_data(
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None,
    max_radius_km: float = 1500.0
) -> Dict[str, Any]:
    """
    Combine live USGS feed, regional Potohar/Nevada events, tectonic fault lines,
    and impact assessments relative to the requested coordinate center.
    """
    live_features = fetch_usgs_live_earthquakes()

    all_features = list(live_features) + list(REGIONAL_HISTORIC_EVENTS)
    # Deduplicate by ID
    seen_ids = set()
    unique_events = []
    for feat in all_features:
        fid = feat.get("id")
        if fid not in seen_ids:
            seen_ids.add(fid)
            unique_events.append(feat)

    processed_events = []
    for feat in unique_events:
        coords = feat.get("geometry", {}).get("coordinates", [0, 0, 0])
        lon, lat = coords[0], coords[1]
        depth_km = coords[2] if len(coords) > 2 else 10.0
        props = feat.get("properties", {})
        mag = float(props.get("mag") or 3.0)

        dist_km = None
        mmi_info = None
        if center_lat is not None and center_lon is not None:
            dist_km = round(haversine_km(center_lat, center_lon, lat, lon), 1)
            if dist_km > max_radius_km and len(processed_events) > 10:
                continue
            mmi_info = estimate_mmi(mag, depth_km, dist_km)
        else:
            mmi_info = estimate_mmi(mag, depth_km, 10.0)

        impact_radius_km = round(10 ** (0.43 * mag - 0.27), 1)

        processed_events.append({
            "id": feat.get("id"),
            "title": props.get("title"),
            "mag": mag,
            "depth_km": depth_km,
            "lat": lat,
            "lon": lon,
            "time_epoch": props.get("time"),
            "time_iso": datetime.fromtimestamp(props.get("time", 0) / 1000.0, tz=timezone.utc).isoformat() if props.get("time") else None,
            "place": props.get("place"),
            "distance_km": dist_km,
            "impact_radius_km": impact_radius_km,
            "mmi": mmi_info,
            "url": props.get("url")
        })

    if center_lat is not None and center_lon is not None:
        processed_events.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 99999))
    else:
        processed_events.sort(key=lambda x: x["mag"], reverse=True)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "center": {"lat": center_lat, "lon": center_lon} if center_lat else None,
        "events_count": len(processed_events),
        "earthquakes": processed_events[:50],
        "fault_lines": FAULT_LINES_GEOJSON
    }


def get_flood_hazard_data(
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Return hydrological gauging stations, floodplain risk zones,
    and 3D Flood Inundation Simulator configuration.
    """
    is_islamabad = False
    if center_lat is not None and center_lon is not None:
        if 33.0 <= center_lat <= 34.0 and 72.5 <= center_lon <= 73.5:
            is_islamabad = True

    active_region = "Islamabad (Soan Basin)" if is_islamabad else "Las Vegas Valley (Sector 7)"
    base_datum_m = 525.0 if is_islamabad else 690.0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_region": active_region,
        "base_datum_m": base_datum_m,
        "simulator": {
            "surge_min_m": 0.0,
            "surge_max_m": 10.0,
            "default_surge_m": 2.0,
            "presets": [
                {
                    "id": "monsoon_flash",
                    "label": "Monsoon Flash Surge (+1.5m)",
                    "surge_m": 1.5,
                    "description": "Submerges basements, ground drainage channels, and low-lying perimeter roads."
                },
                {
                    "id": "dam_spillway",
                    "label": "Spillway / High Basin Surge (+3.5m)",
                    "surge_m": 3.5,
                    "description": "Ground floors submerged up to 1.5m. Rapid current; occupants must reach Floor 2+."
                },
                {
                    "id": "catastrophic_deluge",
                    "label": "100-Year Catastrophic Deluge (+6.0m)",
                    "surge_m": 6.0,
                    "description": "Complete ground and 2nd-floor submersion. Rooftop evacuation and amphibious rescue essential."
                }
            ]
        },
        "stations": HYDRO_STATIONS,
        "flood_zones": FLOOD_ZONES_GEOJSON
    }


def calculate_building_flood_impact(
    dem_ground_m: float,
    building_height_m: float,
    floors: int,
    surge_water_level_m: float
) -> Dict[str, Any]:
    """
    Evaluate flood submersion for a building based on its DEM ground elevation,
    number of floors, and current flood surge water level.
    """
    water_depth_at_ground = round(surge_water_level_m - dem_ground_m, 2)
    floor_height = round(building_height_m / max(floors, 1), 2)

    if water_depth_at_ground <= 0:
        return {
            "status": "SAFE_DRY",
            "water_depth_m": 0.0,
            "submerged_floors": 0,
            "safe_floors": list(range(1, floors + 1)),
            "evacuation_advice": "Ground entry completely dry. Normal egress available."
        }

    # Count submerged floors
    submerged_floors = 0
    safe_floors = []
    for f in range(1, floors + 1):
        floor_elev = dem_ground_m + ((f - 1) * floor_height)
        if surge_water_level_m > floor_elev:
            submerged_floors += 1
        else:
            safe_floors.append(f)

    if len(safe_floors) > 0:
        advice = f"Ground inundated by {water_depth_at_ground:.1f}m. Evacuate occupants vertically to Floor {safe_floors[0]}+."
        status = "PARTIALLY_SUBMERGED"
    else:
        advice = f"Building fully submerged ({water_depth_at_ground:.1f}m water). Immediate rooftop helicopter/boat rescue required!"
        status = "COMPLETELY_SUBMERGED"

    return {
        "status": status,
        "water_depth_m": water_depth_at_ground,
        "submerged_floors": submerged_floors,
        "safe_floors": safe_floors,
        "evacuation_advice": advice
    }
