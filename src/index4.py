from taipy import Gui
from taipy.gui import Html
import pandas as pd

class HtmlFile:
    def __init__(self, html_path):
        self.html_path = html_path

    def to_html(self):
        with open(self.html_path, 'r') as f:
            html_content = f.read()
        return html_content

n_week = 40

# Assuming "html_path" is the path to your HTML file
html_path = "hello.html"
html_component = HtmlFile(html_path)

def read_df(data_path: str):
    df = pd.read_csv(data_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df

dataset = read_df("./dataset/dataset.csv")
dataset_week = dataset[dataset["Date"].dt.isocalendar().week == n_week]

PAGE = '''
# Pulse

Week number: <|{n_week}|>

<|{n_week}|slider|min=1|max=40|> 

## World Map
<|{html_component}|>

## Bar Graph
<|{dataset_week}|chart|type=bar|x=Date|y=Value|height=100%|width=100%|>

## Data Table
<|{dataset}|table|height=400px|width=95%|>
'''

Gui(page=PAGE).run(dark_mode=True)
