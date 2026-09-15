"""
Stage 2 — generate human-readable addresses for buildings ("Block 7-B, Structure 142").

Reads the committed prediction vectors (EPSG:4326) and writes NEW per-tile files
under data/processed/demo_tiles/ — never touches data/processed/test/vectors/.

Method per tile (all metric ops in EPSG:32611):
  1. DBSCAN on centroids (eps ~30 m, min_samples=1) -> blocks.
  2. Block IDs "7-A", "7-B", ... (sector 7 fixed for the demo zone; letters in
     north-to-south, west-to-east block order). Unique across tiles via `tile`.
     Default eps 20 m: on these dense Vegas tiles the median nearest neighbour
     is ~13 m, so eps=20 separates street blocks while eps=30 merges everything.
  3. Structures numbered in reading order (north first, then west->east) within
     each block: structure_id like "7-B-03".
  4. Nearest OSM road via osmnx (drive network, cached to disk). If the download
     is blocked, degrades gracefully: road_name=None, dist_road_m still computed
     against nothing -> None, address omits the road clause. NEVER stalls.

Output properties per building: address, block_id, structure_id, height_m,
floors (= levels), area_m2, road_name, dist_road_m, tile.

Usage:
    python src/stage2_enrichment/generate_addresses.py --top-n 20
    python src/stage2_enrichment/generate_addresses.py --tiles AOI_2_Vegas_img101
    python src/stage2_enrichment/generate_addresses.py --top-n 2 --no-osm
"""

import argparse
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from heights import LEVEL_HEIGHT_M  # noqa: F401  (documents height provenance)

DEFAULT_INPUT = Path("E:/digital-twin-fyp/data/processed/test/vectors/buildings_predictions.geojson")
DEFAULT_OUT_DIR = Path("E:/digital-twin-fyp/data/processed/demo_tiles")
DEFAULT_ROADS_CACHE = Path("E:/digital-twin-fyp/data/processed/demo_tiles/_roads_cache.geojson")

SECTOR = "7"
METRIC_CRS = "EPSG:32611"


def parse_args():
    p = argparse.ArgumentParser(description="Cluster buildings into blocks and assign addresses")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--top-n", type=int, default=20,
                   help="Process the N densest tiles by polygon count. 0 with --tiles.")
    p.add_argument("--tiles", nargs="*", default=None,
                   help="Explicit tile names (e.g. AOI_2_Vegas_img101). Overrides --top-n.")
    p.add_argument("--eps", type=float, default=30.0, help="DBSCAN eps in metres.")
    p.add_argument("--no-osm", action="store_true", help="Skip OSM road lookup entirely.")
    p.add_argument("--roads-cache", type=Path, default=DEFAULT_ROADS_CACHE)
    p.add_argument("--sector", default=SECTOR)
    return p.parse_args()


def fetch_roads(total_bounds_4326, cache_path, no_osm=False):
    """Return road edges GeoDataFrame (EPSG:4326) or None. Never raises on network issues."""
    if cache_path.exists():
        try:
            roads = gpd.read_file(cache_path)
            print(f"  roads: loaded {len(roads)} cached edges from {cache_path.name}")
            return roads if len(roads) else None
        except Exception as e:
            print(f"  roads: cache unreadable ({e}), refetching")
    if no_osm:
        print("  roads: --no-osm, skipping")
        return None
    try:
        import osmnx as ox
        west, south, east, north = total_bounds_4326
        pad = 0.002
        bbox = (west - pad, south - pad, east + pad, north + pad)
        print(f"  roads: downloading OSM drive network bbox={tuple(round(v, 4) for v in bbox)} ...")
        G = ox.graph_from_bbox(bbox, network_type="drive", simplify=True)
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        edges = edges.reset_index(drop=True)[["geometry", "name"] if "name" in edges.columns else ["geometry"]]
        if "name" not in edges.columns:
            edges["name"] = None
        edges = edges.to_crs("EPSG:4326")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        edges.to_file(cache_path, driver="GeoJSON")
        print(f"  roads: fetched {len(edges)} edges, cached")
        return edges
    except Exception as e:
        print(f"  roads: OSM unavailable ({type(e).__name__}: {str(e)[:120]}), continuing without roads")
        return None


def compass(dx, dy):
    """dx=east, dy=north in metres -> compass label."""
    ang = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
    labels = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    return labels[int((ang + 22.5) // 45) % 8]


def _first_name(name):
    """osmnx road names arrive in several shapes; return one plain string or None.

    In-memory edges carry real lists (sometimes numpy arrays after a GeoJSON
    round-trip); the cached file carries their stringified form. geojson also
    turns missing values into None or NaN.
    """
    if name is None:
        return None
    if isinstance(name, str):
        s = name.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                import ast
                parsed = ast.literal_eval(s)
                return _first_name(parsed)
            except (ValueError, SyntaxError):
                pass
        return s or None
    if isinstance(name, (list, tuple, np.ndarray)):
        flat = list(name)
        return _first_name(flat[0]) if flat else None
    try:
        if isinstance(name, float) and np.isnan(name):
            return None
    except TypeError:
        pass
    return str(name)


def assign_blocks(gdf_m, eps):
    """DBSCAN on centroids -> cluster labels. min_samples=1 so isolates are their own block."""
    from sklearn.cluster import DBSCAN

    cents = np.column_stack([gdf_m.geometry.centroid.x, gdf_m.geometry.centroid.y])
    if len(cents) == 0:
        return np.array([], dtype=int)
    if len(cents) == 1:
        return np.array([0])
    return DBSCAN(eps=eps, min_samples=1).fit_predict(cents)


def process_tile(tile_gdf, tile_name, tile_idx, roads_m, sector, eps):
    gdf_m = tile_gdf.to_crs(METRIC_CRS).copy()
    labels = assign_blocks(gdf_m, eps)
    gdf_m["_cluster"] = labels

    # Order blocks north->south, west->east for stable lettering.
    block_order = (
        gdf_m.groupby("_cluster")[["geometry"]]
        .apply(lambda d: (d.geometry.centroid.y.mean(), d.geometry.centroid.x.mean()))
    )
    ordered = sorted(block_order.index, key=lambda c: (-block_order[c][0], block_order[c][1]))
    letter_of = {c: chr(ord("A") + i) for i, c in enumerate(ordered)}

    gdf_m["block_id"] = [f"{sector}-{letter_of[c]}" for c in gdf_m["_cluster"]]

    # Reading order within block: north first, then west->east.
    gdf_m["_cy"] = gdf_m.geometry.centroid.y
    gdf_m["_cx"] = gdf_m.geometry.centroid.x
    gdf_m = gdf_m.sort_values(["block_id", "_cy", "_cx"], ascending=[True, False, True])
    gdf_m["structure_id"] = [
        f"{b}-{i + 1:02d}" for b, i in zip(gdf_m["block_id"], gdf_m.groupby("block_id").cumcount())
    ]

    # Nearest road per building.
    if roads_m is not None and len(roads_m):
        from shapely.geometry import Point

        sindex = roads_m.sindex
        road_names, road_dists, road_dirs = [], [], []
        for geom in gdf_m.geometry:
            c = geom.centroid
            # sindex.nearest returns (input_idx, tree_idx) rows; we want the tree match.
            _, tree_idx = sindex.nearest(Point(c.x, c.y))
            idx = int(np.asarray(tree_idx).ravel()[0])
            edge = roads_m.geometry.iloc[idx]
            proj = edge.interpolate(edge.project(c))
            dx, dy = c.x - proj.x, c.y - proj.y
            dist = float(np.hypot(dx, dy))
            name = roads_m["name"].iloc[idx] if "name" in roads_m.columns else None
            road_names.append(_first_name(name))
            road_dists.append(round(dist, 1))
            road_dirs.append(compass(dx, dy))
        gdf_m["road_name"] = road_names
        gdf_m["dist_road_m"] = road_dists
        gdf_m["_road_dir"] = road_dirs
    else:
        gdf_m["road_name"] = None
        gdf_m["dist_road_m"] = None
        gdf_m["_road_dir"] = None

    # Human address.
    addrs = []
    for _, r in gdf_m.iterrows():
        base = f"Block {r['block_id']}, Structure {r['structure_id'].split('-')[-1].lstrip('0') or '0'}"
        if r["road_name"] and r["dist_road_m"] is not None:
            base += f", {r['dist_road_m']:.0f}m {r['_road_dir']} of {r['road_name']}"
        addrs.append(base)
    gdf_m["address"] = addrs

    gdf_m["floors"] = gdf_m["levels"].astype(int)
    gdf_m["tile"] = tile_name

    keep = ["address", "block_id", "structure_id", "tile", "area_m2", "levels",
            "floors", "height_m", "road_name", "dist_road_m", "geometry"]
    return gdf_m[keep].to_crs("EPSG:4326")


def main():
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input vectors not found: {args.input}")

    gdf = gpd.read_file(args.input)
    if args.tiles:
        wanted = set(args.tiles)
        tiles = [t for t in sorted(gdf["tile"].unique()) if t in wanted]
        missing = wanted - set(tiles)
        if missing:
            print(f"  warning: tiles not in vectors: {sorted(missing)}")
    else:
        counts = gdf["tile"].value_counts()
        tiles = list(counts.head(args.top_n).index) if args.top_n else list(counts.index)
    if not tiles:
        raise SystemExit("No tiles selected.")
    print(f"Selected {len(tiles)} tiles: {', '.join(tiles[:5])}{'...' if len(tiles) > 5 else ''}")

    # One road fetch for the union bbox (cached); per-tile would hammer Overpass.
    sub = gdf[gdf["tile"].isin(tiles)]
    roads = fetch_roads(tuple(sub.total_bounds), args.roads_cache, no_osm=args.no_osm)
    roads_m = roads.to_crs(METRIC_CRS) if roads is not None else None

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, t in enumerate(tiles):
        tile_gdf = sub[sub["tile"] == t].copy()
        out = process_tile(tile_gdf, t, i, roads_m, args.sector, args.eps)
        out_path = args.out_dir / f"tile_{t}.geojson"
        out.to_file(out_path, driver="GeoJSON")
        n_blocks = out["block_id"].nunique()
        print(f"  wrote {out_path.name}: {len(out)} buildings, {n_blocks} blocks")
        manifest.append({"tile": t, "file": out_path.name, "buildings": len(out), "blocks": n_blocks})

    mp = args.out_dir / "_manifest.json"
    mp.write_text(json.dumps({"sector": args.sector, "eps_m": args.eps,
                              "roads": "osm-drive-cached" if roads_m is not None else "none-fallback",
                              "tiles": manifest}, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} tile files + {mp.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
