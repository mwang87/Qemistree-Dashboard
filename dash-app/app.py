# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import q2_qemistree
from q2_qemistree import prune_hierarchy
from qiime2 import Artifact
import pandas as pd
from skbio import TreeNode

import requests

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


app.layout = html.Div(
    [
        html.Label('Enter Qemistree Task ID:'),
        dcc.Input(id='qemistree-task', type="text", value='8fa3ab31a4e546539ae585e55d7c7139'),
        html.Label('Select feature metadata column to filter qemistree:'),
        dcc.Dropdown(id='prune-col',
                options=[
                    {'label': 'All Structures', 'value' : 'smiles'},
                    {'label': 'MS2 Structures', 'value' : 'ms2_smiles'},
                    {'label': 'CSI:FingerID Structures', 'value' : 'csi_smiles'},
                    {'label': 'Kingdom', 'value' : 'kingdom'},
                    {'label': 'Superclass', 'value' : 'superclass'},
                    {'label': 'Class', 'value' : 'class'},
                    {'label': 'Subclass', 'value' : 'subclass'},
                    {'label': 'Direct Parent', 'value' : 'direct_parent'}
                ],
                value='class'
            ),
        html.Div(id='prune-output'),
        html.Label('Select feature metadata column to label features:'),
        dcc.Dropdown(id='plot-col',
                options=[
                    {'label': 'Kingdom', 'value' : 'kingdom'},
                    {'label': 'Superclass', 'value' : 'superclass'},
                    {'label': 'Class', 'value' : 'class'},
                    {'label': 'Subclass', 'value' : 'subclass'},
                    {'label': 'Direct Parent', 'value' : 'direct_parent'}
                ],
                value='class'
            ),
        html.Label('Label features by MS2 library match when available:'),
        dcc.RadioItems(id='ms2-label',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='True'
           ),
        html.Label('Label unannotated features by parent m/z:'),
        dcc.RadioItems(id='parent-mz',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='True'
           ),
        html.Div(id='plot-output')
    ]
)

@app.callback(
    Output('prune-output', 'children'),
    [Input('qemistree-task', 'value'), Input('prune-col', 'value')],
)
def process_qemistree(qemistree_task, prune_col):
    url = 'https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task=' + qemistree_task
    # TODO: where should we save task outputs if at all

    # hashed feature table
    table = '&file=output_folder/merged-feature-table.qza&block=main'
    ftable = requests.get(url + table)
    with open('merged-feature-table.qza', 'wb') as qza:
        qza.write(ftable.content)
    ftable = Artifact.load('merged-feature-table.qza').view(pd.DataFrame)

    # full tree
    tree = "&file=output_folder/qemistree.qza&block=main"
    tree = requests.get(url+tree)
    with open("qemistree.qza", "wb") as qza:
        qza.write(tree.content)
    tree = Artifact.load('qemistree.qza').view(TreeNode)

    # feature data with classyfire taxonomy
    fdata = "&file=output_folder/classified-feature-data.qza&block=main"
    fdata = requests.get(url+fdata)
    with open("classified-feature-data.qza", "wb") as qza:
        qza.write(fdata.content)
    fdata = Artifact.load('classified-feature-data.qza').view(pd.DataFrame)

    pruned_tree = prune_hierarchy(fdata, tree, prune_col)
    ntips = len([tip for tip in pruned_tree.tips()])


    return 'The number of features after filtering qemistree: %s' %ntips

    @app.callback(
        Output("plot-output", "children"),
        [Input("plot-col", "value"), Input("ms2-label", "value"),
         Input("parent-mz", "value")],
    )
    def update_output(plot_col, ms2_label, parent_mz):
        # TODO figure out how to get sample metadata
        # TODO call plot
        return feature_col, ms2_label, parent_mz

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
