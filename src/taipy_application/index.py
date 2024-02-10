# import pandas as pd

# def get_data(path_to_csv: str):
#     dataset = pd.read_csv(path_to_csv)
#     dataset["Date"] = pd.to_datetime(dataset["Date"])
#     return dataset

# path_to_csv = "dataset.csv"
# dataset = get_data(path_to_csv)

from taipy import Gui

Gui(page="Hello World").run(dark_mode=False)