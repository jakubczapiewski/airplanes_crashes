import pandas as pd
import plotly.express as px

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

crashes_per_aircraft = df.groupby(df['AC Type']).size().reset_index(name='Crashes').sort_values(by=['Crashes'],
                                                                                                ascending=False)
crashes_per_aircraft.columns = ['AC Type', 'Crashes']

# Plot with Plotly
fig = px.line(crashes_per_year, x='Year', y='Crashes', title='Airplane Crashes per Year')
fig.show()

fig = px.line(crashes_per_operator, x='Operator', y='Crashes', title='Airplane Crashes per Operator >1980')
fig.show()


df['FatalityRate'] = (df['Fatalities'] / df['Aboard']) * 100

df_clean = df.dropna(subset=['FatalityRate', 'AC Type'])

fatality_stats = df_clean.groupby('AC Type').agg(
    FatalityRate=('FatalityRate', 'mean'),
    Count=('FatalityRate', 'count')
).reset_index()

fatality_stats = fatality_stats[fatality_stats['Count'] >= 10]
fatality_stats = fatality_stats.sort_values(by='FatalityRate', ascending=False)

fig = px.bar(fatality_stats, x='AC Type', y='FatalityRate',
             title='Śmiertelność (% Fatalities / Aboard) wg typu samolotu (min. 50 przypadków)',
             labels={'FatalityRate': 'Śmiertelność [%]'})
fig.show()
