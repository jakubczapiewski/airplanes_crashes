import time

import geopandas as gpd
import orjson
import osmnx as ox
import pandas as pd
from shapely.geometry import Point
from tqdm import tqdm
df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')
df['Location'] = df['Location'].astype(str).str.strip()
unique_locations = df['Location'].dropna().unique()

with open("location_names.json", encoding="utf-8") as f:
    locations_dict = orjson.loads(f.read())

location_data = {}

for loc in tqdm(unique_locations):
    loc_key = loc
    loc_query = locations_dict.get(loc_key, loc_key)

    try:
        geom = ox.geocoder.geocode(loc_query)

        if geom is None:
            raise ValueError(f"Nominatim geocoder returned 0 results for query '{loc_query}'")

        # Jeśli mamy listę geometrii — weź pierwszą
        if isinstance(geom, list):
            if not geom:
                raise ValueError(f"Nominatim geocoder returned empty list for query '{loc_query}'")
            geom = geom[0]

        # Jeśli dostajemy tylko współrzędne (lat, lon) — konwertuj na Point
        if isinstance(geom, tuple) and len(geom) == 2:
            lat, lon = geom
            geom = Point(lon, lat)

        # Tworzymy GeoDataFrame ręcznie
        gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[geom])

        # Wyznaczamy centroid (w EPSG:3857)
        gdf_proj = gdf.to_crs(epsg=3857)
        centroid = gdf_proj.geometry.centroid.iloc[0]
        centroid_wgs84 = gpd.GeoSeries([centroid], crs='EPSG:3857').to_crs(epsg=4326).iloc[0]

        location_data[loc_key] = {
            'lat': centroid_wgs84.y,
            'lng': centroid_wgs84.x,
            'geometry': geom
        }

    except Exception as e:
        location_data[loc_key] = {
            'lat': None,
            'lng': None,
            'geometry': None
        }
        print(f"Nie udało się zlokalizować: {loc_query} — {e}")

    # time.sleep(1)

df['Latitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lat'))
df['Longitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lng'))
df['Geometry'] = df['Location'].map(lambda x: location_data.get(x, {}).get('geometry'))

df.to_csv('crashes_with_coordinates.csv', index=False)

gdf_full = gpd.GeoDataFrame(df, geometry='Geometry', crs='EPSG:4326')
gdf_full.to_file('crashes_with_geometries.geojson', driver='GeoJSON')