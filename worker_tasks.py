from celery import Celery
import os
import json
import requests
import errno
from werkzeug.utils import secure_filename
import glob

import subprocess
from time import sleep
import shutil

celery_instance = Celery('tasks', backend='rpc://qemistree-mqrabbit', broker='pyamqp://qemistree-mqrabbit')

@celery_instance.task(time_limit=120)
def process_qemistree(gnps_task_id):
    #TODO: Do Things Here

    return ""
