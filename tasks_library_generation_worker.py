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
from tasks_library_harmonization_worker import run_cleaning_pipeline, run_cleaning_pipeline_library_specific

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
    
    #### MatchMS/ML Prep Pipeline ####
    run_cleaning_pipeline.apply_async(expires=48*60*60)
    # Multiplex libraries
    output_dir = Path("/output/")
    all_pattern = re.compile(r"MULTIPLEX-SYNTHESIS-LIBRARY-ALL-PARTITION-\d+\.json$")
    filtered_pattern = re.compile(r"MULTIPLEX-SYNTHESIS-LIBRARY-FILTERED-PARTITION-\d+\.json$")

    for file in output_dir.iterdir():
        if all_pattern.match(file.name):
            library_name = file.stem  # remove .json
            run_cleaning_pipeline_library_specific.apply_async((library_name,), expires=48*60*60)
        elif filtered_pattern.match(file.name):
            library_name = file.stem
            run_cleaning_pipeline_library_specific.apply_async((library_name,), expires=48*60*60)

    return ""

celery_instance.conf.task_routes = {
    'tasks_library_generation_worker.generate_gnps_data': {'queue': 'tasks_library_generation_worker'},
}