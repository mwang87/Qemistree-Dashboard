# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import q2_qemistree
import os
from zipfile import ZipFile
from flask import Flask, send_from_directory
from bs4 import BeautifulSoup
import urllib.parse

import pandas as pd
from skbio import TreeNode

import requests

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)
server = app.server


app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.H1(children='Qemistree Dashboard'),
        html.Div(id='version', children="Version - Release_1"),
        html.Div([
            html.Label('Enter Qemistree Task ID:'),
            ], style=dict(display = 'inline-block')),
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
                value='class',
                style = dict(width = '40%', display = 'inline-block'),
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
                value='class',
                style = dict(width = '40%', display = 'inline-block'),
            ),
        html.Label('Label features by MS2 library match when available:'),
        dcc.RadioItems(id='ms2-label',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='False'
           ),
        html.Label('Label unannotated features by parent m/z:'),
        dcc.RadioItems(id='parent-mz',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='True'
           ),
        html.Label('Sample metadata column to make barplots:'),
        dcc.Input(id='group-samples-col', type='text', value='filename'),
        html.Label('Normalize feature abundances:'),
        dcc.RadioItems(id='normalize-features',
                options=[
                    {'label': 'Yes', 'value' : 'True'},
                    {'label': 'No', 'value' : 'False'},
                ],
                value='True'
           ),
        html.Button('Submit', id='button'),
        html.Div(id='compute-details'),
        html.Div(id='plot-download'),
        html.Div(id='plot-qiime2'),
        html.Div(id='plot-output')
    ]
)

# This enables parsing the URL to shove a task into the qemistree id
@app.callback(Output('qemistree-task', 'value'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if len(pathname) > 1:
        return pathname[1:]
    else:
        return "8fa3ab31a4e546539ae585e55d7c7139"

# This function will rerun at any 
@app.callback(
    [Output('compute-details', 'children'), Output('plot-download', 'children'), Output('plot-qiime2', 'children'), Output('plot-output', 'children')],
    [Input('button', 'n_clicks')],
    state = [State('qemistree-task', 'value'),
    State("prune-col", 'value'),
    State("plot-col", "value"),
    State("ms2-label", "value"),
    State("parent-mz", "value"),
    State("normalize-features", "value"),
    State("group-samples-col", "value")],
)
def process_qemistree(n_clicks, qemistree_task, prune_col, plot_col,
                      ms2_label, parent_mz, normalize_features, 
                      group_samples_col):
    url = 'https://gnps.ucsd.edu/ProteoSAFe/DownloadResultFile?task=' + qemistree_task
    
    # Metadata File
    output_filename = './output/{}_metadata.tsv'.format(qemistree_task)
    metadata = requests.get(url +  '&file=metadata_table/&block=main')
    if metadata.status_code == 200:
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

    # feature data with classyfire taxonomy
    output_filename = './output/{}_classified-feature-data.qza'.format(qemistree_task)
    fdata = "&file=output_folder/classified-feature-data.qza&block=main"
    fdata = requests.get(url+fdata)
    with open(output_filename, 'wb') as qza:
        qza.write(fdata.content)

    # tree pruning
    prune_cmd = ("qiime qemistree prune-hierarchy --i-feature-data ./output/{}_classified-feature-data.qza "
                "--i-tree ./output/{}_qemistree.qza --p-column {} "
                "--o-pruned-tree ./output/{}_qemistree-pruned.qza"
                ).format(qemistree_task, qemistree_task, prune_col, qemistree_task)
    os.system(prune_cmd)
    
    if os.path.isfile('./output/{}_metadata.tsv'.format(qemistree_task)):
        metadata_path = './output/{}_metadata.tsv'.format(qemistree_task)
    else:
        metadata_path = None
    
    group_table_path = None
    if metadata_path:
        # feature table grouping
        group_cmd = ("qiime feature-table group --i-table ./output/{}_merged-feature-table.qza "
                    "--p-axis 'sample' --m-metadata-file {} "
                    "--m-metadata-column '{}' --p-mode 'mean-ceiling' "
                    "--o-grouped-table ./output/{}_grouped-merged-feature-table.qza"
                    ).format(qemistree_task, metadata_path, group_samples_col, qemistree_task)
        os.system(group_cmd)
        group_table_path = './output/{}_grouped-merged-feature-table.qza'.format(qemistree_task)
    else:
        group_table_path = None
    
    # qemistree plotting
    output_qzv = "./output/{}_qemistree.qzv".format(qemistree_task)
    if group_table_path:
        plot_cmd = ("qiime qemistree plot --i-tree ./output/{}_qemistree-pruned.qza "
                    "--i-feature-metadata ./output/{}_classified-feature-data.qza "
                    "--i-grouped-table {} "
                    "--p-category '{}' --p-ms2-label {} --p-parent-mz {} --p-normalize-features {} "
                    "--o-visualization {}"
                    ).format(qemistree_task, qemistree_task, group_table_path, plot_col,
                            ms2_label, parent_mz, normalize_features, output_qzv)
    else:
        plot_cmd = ("qiime qemistree plot --i-tree ./output/{}_qemistree-pruned.qza "
                    "--i-feature-metadata ./output/{}_classified-feature-data.qza "
                    "--p-category '{}' --p-ms2-label {} --p-parent-mz {} --p-normalize-features {} "
                    "--o-visualization {}"
                    ).format(qemistree_task, qemistree_task, plot_col,
                            ms2_label, parent_mz, normalize_features, output_qzv)
    os.system(plot_cmd)

    # Opening the file
    itol_url = ""
    with ZipFile(output_qzv) as myzip:
        for name in myzip.namelist():
            if "index.html" in name:
                content_text = myzip.read(name)
                soup = BeautifulSoup(content_text, 'html.parser')
                itol_url = soup.h1.a.get("href")
                itol_url = itol_url.replace("http://", "https://")
    
    qemistree_qzv_source_url = "https://qemistree.ucsd.edu/download/{}".format(qemistree_task)
    cors_url = "https://cors-anywhere.herokuapp.com/{}".format(qemistree_qzv_source_url)
    qiime2_view_url = "https://view.qiime2.org/?src={}".format(urllib.parse.quote_plus(cors_url))
        
          
    return "A qemistree visualization for the task ID: {}. Features were filtered by '{}' & labeled by '{}'".format(qemistree_task, prune_col, plot_col), \
            html.A(html.Button('Download qzv'),href="/download/{}".format(qemistree_task)), \
            html.A(html.Button('View Qiime2 Viewer'),href=qiime2_view_url, target="_blank"), \
            html.Iframe(src=itol_url, height="800px", width="1200px")

@server.route("/download/<task>")
def download(task):
    """Serve a file from the upload directory."""
    return send_from_directory("./output", os.path.basename(task) + "_qemistree.qzv", as_attachment=True)

if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
