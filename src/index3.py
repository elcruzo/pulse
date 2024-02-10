import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# Set initial week number
n_week = 40

# Define function to read DataFrame from CSV
def read_df(data_path: str):
    df = pd.read_csv(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

# Read dataset
dataset = read_df("/Users/joshuadonatien/Documents/pulse/src/dataset/dataset.csv")

# Filter dataset for the initial week number
dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]

# Define function to handle widget changes
def on_change(n_week):
    # Filter dataset based on selected week number
    dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]

    # Display the updated dataset
    st.dataframe(dataset_week)

# Define Streamlit app layout
st.title("Pulse")

# Week number slider
n_week = st.slider("Week number", min_value=1, max_value=40, value=n_week, step=1, key="week_slider")
path_to_html=""
# Display Folium Map using an iframe
components.iframe(f'<iframe src="http://localhost:5001/" width="100%" height="500" style="border:none;"></iframe>')

# Display bar graph
st.bar_chart(dataset_week.set_index("Date")["Value"])

# Display data table
st.dataframe(dataset)

# Call on_change function when the week number slider value changes
on_change(n_week)
