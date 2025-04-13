import time

import geopandas as gpd
import osmnx as ox
import pandas as pd

df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')
unique_locations = df['Location'].dropna().apply(lambda x: x.strip()).unique()

print(len(unique_locations))

# Słownik: lokalizacja → (lat, lng, geometry)
location_data = {}

for loc in unique_locations:
    try:
        gdf = ox.geocode_to_gdf(loc)
        gdf_proj = gdf.to_crs(epsg=3857)
        # centroid = gdf_proj.geometry.centroid.iloc[0]
        centroid_wgs84 = gdf_proj.set_geometry('geometry').to_crs(epsg=4326).geometry.centroid.iloc[0]

        location_data[loc] = {
            'lat': centroid_wgs84.y,
            'lng': centroid_wgs84.x,
            'geometry': gdf.geometry.iloc[0]  # oryginalna geometria (polygon)
        }
    except Exception as e:
        location_data[loc] = {
            'lat': None,
            'lng': None,
            'geometry': None
        }
        print(f"Nie udało się zlokalizować: {loc} — {e}")
    time.sleep(1)

# Dodaj dane do głównego df
df['Latitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lat'))
df['Longitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lng'))
df['Geometry'] = df['Location'].map(lambda x: location_data.get(x, {}).get('geometry'))

# Zapisz jako CSV (punktowe dane)
df.to_csv('crashes_with_coordinates.csv', index=False)

# Zapisz jako GeoJSON (pełne geometrie)
gdf_full = gpd.GeoDataFrame(df, geometry='Geometry', crs='EPSG:4326')
gdf_full.to_file('crashes_with_geometries.geojson', driver='GeoJSON')
