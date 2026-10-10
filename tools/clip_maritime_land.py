#!/usr/bin/env python3
"""Clip maritime OSM administrative polygons to the OSM land coastline.

Some district relations include maritime jurisdiction. Those sea areas must
not be rendered as land on either map level. Run with the OSM land polygon
shapefile from https://osmdata.openstreetmap.de/data/land-polygons.html:

    python3 tools/clip_maritime_land.py data/2026-10-10 PATH/land_polygons.shp data/2026-10-10b ID_RI ID_PD

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
        raise ValueError(f"No OSM land polygons intersect {bbox}")
    return unary_union(polygons)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Published, immutable source version directory")
    parser.add_argument("land_shapefile", type=Path, help="OSM land_polygons.shp")
    parser.add_argument("output", type=Path, help="New version directory")
    parser.add_argument("codes", nargs="+", help="Province codes, e.g. ID_RI ID_PD")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output version already exists; never overwrite a published snapshot")

    national = json.loads((args.source / "MapNational.geojson").read_text(encoding="utf-8"))
    manifest = json.loads((args.source / "MapManifest.json").read_text(encoding="utf-8"))
    if len(national["features"]) != 38 or sum(row["districtCount"] for row in manifest["provinces"]) != 514:
        raise ValueError("Unexpected national coverage")
    if len(set(args.codes)) != len(args.codes):
        raise ValueError("Duplicate province code")

    outputs = {}
    report = []
    for code in args.codes:
        province = next((feature for feature in national["features"] if feature["properties"]["code"] == code), None)
        manifest_row = next((row for row in manifest["provinces"] if row["code"] == code), None)
        if province is None or manifest_row is None:
            raise ValueError(f"Unknown province code: {code}")
        filename = f"MapProvince_{code}.geojson"
        districts = json.loads((args.source / filename).read_text(encoding="utf-8"))
        original = shape(province["geometry"])
        if len(districts["features"]) != manifest_row["districtCount"]:
            raise ValueError(f"Unexpected district count: {code}")

        # Include coastline just beyond the administrative extent.
        min_x, min_y, max_x, max_y = original.bounds
        land_mask = read_land_mask(args.land_shapefile, (min_x - 0.1, min_y - 0.1, max_x + 0.1, max_y + 0.1))
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
        # Match the existing national display tolerance. District geometry
        # keeps every source and coastline vertex; it is never simplified.
        overview = land_union
        for tolerance in (0.0005, 0.00025, 0.0001, 0.00005, 0):
            candidate = land_union.simplify(tolerance, preserve_topology=True) if tolerance else land_union
            if not candidate.is_empty and candidate.is_valid:
                overview = candidate
                break
        if overview.is_empty or not overview.is_valid:
            raise ValueError(f"Invalid corrected national geometry: {code}")
        if land_union.area >= original.area * 0.98:
            raise ValueError(f"Correction removed too little sea area: {code}")
        province["geometry"] = mapping(overview)

        new_points = sum(count_coordinates(feature["geometry"]["coordinates"]) for feature in districts["features"])
        new_national_points = count_coordinates(province["geometry"]["coordinates"])
        manifest["districtPoints"] += new_points - old_points
        manifest["nationalPoints"] += new_national_points - manifest_row["provincePoints"]
        manifest_row["provincePoints"] = new_national_points
        outputs[filename] = districts
        report.append({"code": code, "districts": len(corrected), "oldArea": original.area,
                       "newArea": land_union.area, "oldDistrictPoints": old_points,
                       "newDistrictPoints": new_points})

    manifest["snapshot"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["source"] += "; clipped maritime district polygons to OSM land polygons for " + ", ".join(args.codes)
    manifest["nationalGeometry"] = "District union with OSM land clipping for maritime provinces; national simplification at most 0.0005 degrees"

    shutil.copytree(args.source, args.output)
    outputs["MapNational.geojson"] = national
    outputs["MapManifest.json"] = manifest
    for name, payload in outputs.items():
        (args.output / name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "report": report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
