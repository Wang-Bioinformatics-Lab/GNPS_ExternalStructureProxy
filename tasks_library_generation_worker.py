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

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

@celery_instance.task()
def generate_gnps_data():

    # TODO CALL THE NEXTFLOW HERE
    import sys
    print("RUNNING GNPS GENERATE WORKFLOW", file=sys.stderr, flush=True)

    path_to_script  = "/app/pipelines/Library_Pulldown_Workflow/nf_workflow.nf"
    work_dir = "/app/pipelines/Library_Pulldown_Workflow/work"

    stdout_log = "/output/library_generation_nextflow.log"
    output_directory = "/output"
    cache_summary_location = "/output/library_summaries"
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory, exist_ok=True)
    
    # Use subprocess to run a nextflow script to generate all everything we need
    cmd = " ".join([
        "nextflow", "run", path_to_script, 
        "-c", "/app/pipelines/Library_Pulldown_Workflow/nextflow_external.config",
        "--publishdir", output_directory,
        "--cachelibrariesdir", cache_summary_location,
        "-w". work_dir,
    ])
    cmd = "export MAMBA_ALWAYS_YES='true' && {} >> {}".format(cmd, stdout_log)
    os.system(cmd)
    
    #### MatchMS/ML Prep Pipeline ####
    run_cleaning_pipeline.delay()
    # Multiplex libraries
    output_dir = Path("/output/")
    all_pattern = re.compile(r"MULTIPLEX-SYNTHESIS-LIBRARY-ALL-PARTITION-\d+\.json$")
    filtered_pattern = re.compile(r"MULTIPLEX-SYNTHESIS-LIBRARY-FILTERED-PARTITION-\d+\.json$")

    for file in output_dir.iterdir():
        if all_pattern.match(file.name):
            library_name = file.stem  # remove .json
            run_cleaning_pipeline_library_specific.delay(library_name)
        elif filtered_pattern.match(file.name):
            library_name = file.stem
            run_cleaning_pipeline_library_specific.delay(library_name)

    return ""

    
    

@celery_instance.task(time_limit=64_800) # 18 Hour Timeout
def run_cleaning_pipeline():
    utils.run_cleaning_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/cleaned_data/")
    
    return "Finished matchms cleaning pipeline"

celery_instance.conf.beat_schedule = {
    "generate_gnps_data": {
        "task": "tasks_library_generation_worker.generate_gnps_data",
        "schedule": 86400   # Every 24 hours
    }
}

@celery_instance.task(time_limit=64_800) # 18 Hour Timeout
def run_cleaning_pipeline_library_specific(library):
    print(f"Executing cleaning pipeline for library: {library}", flush=True)

    output_dir = Path(f"/output/cleaned_libraries/{library}/")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    utils.run_cleaning_pipeline(f"/output/{library}.json", output_dir, no_massbank=True)
    
    return f"Finished matchms cleaning pipeline for {library}"

celery_instance.conf.task_routes = {
    'tasks_library_generation_worker.generate_gnps_data': {'queue': 'tasks_library_generation_worker'},
    'tasks_library_generation_worker.run_cleaning_pipeline': {'queue': 'tasks_library_generation_worker'},
    'tasks_library_generation_worker.run_cleaning_pipeline_library_specific': {'queue': 'tasks_library_generation_worker'},
}