import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def load_data(file_path='crashes_with_coordinates.csv'):
    """
    Load the CSV file into a pandas DataFrame

    Args:
        file_path (str): Path to the CSV file

    Returns:
        pd.DataFrame: DataFrame containing the crash data
    """
    df = pd.read_csv(file_path)
    # Convert Date to datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Fill NaN values in numeric columns
    numeric_columns = ['Aboard', 'Fatalities', 'Aboard Passangers', 'Aboard Crew', 
                       'Fatalities Passangers', 'Fatalities Crew', 'Ground']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df

def create_scatter_map(df):
    """
    Create a scatter map showing crash locations

    Args:
        df (pd.DataFrame): DataFrame containing crash data

    Returns:
        plotly.graph_objects.Figure: Scatter map figure
    """
    # Create hover text with crash details
    df['hover_text'] = df.apply(
        lambda row: f"Date: {row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else 'Unknown'}<br>" +
                   f"Location: {row['Location']}<br>" +
                   f"Operator: {row['Operator']}<br>" +
                   f"Aircraft: {row['AC Type']}<br>" +
                   f"Fatalities: {row['Fatalities']}/{row['Aboard']}<br>" +
                   f"Summary: {str(row['Summary'])[:100] + '...' if pd.notna(row['Summary']) else 'No summary available'}",
        axis=1
    )

    # Create scatter map
    fig = px.scatter_map(
        df,
        lat='Latitude',
        lon='Longitude',
        hover_name='Location',
        hover_data={
            'Latitude': False,
            'Longitude': False,
            'hover_text': True
        },
        custom_data=['hover_text'],
        color='Fatalities',
        size='Aboard',
        color_continuous_scale='Viridis',
        size_max=15,
        zoom=1,
        title='Airplane Crashes Around the World'
    )

    # Update hover template to use custom hover text
    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    # Use OpenStreetMap for the base map
    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=800
    )

    return fig

def create_heatmap(df):
    """
    Create a heatmap showing crash density

    Args:
        df (pd.DataFrame): DataFrame containing crash data

    Returns:
        plotly.graph_objects.Figure: Heatmap figure
    """
    fig = px.density_map(
        df,
        lat='Latitude',
        lon='Longitude',
        z='Fatalities',
        radius=20,
        center=dict(lat=0, lon=0),
        zoom=1,
        title='Heatmap of Airplane Crashes by Fatalities'
    )

    fig.update_layout(
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=800
    )

    return fig

def create_time_series(df):
    """
    Create a time series chart showing crashes over time

    Args:
        df (pd.DataFrame): DataFrame containing crash data

    Returns:
        plotly.graph_objects.Figure: Time series figure
    """
    # Group by year and count crashes
    yearly_crashes = df.groupby(df['Date'].dt.year).size().reset_index(name='count')
    yearly_fatalities = df.groupby(df['Date'].dt.year)['Fatalities'].sum().reset_index()

    # Create figure with two y-axes
    fig = go.Figure()

    # Add traces
    fig.add_trace(
        go.Scatter(
            x=yearly_crashes['Date'],
            y=yearly_crashes['count'],
            name='Number of Crashes',
            line=dict(color='blue')
        )
    )

    fig.add_trace(
        go.Scatter(
            x=yearly_fatalities['Date'],
            y=yearly_fatalities['Fatalities'],
            name='Number of Fatalities',
            line=dict(color='red')
        )
    )

    # Update layout
    fig.update_layout(
        title='Airplane Crashes and Fatalities Over Time',
        xaxis_title='Year',
        yaxis_title='Count',
        legend=dict(x=0.01, y=0.99),
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        height=500
    )

    return fig

def main():
    """
    Main function to load data and create maps
    """
    # Load data
    df = load_data()

    # Create scatter map
    scatter_map = create_scatter_map(df)
    scatter_map.write_html('airplane_crashes_map.html')

    # Create heatmap
    heatmap = create_heatmap(df)
    heatmap.write_html('airplane_crashes_heatmap.html')

    # Create time series
    time_series = create_time_series(df)
    time_series.write_html('airplane_crashes_time_series.html')

    print("Maps created successfully!")
    print("- Scatter map saved as 'airplane_crashes_map.html'")
    print("- Heatmap saved as 'airplane_crashes_heatmap.html'")
    print("- Time series saved as 'airplane_crashes_time_series.html'")

if __name__ == "__main__":
    main()
