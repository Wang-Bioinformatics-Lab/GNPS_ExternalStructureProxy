from celery import Celery
import os
import json
import requests
import utils
import pandas as pd
import datetime
import subprocess
from pathlib import Path
import re
from pandas import read_csv

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

@celery_instance.task()
def generate_gnps_data():

    # TODO CALL THE NEXTFLOW HERE
    import sys
    print("RUNNING GNPS GENERATE WORKFLOW", file=sys.stderr, flush=True)

    path_to_script  = "/app/pipelines/Library_Pulldown_Workflow/nf_workflow.nf"
    work_dir = "/data/gscratch/web-services/Library_Pulldown_Workflow/work"
    stdout_log = "/output/library_generation_nextflow.log"
    nextflow_config = "/app/pipelines/Library_Pulldown_Workflow/nextflow_external.config"
    output_directory = "/output"

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory, exist_ok=True)
    
    # Use subprocess to run a nextflow script to generate all everything we need
    cmd = " ".join([
        "nextflow", "run", path_to_script, 
        "-c", nextflow_config,
        "-w", work_dir,
    ])
    cmd = "export MAMBA_ALWAYS_YES='true' && {} >> {}".format(cmd, stdout_log)
    os.system(cmd)
    
    # ML/matchms cleaning triggers were removed: preprocessed downloads are frozen.
    return ""

celery_instance.conf.task_routes = {
    'tasks_library_generation_worker.generate_gnps_data': {'queue': 'tasks_library_generation_worker'},
}