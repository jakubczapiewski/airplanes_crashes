import pandas as pd
import plotly.express as px

pd.options.plotting.backend = "plotly"

# Read the data
df = pd.read_csv('Airplane_Crashes_and_Fatalities_Since_1908_t0_2023.csv', encoding='latin1')

# Convert 'Date' column to datetime
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # handle any bad/missing dates

# Drop rows with invalid/missing dates just in case
df = df.dropna(subset=['Date'])



crashes_per_operator= df.groupby(df['Operator']).size().reset_index(name='Crashes').sort_values(by=['Crashes'], ascending=False)
crashes_per_operator.columns = ['Operator', 'Crashes']

# Group by year
crashes_per_year = df.groupby(df['Date'].dt.year).size().reset_index(name='Crashes')
crashes_per_year.columns = ['Year', 'Crashes']

# Plot with Plotly
fig = px.line(crashes_per_year, x='Year', y='Crashes', title='Airplane Crashes per Year')
fig.show()


fig = px.line(crashes_per_operator, x='Operator', y='Crashes', title='Airplane Crashes per Operator')
fig.show()