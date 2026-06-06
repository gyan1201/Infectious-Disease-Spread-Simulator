# Adding a New City Map to the GUI

The Streamlit GUI (`gui/app.py`) renders choropleth maps using
[Folium](https://python-visualization.github.io/folium/).
Each city needs a single GeoJSON file where every feature represents one census
tract / region, with an `"id"` property that matches the `regionId` values
written by the simulation.

---

## How maps work in the GUI

```
gui/
  app.py
  atlanta_regions.geojson      ← one file per city
  san-fran_regions.geojson
```

`app.py` maintains a city → file mapping near the top of the file:

```python
CITY_GEOJSON = {
    "Atlanta":       str(GUI_DIR / "atlanta_regions.geojson"),
    "San Francisco": str(GUI_DIR / "san-fran_regions.geojson"),
}
```

At runtime, each GeoJSON feature **must** have an integer `"id"` property that
matches the `regionId` column in `DiseaseReports.tsv`. The GUI joins on this
field to colour each tract.

---

## Step 1 — Create the simulation shapefiles

Follow `map.md` in this folder to produce `buildings.shp`, `buildingUnits.shp`,
and `walkways.shp` for your city.  Place them under:

```
examples/<city-name>/
  buildings.shp   (+ .dbf .prj .shx etc.)
  buildingUnits.shp
  walkways.shp
  region_census.shp   ← census-tract polygons with demographic attributes
```

---

## Step 2 — Convert `region_census.shp` to GeoJSON

The GUI reads a pre-converted GeoJSON, not the raw shapefile.  Use QGIS or
the command below (requires `geopandas`):

```python
import geopandas as gpd

gdf = gpd.read_file("examples/<city-name>/region_census.shp")

# Reproject to WGS-84 (lat/lon) which Folium expects
gdf = gdf.to_crs(epsg=4326)

# The simulation numbers regions starting at 1; make sure the GeoJSON
# feature property "id" matches.  Adjust the column name if needed.
gdf = gdf.rename(columns={"TrackId_int": "id"})   # <- use your actual column

# Keep only the columns the GUI needs (id + any you want in tooltips)
gdf = gdf[["id", "geometry"]]

gdf.to_file("gui/<city-name>_regions.geojson", driver="GeoJSON")
```

**Required property:** every feature must have an integer (or integer-string)
`"id"` field.  The GUI casts it to `int` when joining to simulation data.

The existing Atlanta GeoJSON was produced from `region_census.shp` in
`examples/atlanta/`.  Its features carry the full census demographic columns
(`TotPop`, `Male`, `Race0`–`Race6`, `Income0`–`Income6`, etc.) which are used
only for tooltips; they are not required for the choropleth to work.

---

## Step 3 — Register the city in `app.py`

Open `gui/app.py` and add your city to two places:

**1. The `CITY_GEOJSON` dict** (around line 46):

```python
CITY_GEOJSON = {
    "Atlanta":       str(GUI_DIR / "atlanta_regions.geojson"),
    "San Francisco": str(GUI_DIR / "san-fran_regions.geojson"),
    "My City":       str(GUI_DIR / "my-city_regions.geojson"),   # <- add this
}
```

**2. The map default centre** inside `build_choropleth` and
`build_reporting_map` (search for `_map_center`).  Both functions pass a
fallback `[lat, lon]` used when the GeoJSON bounding box cannot be computed.
The existing default is Atlanta `[33.75, -84.39]`; it is only used as a
last-resort fallback so it does not need to be exact.

---

## Step 4 — Test

1. Run a simulation with the new city properties file, e.g.:

   ```bash
   bash run.sh my-city-test 30
   ```

2. Open the GUI, select **My City** from the city dropdown in the Results tab,
   and point it at the new log folder.

3. Verify that the choropleth colours every tract.  Any tract whose `regionId`
   does not match a GeoJSON `"id"` will be left grey — check for mismatches
   with:

   ```python
   import json, pandas as pd
   geo = json.load(open("gui/my-city_regions.geojson"))
   geo_ids  = {int(f["properties"]["id"]) for f in geo["features"]}
   tsv_ids  = set(pd.read_csv("logs/my-city-test/DiseaseReports.tsv",
                               sep="\t", usecols=[0])["regionId"].dropna().astype(int))
   print("Missing from GeoJSON:", tsv_ids - geo_ids)
   print("Extra in GeoJSON:",     geo_ids - tsv_ids)
   ```

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| All tracts grey | `"id"` property missing or wrong type in GeoJSON |
| Map shows wrong location | CRS not reprojected to EPSG:4326 before export |
| Tooltip shows `None` | Column renamed incorrectly in Step 2 |
| City not in dropdown | Entry missing from `CITY_GEOJSON` in `app.py` |
