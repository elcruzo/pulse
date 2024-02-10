from taipy import Gui
import pandas as pd


n_week = 40

def read_df(data_path: str):
    df = pd.read_csv(data_path)
    return df

dataset = read_df("./dataset/dataset.csv")

# <|{var_name|visual_element|param_1=param_1|param_2=param_2|...|>
page = '''
# Pulse

Week number: <|{n_week}|>

<|{n_week}|slider|min=1|max=40|> 

## Data Table
<|{dataset}|table|height=400px|width=95%|>


## Bar Graph
<|{dataset}|chart|type=bar|x=Date|y=Value|>
'''
Gui(page=page).run(dark_mode=True)
