import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.options.plotting.backend = "plotly"

# Read the data
df = pd.read_csv('crashes_with_coordinates.csv', encoding='latin1')
print(df.columns)
# Convert 'Date' column to datetime
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # handle any bad/missing dates

# Drop rows with invalid/missing dates just in case
df = df.dropna(subset=['Date'])

crashes_per_operator = df[df['Date'].dt.year > 1980].groupby(df['Operator']).size().reset_index(
    name='Crashes').sort_values(by=['Crashes'], ascending=False)
crashes_per_operator.columns = ['Operator', 'Crashes']

# Group by year
crashes_per_year = df.groupby(df['Date'].dt.year).size().reset_index(name='Crashes')
crashes_per_year.columns = ['Year', 'Crashes']

crashes_per_aircraft = (df.groupby(df['AC Type']).size().reset_index(name='Crashes').sort_values(by=['Crashes'],
                                                                                                 ascending=False))

crashes_per_aircraft.columns = ['AC Type', 'Crashes']
crashes_per_aircraft = crashes_per_aircraft[crashes_per_aircraft['Crashes'] > 10]

# Plot with Plotly
fig = px.line(crashes_per_year, x='Year', y='Crashes', title='Airplane Crashes per Year')
fig.show()
fig.write_image('crashes_per_year.png')

fig = px.line(crashes_per_operator, x='Operator', y='Crashes', title='Airplane Crashes per Operator >1980')
fig.show()
fig.write_image('crashes_per_operator.png')

df['FatalityRate'] = (df['Fatalities'] / df['Aboard']) * 100

df_clean = df.dropna(subset=['FatalityRate', 'AC Type'])

fatality_stats = df_clean.groupby('AC Type').agg(
    FatalityRate=('FatalityRate', 'mean'),
    Count=('FatalityRate', 'count')
).reset_index()

fatality_stats = fatality_stats[fatality_stats['Count'] >= 10]
fatality_stats = fatality_stats.sort_values(by='FatalityRate', ascending=False)

fig = px.bar(fatality_stats, x='AC Type', y='FatalityRate',
             title='Śmiertelność (% Fatalities / Aboard) wg typu samolotu (min. 10 przypadków)',
             labels={'FatalityRate': 'Śmiertelność [%]'})

fig.show()
fig.write_image('Fatality Rate per ac type.png')

fig = px.bar(crashes_per_aircraft, x='AC Type', y='Crashes',
             title='Ilość wypadków wg typu samolotu',
             )
fig.show()
fig.write_image('Ilość wypadków wg typu samolotu.png')

# Merge dwóch zbiorów danych po AC Type
merged = pd.merge(fatality_stats, crashes_per_aircraft, on='AC Type', how='inner')

# Tworzymy wykres z dwiema osiami Y
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Dodajemy śmiertelność jako słupki
fig.add_trace(
    go.Bar(x=merged['AC Type'], y=merged['FatalityRate'], name='Śmiertelność [%]'),
    secondary_y=False,
)

# Dodajemy liczbę wypadków jako linia
fig.add_trace(
    go.Scatter(x=merged['AC Type'], y=merged['Crashes'], name='Liczba wypadków', mode='lines+markers'),
    secondary_y=True,
)

# Tytuł i opisy osi
fig.update_layout(
    title_text="Śmiertelność i liczba wypadków wg typu samolotu (min. 10 przypadków)",
    xaxis_title="Typ samolotu",
    legend=dict(x=0.5, y=1.15, orientation="h", xanchor="center"),
    height=600
)

fig.update_yaxes(title_text="Śmiertelność [%]", secondary_y=False)
fig.update_yaxes(title_text="Liczba wypadków", secondary_y=True)

fig.show()
fig.write_image("fatality_vs_crashes_per_ac_type.png")
