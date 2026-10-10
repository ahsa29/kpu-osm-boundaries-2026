#!/usr/bin/env python3
"""Clip Sumatera Utara's OSM administrative polygons to OSM land polygons.

The district relations around Nias include maritime jurisdiction. Those sea
areas must not be rendered as land on either map level. Run with the OSM land
polygon shapefile from https://osmdata.openstreetmap.de/data/land-polygons.html:

    python3 tools/repair_sumut_land.py data/2026-10-09 PATH/land_polygons.shp data/2026-10-10

Requires Shapely 2 and pyshp. The input version remains untouched.
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import shapefile
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


SUMUT = "ID_SU"


def count_coordinates(value):
    if len(value) >= 2 and isinstance(value[0], (int, float)):
        return 1
    return sum(count_coordinates(child) for child in value)


def polygonal(geometry):
    if geometry.is_empty:
        return geometry
    if isinstance(geometry, (Polygon, MultiPolygon)):
        return geometry
    if isinstance(geometry, GeometryCollection):
        parts = [part for part in geometry.geoms if isinstance(part, (Polygon, MultiPolygon)) and not part.is_empty]
        return unary_union(parts) if parts else Polygon()
    return Polygon()


def read_land_mask(shapefile_path, bbox):
    polygons = []
    with shapefile.Reader(str(shapefile_path)) as reader:
        for record in reader.iterShapes(bbox=bbox):
            if record is None:
                continue
            land = polygonal(make_valid(shape(record.__geo_interface__)))
            if not land.is_empty:
                polygons.append(land)
    if not polygons:
        raise ValueError("No OSM land polygons intersect Sumatera Utara")
    return unary_union(polygons)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Published, immutable source version directory")
    parser.add_argument("land_shapefile", type=Path, help="OSM land_polygons.shp")
    parser.add_argument("output", type=Path, help="New version directory")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output version already exists; never overwrite a published snapshot")

    national = json.loads((args.source / "MapNational.geojson").read_text(encoding="utf-8"))
    districts = json.loads((args.source / f"MapProvince_{SUMUT}.geojson").read_text(encoding="utf-8"))
    manifest = json.loads((args.source / "MapManifest.json").read_text(encoding="utf-8"))
    province = next(feature for feature in national["features"] if feature["properties"]["code"] == SUMUT)
    original = shape(province["geometry"])
    if len(national["features"]) != 38 or len(districts["features"]) != 33:
        raise ValueError("Unexpected province or Sumatera Utara district count")

    # Include a small margin so island coastlines at the edge of the old
    # administrative extent are present before the intersection.
    min_x, min_y, max_x, max_y = original.bounds
    bbox = (min_x - 0.1, min_y - 0.1, max_x + 0.1, max_y + 0.1)
    land_mask = read_land_mask(args.land_shapefile, bbox)
    old_points = sum(count_coordinates(feature["geometry"]["coordinates"]) for feature in districts["features"])
    corrected = []
    for feature in districts["features"]:
        source_geometry = shape(feature["geometry"])
        clipped = polygonal(make_valid(source_geometry.intersection(land_mask)))
        if clipped.is_empty or not clipped.is_valid or clipped.area <= 0:
            raise ValueError(f"Empty or invalid corrected district: {feature['properties']['unit']}")
        feature["geometry"] = mapping(clipped)
        corrected.append(clipped)

    land_union = unary_union(corrected)
    overview = land_union.simplify(0.0005, preserve_topology=True)
    if overview.is_empty or not overview.is_valid:
        raise ValueError("Corrected Sumatera Utara overview is invalid")
    if land_union.area >= original.area * 0.9:
        raise ValueError("Correction removed too little sea area; inspect OSM land mask")
    province["geometry"] = mapping(overview)

    new_points = sum(count_coordinates(feature["geometry"]["coordinates"]) for feature in districts["features"])
    old_national_points = next(row["provincePoints"] for row in manifest["provinces"] if row["code"] == SUMUT)
    new_national_points = count_coordinates(province["geometry"]["coordinates"])
    manifest["districtPoints"] += new_points - old_points
    manifest["nationalPoints"] += new_national_points - old_national_points
    next(row for row in manifest["provinces"] if row["code"] == SUMUT)["provincePoints"] = new_national_points
    manifest["snapshot"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["source"] += "; clipped Sumatera Utara maritime district polygons to OSM land polygons"
    manifest["nationalGeometry"] = "District union clipped to OSM land for Sumatera Utara; national simplification at most 0.0005 degrees"

    shutil.copytree(args.source, args.output)
    for name, payload in (("MapNational.geojson", national), (f"MapProvince_{SUMUT}.geojson", districts), ("MapManifest.json", manifest)):
        (args.output / name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "districts": len(corrected), "oldArea": original.area,
                      "newArea": land_union.area, "oldDistrictPoints": old_points, "newDistrictPoints": new_points},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
