# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import requests

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


app.layout = html.Div(
    [
        dcc.Input(id="qemistreetask", type="text", value=""),
        html.Div(id="qesmitree-output"),
        dcc.Input(id="input-1", type="text", value="Montréal"),
        dcc.Input(id="input-2", type="text", value="Canada"),
        html.Div(id="number-output"),
    ]
)

@app.callback(
    Output("number-output", "children"),
    [Input("input-1", "value"), Input("input-2", "value")],
)
def update_output(input1, input2):
    return u'Input 1 is "{}" and Input 2 is "{}"'.format(input1, input2)

@app.callback(
    Output("qesmitree-output", "children"),
    [Input("qemistreetask", "value")],
)
def process_qemistree(qemistree_task):
    url = "https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task=8500452e56804441830a590f0a3d961b&file=output_folder/feature-table.qza&block=main"
    return url

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")