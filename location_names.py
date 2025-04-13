import ollama
import orjson
import pandas as pd

df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')
unique_locations = df['Location'].dropna().apply(lambda x: x.strip()).unique()


def clean_location_with_ollama(location):
    prompt = f"""
    Given an informal location, return a simplified and geocodable place name. Country, city, ocean, sea etc. 

    Remove words like 'Near', 'Off', 'Over', and make sure the result matches real places as listed in OpenStreetMap.

    Only return the cleaned location name — no explanation, no extra text.

    Input: {location}
    Output:"""

    response = ollama.chat(
        model='gemma3:1b',
        messages=[{"role": "user", "content": prompt}]
    )

    cleaned = response['message']['content'].strip()
    return cleaned


locations_dict = {}

for loc in unique_locations:
    new_loc = clean_location_with_ollama(loc)
    locations_dict[loc] = new_loc
    print(loc, " -> ", new_loc)

with open('location_names.json', 'w') as json_file:
    json_pretty = orjson.dumps(locations_dict, option=orjson.OPT_INDENT_2).decode("utf-8")
    json_file.write(json_pretty)
