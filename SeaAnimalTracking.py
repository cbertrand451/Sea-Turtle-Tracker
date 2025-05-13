import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import numpy as np



##load and clean data
#load data using os path
file_path = os.path.join(os.path.dirname(__file__), 'data', 'obis_seamap_dataset_758_lines.csv')
df = pd.read_csv(file_path)
# convert  date_time to a datetime object called 'timestamp'
df['timestamp_begin'] = pd.to_datetime(df['datetime_begin'])
df['timestamp_end'] = pd.to_datetime(df['datetime_end'])
#create the dataset with necesary data
df_turtles = df[['series_id', 'longitude_begin', 'latitude_begin', 'longitude_end', 'latitude_end', 'timestamp_begin', 'timestamp_end', 'length_km', 'speed_kph']]
#get rid of null rows
df_turtles = df_turtles.dropna()


##create UI
#title of the page
st.title("Tracking Loggerhead Sea Turtles!")
#description
st.markdown("This visualization follows the path of 17 different juvenile Loggerhead Sea Turtles from 2002 to 2005. " \
" Select a turtle in order to see it's path along with descriptive statistics and insights." \
" Zoom in to see plotted data points with datetime information." \
" Enjoy!")
st.markdown("---")

#these are all the options of turtles
series_options = df_turtles['series_id'].unique()
#select which turtle is being shown
selected_series = st.selectbox("Select Turtle:", series_options)
##clean/wrangle selected turtle data
#create selected turtle dataset
df_selected = df_turtles[df_turtles['series_id'] == selected_series].copy()
#sort by time 
df_selected = df_selected.sort_values('timestamp_begin')


##fix longitude wraparound data
#copying the original columns
lon1 = df_selected['longitude_begin'].values.copy()
lon2 = df_selected['longitude_end'].values.copy()
#creating new columns for the fixed data to go into
lon1_un = lon1.copy()
lon2_un = lon2.copy()
#find the difference
diff = np.abs(lon1 - lon2)
#create a true/false array for if the values are wrapped
wrapped = diff > 180
#correct the vals if wrapped
lon2_un[wrapped & (lon1 > lon2)] += 360
lon1_un[wrapped & (lon2 > lon1)] += 360
#replace the values with the fixed unwrapped ones 
df_selected['longitude_begin'] = lon1_un
df_selected['longitude_end'] = lon2_un


#create columns that displays time as a string for later UI use
df_selected['time_string'] = df_selected['timestamp_begin'].dt.strftime('%B %m, %Y: %I:%M %p')
#df_selected['time_string_end'] = df_selected['timestamp_end'].dt.strftime('%B %m, %Y: %I:%M %p')

##creating dataframes for the interactive points
#normal points
df_points = df_selected.iloc[1:].copy()

#starting point
df_start = pd.DataFrame([{
    'longitude': df_selected['longitude_begin'].iloc[0],
    'latitude': df_selected['latitude_begin'].iloc[0], 
    'time_string' : df_selected['timestamp_begin'].iloc[0].strftime('%B %m, %Y: %I:%M %p')
}])

#ending points
df_end = pd.DataFrame([{
    'longitude': df_selected['longitude_end'].iloc[-1],
    'latitude': df_selected['latitude_end'].iloc[-1]
}])


##creating sidebar 
st.sidebar.title("Turtle Description")
st.sidebar.markdown(f"Selected Turtle: **{selected_series}**")
unit = st.sidebar.radio("Select Unit", ["Kilometers", "Miles"])
st.sidebar.markdown('---')

#Movement
if unit == "Kilometers":
    total_distance = round(df_selected['length_km'].sum(), 3)
    avg_speed = round(df_selected['speed_kph'].mean(), 3)
    max_speed = round(df_selected[df_selected['speed_kph'] <= 24]['speed_kph'].max(), 3)
    longest_move = round(df_selected['length_km'].max(), 3)
    speed_unit = "km/hr"
    distance_unit = "km"
else:
    total_distance = round(df_selected['length_km'].sum() * 0.621371, 3)
    avg_speed = round(df_selected['speed_kph'].mean() * 0.621371, 3)
    max_speed = round(df_selected[df_selected['speed_kph'] <= 24]['speed_kph'].max() * 0.621371, 3)
    longest_move = round(df_selected['length_km'].max() * 0.621371, 3)
    speed_unit = "mph"
    distance_unit = "miles"

# Display values
st.sidebar.markdown(f"Total Distance: {total_distance} {distance_unit}")
st.sidebar.markdown(f"Average Speed: {avg_speed} {speed_unit}")
st.sidebar.markdown(f"Max Speed: {max_speed} {speed_unit}")
st.sidebar.markdown(f"Total Moves: {len(df_selected)}")
st.sidebar.markdown(f"Longest Move: {longest_move} {distance_unit}")
st.sidebar.markdown('---')

#Time
st.sidebar.subheader("Time Metrics")
#computing start and end times to clean up the text
start = df_selected['timestamp_begin'].min()
end = df_selected['timestamp_end'].max()
days = (end - start).days
st.sidebar.markdown(f"Start Date: {start.strftime('%B %m, %Y: %I:%M %p')}")
st.sidebar.markdown(f"End Date: {df_selected['timestamp_end'].max().strftime('%B %m, %Y: %I:%M %p')}")
st.sidebar.markdown(f"Calendar Duration: {days} days")
#creating a column to calculate average time
df_selected['time_diff'] = df_selected['timestamp_end'] - df_selected['timestamp_begin']
time_m = df_selected['time_diff'].mean()
seconds_m = time_m.seconds
st.sidebar.markdown(f"Average Time per Move: {time_m.days} days, {round(seconds_m / 3600, 3)} hours")
st.sidebar.markdown('---')

#Location
st.sidebar.subheader("Location Metrics")
st.sidebar.caption("*Metrics in (Latitude, Longitude) form*")
st.sidebar.markdown(f"Starting Location: ({df_selected['latitude_begin'].iloc[0]}, {df_selected['longitude_begin'].iloc[0]})")
st.sidebar.markdown(f"Ending Location: ({df_selected['latitude_end'].iloc[-1]}, {df_selected['longitude_end'].iloc[-1]})")

df_selected['mid_lat'] = (df_selected['latitude_begin'] + df_selected['latitude_end']) / 2
df_selected['mid_lon'] = (df_selected['longitude_begin'] + df_selected['longitude_end']) / 2
st.sidebar.markdown(f"Center of Path: ({round(df_selected['mid_lat'].mean(), 2)}, {round(df_selected['mid_lon'].mean(), 2)})")
center_path = st.sidebar.toggle("Show Center Point")
st.sidebar.caption("Center Point does not show Spherical (Geographic) Mean. Point may not fall in the correct spt if the turtle path cross the INternational Date Line.")

#set dataframe for center path point
df_center = pd.DataFrame([{
    'lat': df_selected['mid_lat'].mean(),
    'lon': df_selected['mid_lon'].mean()
}])

#set colors
line_color = [255, 255, 255]
point_color = [0, 0, 255]

##Creating the actual lines
layer = pdk.Layer("LineLayer",
                  data= df_selected, 
                  get_source_position= "[longitude_begin, latitude_begin]", 
                  get_target_position="[longitude_end, latitude_end]", 
                  get_width= 3, 
                  get_color=line_color,
                  pickable=True)

##creating the points
#middle blue points
point_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_points,
    get_position='[longitude_begin, latitude_begin]',
    get_color=point_color,
    get_radius=500,
    pickable=True, 
    radiusScale=4, 
    radiusMinPixels=2, 
    radiusMaxPixels=10
)

#starting green point
start_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_start,
    get_position='[longitude, latitude]',
    get_color=[0, 255, 0], 
    get_radius=1000, 
    radiusScale=8, 
    radiusMinPixels=4, 
    radiusMaxPixels=25, 
)

#ending red point
end_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_end,
    get_position='[longitude, latitude]',
    get_color=[255, 0, 0],  
    get_radius=1000, 
    radiusScale=8, 
    radiusMinPixels=4, 
    radiusMaxPixels=25, 
)

center_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_center,
    get_position='[lon, lat]',
    get_color=[160, 32, 240],  
    get_radius=2000, 
    radiusScale=10, 
    radiusMinPixels=6, 
    radiusMaxPixels=50, 
)
layers_ = [layer, point_layer, start_layer, end_layer]
if center_path:
    layers_ = [layer, point_layer, start_layer, end_layer, center_layer]

#this is the state that is shown when the turtle is selected
view_state = pdk.ViewState(latitude=df_selected['latitude_begin'].mean(), 
                           longitude=df_selected['longitude_begin'].mean(), 
                           zoom=4, pitch=0)

r = pdk.Deck(layers=layers_, initial_view_state=view_state, tooltip={"text": "Time: {time_string}"})

st.pydeck_chart(r)

##Citations
st.subheader("Data Set Citation:")
st.markdown("Dutton, P. and G. Balazs. 2014. SWFSC juvenile loggerhead sea turtle tracking 2002-2005. Data downloaded from OBIS-SEAMAP (http://seamap.env.duke.edu/dataset/758) on 2025-05-12.")
st.markdown('---')
url = "https://turtle-snorkeling-oahu.com/what-is-the-fastest-turtle-in-the-water/"
st.markdown("Read about [Loggerhead Turtles Max Speed](%s)" % url)
st.caption("^Article used to help filter and calculate possible max speeds")
#st.markdown("possible image")
#st.markdown("https://commons.wikimedia.org/wiki/File:Loggerhead_Sea_Turtle-Caretta_caretta_%2817298266875%29.jpg")


#st.subheader("notes for me")
#st.markdown("add option to show all turtles at once (have different colors too)")
#st.markdown("add slider to show time")
#st.markdown("create option for animation")
#st.markdown('create a switch to turn on a point for the center of path (mean of lat/lon)')
#st.markdown("add distance between points by creating a column called distance since last")
#st.markdown('there is already a column called "time_diff" for df_selected that shows diference between times.^^')
