import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

app = dash.Dash(__name__)

data = {
    'iso_alpha': ['USA', 'CAN', 'MEX'],
    'info': ['Info about USA', 'Info about Canada', 'Info about Mexico']
}

df = pd.DataFrame(data)

# Creating the choropleth figure
fig = px.choropleth(df, locations='iso_alpha', hover_name='info', projection='natural earth')

app.layout = html.Div([
    dcc.Graph(id='world-map', figure=fig),
    html.Div(id='country-info')  # This Div will display information based on interactions
])

@app.callback(
    Output('country-info', 'children'),
    [Input('world-map', 'hoverData'), Input('world-map', 'clickData')]
)
def display_interactive_data(hoverData, clickData):
    # Prioritize click data over hover data
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = 'No clicks yet'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'world-map' and clickData:
        info = clickData['points'][0]['hovertext']
        return html.P(f"Clicked info: {info}")
    elif hoverData:
        info = hoverData['points'][0]['hovertext']
        return html.P(f"Hover info: {info}")
    return "Hover over or click on a country to see information."

if __name__ == '__main__':
    app.run_server(debug=True)