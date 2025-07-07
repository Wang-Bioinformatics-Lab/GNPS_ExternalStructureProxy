from celery import Celery
import os
import json
import requests
import utils
import pandas as pd
import datetime
import subprocess

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

@celery_instance.task()
def generate_gnps_data():

    # TODO CALL THE NEXTFLOW HERE
    import sys
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXX", file=sys.stderr, flush=True)

    path_to_script  = "/app/pipelines/Library_Pulldown_Workflow/nf_workflow.nf"
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
    ])
    cmd = "export MAMBA_ALWAYS_YES='true' && {} >> {}".format(cmd, stdout_log)
    os.system(cmd)
    
    #### MatchMS/ML Prep Pipeline ####
    run_cleaning_pipeline.delay()

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

celery_instance.conf.task_routes = {
    'tasks_library_generation_worker.generate_gnps_data': {'queue': 'tasks_library_generation_worker'},
    'tasks_library_generation_worker.run_cleaning_pipeline': {'queue': 'tasks_library_generation_worker'},
}