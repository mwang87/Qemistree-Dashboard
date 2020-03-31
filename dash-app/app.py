# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import q2_qemistree
import os

import pandas as pd
from skbio import TreeNode

import requests

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server


app.layout = html.Div(
    [
        html.H1(children='Qemistree Dashboard'),
        html.Div([
            html.Label('Enter Qemistree Task ID:'),
        ], style={'display': 'inline-block'}),
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
        html.Label('Normalize feature abundances:'),
        dcc.RadioItems(id='normalize-features',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='True'
           ),
        html.Label('Sample metadata column to make barplots:'),
        dcc.Input(id='group-samples-col', type='text', value='filename'),
        html.Div(id='plot-output')
    ]
)

# This function will rerun at any 
@app.callback(
    Output('plot-output', 'children'),
    [Input('qemistree-task', 'value'), 
    Input('prune-col', 'value'), 
    Input("plot-col", "value"), 
    Input("ms2-label", "value"),
    Input("parent-mz", "value"),
    Input("normalize-features", "value"),
    Input("group-samples-col", "value")],
)
def process_qemistree(qemistree_task, prune_col, plot_col, 
                      ms2_label, parent_mz, normalize_features, 
                      group_samples_col):
    url = 'https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task=' + qemistree_task

    # Metadata File
    output_filename = './output/{}_metadata.tsv'.format(qemistree_task)
    metadata = requests.get(url +  '&file=metadata_table/&block=main')
    with open(output_filename, 'wb') as output_file:
        output_file.write(metadata.content)

    # hashed feature table
    output_filename = './output/{}_merged-feature-table.qza'.format(qemistree_task)
    table = '&file=output_folder/merged-feature-table.qza&block=main'
    ftable = requests.get(url + table)
    with open(output_filename, 'wb') as qza:
        qza.write(ftable.content)

    # full tree
    output_filename = './output/{}_qemistree.qza'.format(qemistree_task)
    tree = "&file=output_folder/qemistree.qza&block=main"
    tree = requests.get(url+tree)
    with open(output_filename, 'wb') as qza:
        qza.write(tree.content)
    # tree = Artifact.load(output_filename).view(TreeNode)

    # feature data with classyfire taxonomy
    output_filename = './output/{}_classified-feature-data.qza'.format(qemistree_task)
    fdata = "&file=output_folder/classified-feature-data.qza&block=main"
    fdata = requests.get(url+fdata)
    with open(output_filename, 'wb') as qza:
        qza.write(fdata.content)
    # fdata = Artifact.load(output_filename).view(pd.DataFrame)

    # tree pruning
    prune_cmd = ("qiime qemistree prune-hierarchy --i-feature-data ./output/{}_classified-feature-data.qza "
                 "--i-tree ./output/{}_qemistree.qza --p-column {} "
                 "--o-pruned-tree ./output/{}_qemistree-pruned.qza"
                ).format(qemistree_task, qemistree_task, prune_col, qemistree_task)
    os.system(prune_cmd)
    
    # feature table grouping
    group_cmd = ("qiime feature-table group --i-table ./output/{}_merged-feature-table.qza "
                 "--p-axis 'sample' --m-metadata-file ./output/{}_metadata.tsv "
                 "--m-metadata-column '{}' --p-mode 'mean-ceiling' "
                 "--o-grouped-table ./output/{}_grouped-merged-feature-table.qza"
                ).format(qemistree_task, qemistree_task, group_samples_col, qemistree_task)
    os.system(group_cmd)
    
    # qemistree plotting
    plot_cmd = ("qiime qemistree plot --i-tree ./output/{}_qemistree-pruned.qza "
                "--i-feature-metadata ./output/{}_classified-feature-data.qza "
                "--i-grouped-table ./output/{}_grouped-merged-feature-table.qza "
                "--p-category '{}' --p-ms2-label {} --p-parent-mz {} --p-normalize-features {} "
                "--o-visualization ./output/{}_qemistree.qzv"
                ).format(qemistree_task, qemistree_task, qemistree_task, plot_col,  
                         ms2_label, parent_mz, normalize_features, qemistree_task)
    os.system(plot_cmd)   


if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
