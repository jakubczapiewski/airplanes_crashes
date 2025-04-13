import pandas as pd
import re
import orjson

df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')
unique_locations = df['Location'].dropna().apply(lambda x: x.strip()).unique()

def clean_location(location):
    location = re.sub(r'^(Near|Off|Over|off|near|over)\s+', '', location)

    location = re.sub(r'\(.*?\)', '', location)

    location = location.strip().strip(',')

    location = re.sub(r'\s+', ' ', location)

    return location.strip()

locations_dict = {}

for loc in unique_locations:
    new_loc = clean_location(loc)
    locations_dict[loc] = new_loc
    print(loc, " -> ", new_loc)

with open('location_names.json', 'w') as json_file:
    json_pretty = orjson.dumps(locations_dict, option=orjson.OPT_INDENT_2).decode("utf-8")
    json_file.write(json_pretty)
