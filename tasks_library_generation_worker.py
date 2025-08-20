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
    library_names = read_csv("/app/library_names.tsv", names=['library', 'type'], dtype=str)  # Named as a tsv, is a csv
    library_names['json_name'] = library_names['library'].str.strip() + ".json"
    name_type_mapping = library_names.set_index('json_name')['type'].to_dict()

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
    run_cleaning_pipeline.apply_async(expires=48*60*60) # Must start within 48 hours
    # Propagated ("GNPS-PROPOGATED") libs
    output_dir = Path("/output/")

    for file in sorted(list(output_dir.glob("*.json"))):
        file_name = file.name
        library_name = file.stem
        if str(library_name).startswith("CMMC-REFRAME"):
            # Drop the CMMC (n.b. do not drop it from the library_name)
            file_name = file_name.replace("CMMC-REFRAME-", "REFRAME-")

        if name_type_mapping.get(file_name) == "GNPS-PROPOGATED":
            print(f"Processing file: {file_name}", file=sys.stderr, flush=True)

            run_cleaning_pipeline_library_specific.apply_async((library_name,), expires=72*60*60)    # Must start within 72 hours
        else:
            print(f"generate_gnps_data() library harmonization is not queuing file: {file.name} - not a GNPS-PROPOGATED library", file=sys.stderr, flush=True)

    return ""

celery_instance.conf.task_routes = {
    'tasks_library_generation_worker.generate_gnps_data': {'queue': 'tasks_library_generation_worker'},
}