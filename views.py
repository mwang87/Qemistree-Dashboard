# views.py
from flask import abort, jsonify, render_template, request, redirect, url_for, make_response, send_from_directory
import uuid

from app import app
from worker_tasks import process_qemistree

from werkzeug.utils import secure_filename
import os
import glob
import json
import requests
import random
import shutil
import urllib
from time import sleep
import glob

import util

@app.route('/', methods=['GET'])
def homepage():
    response = make_response(render_template('qemistree.html'))
    response.set_cookie('sessionid', str(uuid.uuid4()))
    response.set_cookie('uploadedFiles', "False")
    return response

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{}"

@app.route('/qemistree', methods=['POST'])
def analyzeqemistree():
    sessionid = request.cookies.get('sessionid')

    # Getting post parameters
    task = request.values.get("task")
    
    result = process_qemistree.delay(task)

    while(1):
        if result.ready():
            break
        sleep(3)
    result = result.get()

    return sessionid
