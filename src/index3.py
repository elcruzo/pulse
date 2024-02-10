from taipy import Gui
import pandas as pd
# import folium


n_week = 40
map_url = "http://localhost:5001/"
iframe_html = f'<iframe src="{map_url}" width="100%" height="500" style="border:none;"></iframe>'

# map_url = "http://127.0.0.1:5500/Hacklytics/pulse/src/static/map.html"
# iframe_html = f'<iframe src="{map_url}" width="100%" height="500" style="border:none;"></iframe>'


def read_df(data_path: str):
    df = pd.read_csv(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

dataset = read_df("./dataset/dataset.csv")
dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]


def on_change(state, var_name: str, var_value):
    if var_name == "n_week":
        state.dataset_week = dataset[dataset["Date"].dt.isocalendar().week == var_value]


# state.n_week = 10
# <|{var_name|visual_element|param_1=param_1|param_2=param_2|...|>
PAGE = '''
# Pulse

Week number: <|{n_week}|>

<|{n_week}|slider|min=1|max=40|> 

## Folium Map
<|{iframe_html}|>

## Bar Graph
<|{dataset_week}|chart|type=bar|x=Date|y=Value|height=100%|width=100%|>

## Data Table
<|{dataset}|table|height=400px|width=95%|>

'''
Gui(page=PAGE).run(dark_mode=True)
