import ollama
import orjson
import pandas as pd

df = pd.read_csv('crashes_with_coordinates.csv', encoding='latin1')
unique_summary = df['Summary'].dropna().apply(lambda x: x.strip()).unique()


def summary_with_ollama(location):
    prompt = f"""
    Given an airplanes crash summary, return a one word crash cause

    Only return the crash cause — no explanation, no extra text.

    Input: {location}
    Output:"""

    response = ollama.chat(
        model='gemma3:1b',
        messages=[{"role": "user", "content": prompt}]
    )

    cleaned = response['message']['content'].strip()
    return cleaned


summary_dict = {}

for summary in unique_summary:
    new_summary = summary_with_ollama(summary)
    summary_dict[summary] = new_summary
    print(summary, " -> ", new_summary)

with open('category.json', 'w') as json_file:
    json_pretty = orjson.dumps(summary_dict, option=orjson.OPT_INDENT_2).decode("utf-8")
    json_file.write(json_pretty)
#

# with open('category.json', 'r') as json_file:
#     summary_dict = orjson.loads(json_file.read())
#
#
#
# df['Category'] = df['Summary'].map(lambda x: summary_dict.get(x))
#
# df.to_csv('crashes_with_coordinates.csv', index=False)