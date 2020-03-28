#!/bin/bash

celery -A worker_tasks worker -l info -c 1
