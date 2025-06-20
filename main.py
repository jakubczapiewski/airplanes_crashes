import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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

# Przygotowanie danych
X = crashes_per_year['Year'].values.reshape(-1, 1)
y = crashes_per_year['Crashes'].values

# Trening modelu regresji liniowej
model = LinearRegression()
model.fit(X, y)

# Predykcja na lata 2025–2030
future_years = np.arange(2025, 2031).reshape(-1, 1)
future_predictions = model.predict(future_years)

# Połączenie danych historycznych i predykcji
predicted_df = pd.DataFrame({'Year': future_years.flatten(), 'Crashes': future_predictions})
combined_df = pd.concat([crashes_per_year, predicted_df], ignore_index=True)

# Oznacz czy dane są przewidywane
combined_df['Type'] = ['History'] * len(crashes_per_year) + ['Prediction'] * len(predicted_df)

# Wizualizacja
fig = px.line(combined_df, x='Year', y='Crashes', color='Type',
              title='Liczba wypadków lotniczych – dane historyczne i prognoza (2025–2030)')
fig.update_traces(mode='lines+markers')
fig.show()
fig.write_image("crash_prediction_2025_2030.png")



# Upewniamy się, że dane są w porządku czasowym
crashes_per_year_sorted = crashes_per_year.sort_values('Year')
crashes_per_year_sorted.set_index('Year', inplace=True)

# Tworzymy model wygładzania (Holt-Winters bez sezonowości)
model = ExponentialSmoothing(crashes_per_year_sorted['Crashes'], trend='add', seasonal=None)
fit = model.fit()

# Prognozujemy kolejne 6 lat (2025–2030)
forecast_years = np.arange(crashes_per_year_sorted.index.max() + 1, crashes_per_year_sorted.index.max() + 7)
forecast = fit.forecast(6)

# Tworzymy ramkę z predykcją
forecast_df = pd.DataFrame({'Year': forecast_years, 'Crashes': forecast.values})
forecast_df['Type'] = 'Prediction'

# Dane historyczne
history_df = crashes_per_year_sorted.reset_index()
history_df['Type'] = 'History'

# Łączymy dane
combined_forecast = pd.concat([history_df, forecast_df])

# Wykres
fig = px.line(combined_forecast, x='Year', y='Crashes', color='Type',
              title='Prognoza liczby wypadków (model wygładzania wykładniczego)')
fig.update_traces(mode='lines+markers')
fig.show()
fig.write_image("ets_forecast_crashes.png")
