import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# === Wczytanie danych ===
df = pd.read_csv("crashes_with_coordinates.csv", encoding="latin1")
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])

# === Śmiertelność i AC Type ===
df["FatalityRate"] = (df["Fatalities"] / df["Aboard"]) * 100
df = df.dropna(subset=["FatalityRate", "AC Type"])

# Agregacja per AC Type
ac_stats = df.groupby("AC Type").agg(
    Crashes=("Date", "count"),
    MeanFatalityRate=("FatalityRate", "mean")
).reset_index()

ac_stats = ac_stats[ac_stats["Crashes"] >= 10].sort_values(by="Crashes", ascending=False)

# === Crashes per year (do ETS) ===
crashes_per_year = df.groupby(df["Date"].dt.year).size().reset_index(name="Crashes")
crashes_per_year.columns = ["Year", "Crashes"]
crashes_per_year = crashes_per_year.sort_values("Year")

# Zamiana Year → datetime
ts_data = crashes_per_year.copy()
ts_data["Date"] = pd.to_datetime(ts_data["Year"].astype(str) + "-01-01")
ts_data.set_index("Date", inplace=True)

# === ETS model ===
model = ExponentialSmoothing(ts_data["Crashes"], trend="add", seasonal=None)
fit = model.fit()

forecast_dates = pd.date_range(start=ts_data.index.max() + pd.DateOffset(years=1), periods=6, freq="YS")
forecast = fit.forecast(6)

forecast_df = pd.DataFrame({"Date": forecast_dates, "Crashes": forecast.values, "Type": "Prediction"})
history_df = ts_data.reset_index()[["Date", "Crashes"]]
history_df["Type"] = "History"

combined_df = pd.concat([history_df, forecast_df])
combined_df["Year"] = combined_df["Date"].dt.year

# === Aplikacja DASH ===
app = Dash(__name__)
app.title = "Crash Forecast Dashboard"

app.layout = html.Div([
    html.H1("Airplane Crash Statistics Dashboard", style={"textAlign": "center"}),

    html.Label("Pokaż dane ogólne:"),
    dcc.RadioItems(
        id="data_selector",
        options=[
            {"label": "Tylko dane historyczne", "value": "History"},
            {"label": "Z predykcją (ETS)", "value": "All"},
        ],
        value="All",
        labelStyle={"display": "inline-block", "margin-right": "20px"}
    ),
    dcc.Graph(id="crash_graph"),

    html.Hr(),
    html.Label("Wybierz typ samolotu:"),
    dcc.Dropdown(
        id="ac_type_selector",
        options=[{"label": t, "value": t} for t in ac_stats["AC Type"]],
        value=ac_stats["AC Type"].iloc[0],
        style={"width": "50%"}
    ),
    dcc.Graph(id="ac_type_graph"),

    html.Div("Źródło: crashes_with_coordinates.csv", style={"textAlign": "center", "marginTop": "20px"})
])


@app.callback(
    Output("crash_graph", "figure"),
    Input("data_selector", "value")
)
def update_overall_graph(mode):
    if mode == "History":
        filtered_df = combined_df[combined_df["Type"] == "History"]
    else:
        filtered_df = combined_df

    fig = px.line(filtered_df, x="Year", y="Crashes", color="Type",
                  title="Liczba wypadków lotniczych – dane i prognoza",
                  markers=True)
    return fig


@app.callback(
    Output("ac_type_graph", "figure"),
    Input("ac_type_selector", "value")
)
def update_ac_type_graph(selected_ac_type):
    filtered = df[df["AC Type"] == selected_ac_type]
    crashes_per_year = filtered.groupby(filtered["Date"].dt.year).size().reset_index(name="Crashes")

    fig = px.bar(crashes_per_year, x="Date", y="Crashes",
                 title=f"Liczba wypadków rocznie – {selected_ac_type}",
                 labels={"Date": "Rok", "Crashes": "Wypadki"})
    return fig


if __name__ == "__main__":
    app.run(debug=True)
