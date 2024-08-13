import json
from urllib.request import urlopen

import numpy as np
import pandas as pd
import plotly.graph_objects as go

with urlopen('https://raw.githubusercontent.com/thomasvalentine/Choropleth/main/Local_Authority_Districts_(December_2021)_GB_BFC.json') as response:
    Local_authorities = json.load(response)

area_list = [x['properties']['LAD21NM'] for x in Local_authorities['features']]*3

# create random data for the 3 months of data - this will be the model output
random_list = np.random.randint(0, 100, len(area_list))
random_list = random_list.tolist()

# create a dataframe of area_list and random_list
df = pd.DataFrame(list(zip(area_list, random_list)), columns=['Area', 'ML model output'])
df = df.sort_values(by=['Area'])

# create a column of month whic is Aug, Sept and Oct for each area - so should be York, Aug, York, Sept, York, Oct, etc
months_list = ['Aug', 'Sept', 'Oct']
df['month_str'] = np.tile(months_list, len(df) // len(months_list) + 1)[:len(df)]
df['month_numeric']=df['month_str'].map({'Aug':8, 'Sept':9, 'Oct':10})
df['month_datetime'] = pd.to_datetime(df['month_numeric'].apply(lambda x: f'2019-{x:02d}-01'))

# do the same for the incident data
incident_data = pd.read_csv('RNLI_Return_of_Service.csv')
incident_data['Date_of_Launch'] = pd.to_datetime(incident_data['Date_of_Launch'], format='%Y/%m/%d')
incident_data['month_datetime'] = incident_data['Date_of_Launch'].dt.to_period('M').dt.to_timestamp()

# Create the base map
fig = go.Figure()
# plotly.offline.plot(fig, auto_play = False)

# Set map layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=4.2,
    mapbox_center={"lat": 55.09621, "lon": -4.0286298},
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    width=1000,
    height=800,
)

# Prepare frames for the animation
frames = []
for month in df['month_datetime'].unique():
    # Filter scatter data for the current month
    incidents_filtered = incident_data[incident_data['month_datetime'] == month]
    df_filtered = df[df['month_datetime'] == month]

    # Create a new frame
    frame = go.Frame(
        data=[
            # Include the choropleth trace in each frame
            go.Choroplethmapbox(
                geojson=Local_authorities,
                locations=df_filtered['Area'],
                z=df_filtered['ML model output'],
                featureidkey="properties.LAD21NM",
                colorscale="Viridis",
                marker_opacity=0.5,
                zmin=df['ML model output'].min(),
                zmax=df['ML model output'].max(),
                name='Choropleth',
                visible=True,
            ),
            # Add the scatter points for this specific month
            go.Scattermapbox(
                lat=incidents_filtered['y'],
                lon=incidents_filtered['x'],
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Incidents',
                text=incidents_filtered.apply(lambda row: f"Date: {row['Date_of_Launch'].strftime('%Y-%m-%d')}<br>"
                                              f"Type: {row['ReasonforLaunch']}<br>"
                                              f"Location: {row['LifeboatClass']}", axis=1),
                hoverinfo='text',
            )
        ],
        name=str(month)
    )

    frames.append(frame)

# Add frames to the figure
fig.frames = frames

# Include the choropleth in the initial figure (before any frame is active)
initial_df = df[df['month_datetime'] == df['month_datetime'].min()]
fig.add_trace(go.Choroplethmapbox(
    geojson=Local_authorities,
    locations=initial_df['Area'],
    z=initial_df['ML model output'],
    featureidkey="properties.LAD21NM",
    colorscale="Viridis",
    marker_opacity=0.5,
    zmin=df['ML model output'].min(),
    zmax=df['ML model output'].max(),
    name='Choropleth'
))

# Add the initial scatter points (for the first month)
initial_incidents = incident_data[incident_data['month_datetime'] == df['month_datetime'].min()]
fig.add_trace(go.Scattermapbox(
    lat=initial_incidents['y'],
    lon=initial_incidents['x'],
    mode='markers',
    marker=dict(size=10, color='red'),
    name='Incidents',
    text=incidents_filtered.apply(lambda row: f"Date: {row['Date_of_Launch'].strftime('%Y-%m-%d')}<br>"
                                              f"Type: {row['ReasonforLaunch']}<br>"
                                              f"Location: {row['LifeboatClass']}", axis=1),
    hoverinfo='text'
))

# Update the layout with sliders and animation controls
fig.update_layout(
    updatemenus=[{
        "buttons": [
            {
                "args": [None, {"frame": {"duration": 500, "redraw": True}, "fromcurrent": True}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                "label": "Pause",
                "method": "animate"
            }
        ],
        "direction": "left",
        "pad": {"r": 10, "t": 87},
        "showactive": False,
        "type": "buttons",
        "x": 0.1,
        "xanchor": "right",
        "y": 0,
        "yanchor": "top"
    }],
    sliders=[{
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Month: ",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": [
            {
                "args": [
                    [str(month)],
                    {"frame": {"duration": 300, "redraw": True}, "mode": "immediate", "transition": {"duration": 300}}
                ],
                "label": pd.to_datetime(month).strftime('%Y/%m'),
                "method": "animate"
            } for month in df['month_datetime'].unique()
        ]
    }]
)

fig.write_html("index.html")