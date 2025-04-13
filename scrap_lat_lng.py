import time

import geopandas as gpd
import orjson
import osmnx as ox
import pandas as pd

df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')
unique_locations = df['Location'].dropna().apply(lambda x: x.strip()).unique()

with open("location_names.json") as f:
    locations_dict = orjson.loads(f.read())

location_data = {}

for loc in unique_locations:
    loc = locations_dict[loc]
    try:
        gdf = ox.geocode_to_gdf(loc)
        gdf_proj = gdf.to_crs(epsg=3857)
        centroid = gdf_proj.geometry.centroid.iloc[0]
        centroid_wgs84 = gpd.GeoSeries([centroid], crs='EPSG:3857').to_crs(epsg=4326).iloc[0]

        location_data[loc] = {
            'lat': centroid_wgs84.y,
            'lng': centroid_wgs84.x,
            'geometry': gdf.geometry.iloc[0]
        }

    except Exception as e:
        location_data[loc] = {
            'lat': None,
            'lng': None,
            'geometry': None
        }
        print(f"Nie udało się zlokalizować: {loc} — {e}")
    time.sleep(1)

df['Latitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lat'))
df['Longitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lng'))
df['Geometry'] = df['Location'].map(lambda x: location_data.get(x, {}).get('geometry'))

df.to_csv('crashes_with_coordinates.csv', index=False)

gdf_full = gpd.GeoDataFrame(df, geometry='Geometry', crs='EPSG:4326')
gdf_full.to_file('crashes_with_geometries.geojson', driver='GeoJSON')
