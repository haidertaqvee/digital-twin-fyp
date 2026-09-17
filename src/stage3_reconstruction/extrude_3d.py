"""
Stage 3 — Extrude 2D building polygons with heights into full 3D meshes (Wavefront OBJ + MTL).

Converts georeferenced building polygons (EPSG:4326) into metric 3D meshes (EPSG:32611):
  - Extrudes vertical wall quads between ground (z=0) and roof (z=height_m).
  - Triangulates polygon roofs using geometric decomposition.
  - Assigns materials by vulnerability class (Low/Medium/High).
  - Can be imported into Unity, Blender, or WebGL/Three.js viewers.

Usage:
    python src/stage3_reconstruction/extrude_3d.py --tile AOI_2_Vegas_img4174
    python src/stage3_reconstruction/extrude_3d.py --all
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import triangulate

DEFAULT_DEMO_DIR = Path("E:/digital-twin-fyp/data/processed/demo_tiles")
DEFAULT_OUT_DIR = Path("E:/digital-twin-fyp/data/processed/stage3_3d")
DEFAULT_TILE = "AOI_2_Vegas_img4174"
METRIC_CRS = "EPSG:32611"

# Material color definitions
MTL_CONTENT = """# TerraTwin SOS Material Library
newmtl Mat_Low
Ka 0.06 0.72 0.50
Kd 0.06 0.72 0.50
Ks 0.20 0.20 0.20
Ns 20.0
d 1.0

newmtl Mat_Medium
Ka 0.96 0.62 0.04
Kd 0.96 0.62 0.04
Ks 0.20 0.20 0.20
Ns 20.0
d 1.0

newmtl Mat_High
Ka 0.94 0.27 0.27
Kd 0.94 0.27 0.27
Ks 0.20 0.20 0.20
Ns 20.0
d 1.0

newmtl Mat_Roof
Ka 0.20 0.25 0.33
Kd 0.25 0.30 0.40
Ks 0.10 0.10 0.10
Ns 10.0
d 1.0

newmtl Mat_FloorSlab
Ka 0.12 0.15 0.20
Kd 0.18 0.22 0.28
Ks 0.15 0.15 0.15
Ns 15.0
d 1.0
"""


def parse_args():
    p = argparse.ArgumentParser(description="Extrude building polygons into 3D OBJ meshes")
    p.add_argument("--tile", default=DEFAULT_TILE, help="Tile name (e.g. AOI_2_Vegas_img4174)")
    p.add_argument("--all", action="store_true", help="Process all available demo tiles")
    p.add_argument("--demo-dir", type=Path, default=DEFAULT_DEMO_DIR)
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return p.parse_args()


def triangulate_polygon_roof(poly):
    """Return list of (p0, p1, p2) triangles inside the polygon."""
    try:
        raw_tris = triangulate(poly)
        valid_tris = [t for t in raw_tris if poly.contains(t.representative_point())]
        return valid_tris
    except Exception:
        # Fallback to simple triangle fan from vertex 0 if triangulation fails
        coords = list(poly.exterior.coords)[:-1]
        tris = []
        for i in range(1, len(coords) - 1):
            tris.append(Polygon([coords[0], coords[i], coords[i + 1]]))
        return tris


def extrude_tile_to_obj(tile_name, geojson_path, out_dir):
    gdf = gpd.read_file(geojson_path)
    if len(gdf) == 0:
        print(f"  {tile_name}: no features, skipping")
        return None

    gdf_m = gdf.to_crs(METRIC_CRS).copy()
    bounds = gdf_m.total_bounds  # minx, miny, maxx, maxy
    origin_x, origin_y = bounds[0], bounds[1]

    out_dir.mkdir(parents=True, exist_ok=True)
    obj_filename = f"{tile_name}_buildings.obj"
    mtl_filename = f"{tile_name}_buildings.mtl"
    obj_path = out_dir / obj_filename
    mtl_path = out_dir / mtl_filename

    # Write MTL
    mtl_path.write_text(MTL_CONTENT, encoding="utf-8")

    vertices = []  # list of (x, y, z)
    vertex_index = {}  # (x, y, z) -> 1-based index
    faces_by_mat = {
        "Mat_Low": [],
        "Mat_Medium": [],
        "Mat_High": [],
        "Mat_Roof": [],
        "Mat_FloorSlab": [],
    }

    def get_vert_id(x, y, z):
        key = (round(x, 3), round(y, 3), round(z, 3))
        if key not in vertex_index:
            vertices.append(key)
            vertex_index[key] = len(vertices)
        return vertex_index[key]

    for _, row in gdf_m.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue

        h = float(row.get("height_m", 3.0))
        num_floors = int(row.get("floors") or row.get("levels") or max(1, round(h / 3.0)))
        vclass = str(row.get("vuln_class", "low")).lower()
        wall_mat = "Mat_High" if vclass == "high" else ("Mat_Medium" if vclass == "medium" else "Mat_Low")

        # Handle Polygon and MultiPolygon
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)

        for poly in polys:
            ext_coords = list(poly.exterior.coords)[:-1]
            if len(ext_coords) < 3:
                continue

            n = len(ext_coords)
            floor_height = h / max(1, num_floors)
            roof_tris = triangulate_polygon_roof(poly)

            # Extrude distinct floor tiers with intermediate structural slabs
            for fl in range(num_floors):
                z_bot = fl * floor_height
                z_top = (fl + 1) * floor_height

                # 1. Floor Wall Quads
                for i in range(n):
                    p0 = ext_coords[i]
                    p1 = ext_coords[(i + 1) % n]

                    # Relative coordinates
                    x0, y0 = p0[0] - origin_x, p0[1] - origin_y
                    x1, y1 = p1[0] - origin_x, p1[1] - origin_y

                    # 4 vertices of the floor wall quad
                    v_b0 = get_vert_id(x0, y0, z_bot)
                    v_b1 = get_vert_id(x1, y1, z_bot)
                    v_r1 = get_vert_id(x1, y1, z_top)
                    v_r0 = get_vert_id(x0, y0, z_top)

                    # Two triangles per wall quad (CCW outward normal)
                    faces_by_mat[wall_mat].append((v_b0, v_b1, v_r1))
                    faces_by_mat[wall_mat].append((v_b0, v_r1, v_r0))

                # 2. Intermediate Floor Slabs or Roof Cap
                mat_key = "Mat_Roof" if (fl == num_floors - 1) else "Mat_FloorSlab"
                for tri in roof_tris:
                    t_coords = list(tri.exterior.coords)[:-1]
                    if len(t_coords) == 3:
                        vt0 = get_vert_id(t_coords[0][0] - origin_x, t_coords[0][1] - origin_y, z_top)
                        vt1 = get_vert_id(t_coords[1][0] - origin_x, t_coords[1][1] - origin_y, z_top)
                        vt2 = get_vert_id(t_coords[2][0] - origin_x, t_coords[2][1] - origin_y, z_top)
                        faces_by_mat[mat_key].append((vt0, vt1, vt2))

    # Write OBJ File
    with open(obj_path, "w", encoding="utf-8") as f:
        f.write(f"# TerraTwin SOS 3D City Twin Mesh\n")
        f.write(f"# Tile: {tile_name}, Buildings: {len(gdf_m)}\n")
        f.write(f"mtllib {mtl_filename}\n\n")

        # Vertices (Z is UP in Wavefront OBJ)
        for vx, vy, vz in vertices:
            f.write(f"v {vx:.3f} {vy:.3f} {vz:.3f}\n")
        f.write("\n")

        # Faces grouped by material
        for mat_name, f_list in faces_by_mat.items():
            if f_list:
                f.write(f"usemtl {mat_name}\n")
                for f0, f1, f2 in f_list:
                    f.write(f"f {f0} {f1} {f2}\n")
                f.write("\n")

    total_faces = sum(len(fl) for fl in faces_by_mat.values())
    print(f"  {tile_name}: wrote {obj_filename} ({len(vertices)} vertices, {total_faces} faces, {len(gdf_m)} structures)")
    return obj_path


def main():
    args = parse_args()
    if args.all:
        files = sorted(args.demo_dir.glob("tile_*.geojson"))
        print(f"Extruding 3D meshes for {len(files)} tiles...")
        count = 0
        for p in files:
            tname = p.stem.replace("tile_", "")
            res = extrude_tile_to_obj(tname, p, args.out_dir)
            if res:
                count += 1
        print(f"Stage 3 extrusion complete: {count} OBJ meshes generated in {args.out_dir}")
    else:
        p = args.demo_dir / f"tile_{args.tile}.geojson"
        if not p.exists():
            raise SystemExit(f"GeoJSON not found: {p}")
        print(f"Extruding 3D mesh for {args.tile} ...")
        res = extrude_tile_to_obj(args.tile, p, args.out_dir)
        print(f"Stage 3 extrusion complete: {res}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
