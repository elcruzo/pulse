from taipy import Gui
from taipy.gui import Html
import pandas as pd
# import folium

n_week = 40
map_url = "index.html"
iframe_html = f'<iframe src="{map_url}" width="100%" height="500" style="border:none;"></iframe>'

html_path = "index.html"
with open(html_path, "r") as f:
    html_content = f.read()

html_component = Html(html_content)

map_component = Html(iframe_html)

def read_df(data_path: str):
    df = pd.read_csv(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

stockdataset = read_df("./dataset/stock_data.csv")
dataset = read_df("./dataset/dataset.csv")
dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]


def on_change(state, var_name: str, var_value):
    if var_name == "n_week":
        state.dataset_week = dataset[dataset["Date"].dt.isocalendar().week == var_value]

PAGE = '''
# Pulse

Week number: <|{n_week}|>

<|{n_week}|slider|min=1|max=40|>

## Performance Analysis After Natural Disasters
<|{stockdataset}|table|height=400px|width=95%|>

## Trend Graph
<|{dataset_week}|chart|type=bar|x=Date|y=Value|height=100%|width=100%|>

'''

Gui(page=PAGE).run(dark_mode=True)
