import time
import geopandas as gpd
import orjson
import pandas as pd
import googlemaps
from shapely.geometry import Point
from tqdm import tqdm

# Twój klucz API
gmaps = googlemaps.Client(key="AIzaSyBi7_dJC8HWW9nq4vMXGXSlHhiTHWCmAcQ")


def geocode_with_googlemaps(query):
    geocode_result = gmaps.geocode(query)
    if not geocode_result:
        raise ValueError(f"Nie znaleziono lokalizacji: {query}")

    location = geocode_result[0]['geometry']['location']
    return Point(location['lng'], location['lat'])


# Wczytanie danych
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
        geom = geocode_with_googlemaps(loc_query)

        # Tworzenie GeoDataFrame i przeliczanie centroidu
        gdf = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[geom])
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

    time.sleep(0.2)  # Ograniczenie zapytań

# Dodanie współrzędnych do DataFrame
df['Latitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lat'))
df['Longitude'] = df['Location'].map(lambda x: location_data.get(x, {}).get('lng'))
df['Geometry'] = df['Location'].map(lambda x: location_data.get(x, {}).get('geometry'))

df.to_csv('crashes_with_coordinates.csv', index=False)

# Zapis do GeoJSON
gdf_full = gpd.GeoDataFrame(df, geometry='Geometry', crs='EPSG:4326')
gdf_full.to_file('crashes_with_geometries.geojson', driver='GeoJSON')
