import pandas as pd
from taipy import Gui
import requests

def read_df(data_path: str):
    df = pd.read_csv(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

dataset = read_df("./dataset/dataset.csv")

# def fetch_map_data(week_number):
#     response = requests.get(f'http://localhost:8000/map-data?week={week_number}')
#     if response.status_code == 200:
#         return response.json()
#     else:
#         return None

def fetch_map_data(week_number):
    response = requests.get(f'http://localhost:8000/map-data?week={week_number}')
    if response.status_code == 200:
        map_data = response.json()
        # Format map data for the GUI
        formatted_map_data = f'<|{json.dumps(map_data)}|map|height=600px|width=100%|>'
        return formatted_map_data
    else:
        return None
    
def on_change(state, var_name: str, var_value):
    if var_name == "n_week":
        state.dataset_week = dataset[dataset["Date"].dt.isocalendar().week == var_value]
        map_data = fetch_map_data(var_value)
        if map_data:
            state.map_data = map_data
            
n_week = 40
dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]
map_data = fetch_map_data(n_week)

PAGE = f'''
# Pulse

Week number: <|{n_week}|>

<|{n_week}|slider|min=1|max=40|> 

## Bar Graph
<|{dataset_week}|chart|type=bar|x=Date|y=Value|height=100%|width=100%|>

## World Map
<|{map_data}|map|height=600px|width=100%|>

## Data Table
<|{dataset}|table|height=400px|width=95%|>
'''

Gui(page=PAGE).run(dark_mode=True)