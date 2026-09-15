"""
Stage 2 — reverse geocoder: (lat, lon, baro_floor?) -> nearest addressed building.

Loads every data/processed/demo_tiles/tile_*.geojson into one in-memory spatial
index at import/startup. Used by the SOS backend (server.py) and testable standalone:

    python src/stage2_enrichment/reverse_geocode.py --lat 36.1699 --lon -115.1398
    python src/stage2_enrichment/reverse_geocode.py --lat 36.1 --lon -115.2 --baro-floor 2

Returns JSON: address, block_id, structure_id, height_m, floors, est_floor,
vuln_class, vuln_score, distance_m, bearing, inside (bool), tile. When the point
falls outside every footprint, inside=false and the address reads
"~Xm <dir> of <nearest address>" (outdoors case) — never a fabricated indoor fix.

Floor estimate: baro_floor is the phone's barometer-derived floor (1-based) when
available. est_floor = min(baro_floor, floors), or "unknown" when absent.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np

DEFAULT_DEMO_DIR = Path("E:/digital-twin-fyp/data/processed/demo_tiles")
METRIC_CRS = "EPSG:32611"
LEVEL_HEIGHT_M = 3.0

_COMPASS = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]


def bearing_label(dx, dy):
    ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return _COMPASS[int((ang + 22.5) // 45) % 8]


class ReverseGeocoder:
    def __init__(self, demo_dir=DEFAULT_DEMO_DIR):
        files = sorted(Path(demo_dir).glob("tile_*.geojson"))
        if not files:
            raise FileNotFoundError(
                f"No tile_*.geojson in {demo_dir}. Run generate_addresses.py first."
            )
        frames = []
        for f in files:
            g = gpd.read_file(f)
            if len(g):
                frames.append(g)
        if not frames:
            raise ValueError(f"All tile files in {demo_dir} are empty.")
        self.gdf = gpd.GeoDataFrame(__import__("pandas").concat(frames, ignore_index=True),
                                    crs="EPSG:4326")
        self.m = self.gdf.to_crs(METRIC_CRS)
        self.sindex = self.m.sindex

    def lookup(self, lat, lon, baro_floor=None):
        from shapely.geometry import Point

        pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(METRIC_CRS).iloc[0]
        x, y = pt.x, pt.y

        # Inside a footprint?
        hits = list(self.sindex.query(pt, predicate="intersects"))
        inside = len(hits) > 0
        if inside:
            # Smallest containing footprint wins (nested polygons).
            areas = [(self.m.geometry.iloc[i].area, i) for i in hits]
            idx = min(areas)[1]
            dist = 0.0
            direction = None
        else:
            _, tree_idx = self.sindex.nearest(pt)
            idx = int(np.asarray(tree_idx).ravel()[0])
            geom = self.m.geometry.iloc[idx]
            proj = geom.exterior.interpolate(geom.exterior.project(pt))
            dx, dy = x - proj.x, y - proj.y
            dist = float(math.hypot(dx, dy))
            direction = bearing_label(dx, dy)

        row = self.gdf.iloc[idx]
        floors = int(row.get("floors", row.get("levels", 1)))
        if baro_floor is not None:
            try:
                bf = max(1, int(baro_floor))
            except (TypeError, ValueError):
                bf = None
            est_floor = min(bf, floors) if bf else "unknown"
        else:
            est_floor = "unknown"

        address = str(row.get("address", ""))
        if not inside:
            address = f"~{dist:.0f}m {direction} of {address}"

        return {
            "address": address,
            "block_id": str(row.get("block_id", "")),
            "structure_id": str(row.get("structure_id", "")),
            "tile": str(row.get("tile", "")),
            "height_m": float(row.get("height_m", floors * LEVEL_HEIGHT_M)),
            "floors": floors,
            "est_floor": est_floor,
            "vuln_class": str(row.get("vuln_class", "unknown")),
            "vuln_score": float(row.get("vuln_score", -1)) if row.get("vuln_score") is not None else None,
            "distance_m": round(dist, 1),
            "bearing": direction,
            "inside": inside,
            "lat": lat,
            "lon": lon,
        }


def parse_args():
    p = argparse.ArgumentParser(description="Reverse-geocode a GPS fix to the nearest addressed building")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--baro-floor", type=int, default=None)
    p.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR)
    return p.parse_args()


def main():
    args = parse_args()
    print(json.dumps(ReverseGeocoder(args.demo_dir).lookup(args.lat, args.lon, args.baro_floor), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
