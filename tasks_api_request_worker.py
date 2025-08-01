import sys
from celery import Celery
import redis
from redis.exceptions import LockError
import os
from pathlib import Path
import shutil
import subprocess
import pandas as pd

from models import *

from celery.signals import worker_ready

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

redis_client = redis.Redis(host='externalstructureproxy-redis', port=6379, db=0)

RUN_EVERY = 86400  # 24 hours
TASK_TIME_LIMIT = 604800 # One week

@celery_instance.task(time_limit=TASK_TIME_LIMIT, acks_late=True, )
def task_structure_classification():
    """
    This task enriches the structure database with information from multiple APIs including
    classyfire, NPclassyfire and ChemInfoService.

    This task runs periodically, rather than triggered, and may be long-running if a significant number
    of new structures are added to the database.
    """

    # Lock times out synchronously with task time limit
    lock = redis_client.lock("structure_classification_lock", timeout=TASK_TIME_LIMIT, blocking_timeout=5)
    got_lock = lock.acquire(blocking=True)
    if not got_lock:
        print("Another instance of task_structure_classification() already running. Exiting.", file=sys.stderr, flush=True)
        return "Task already running"
    
    try:
        path_to_script = "/app/pipelines/structureClassification/nf_workflow.nf"
        path_to_config = "/app/pipelines/structureClassification/nextflow.config"
        input_paths = [Path("/output/cleaned_data/ALL_GNPS_cleaned.csv")]
        # Get other inputs from haromized libraries
        other_haromized_libraries = Path("/output/cleaned_libraries/").glob("**/*.csv")
        input_paths.extend(other_haromized_libraries)
        output_path_static = Path("/output/structure_classification")
        output_path = Path("/internal-outputs/structure_classification")

        # Ensure input files exist
        for input_path in input_paths:
            if not input_path.exists():
                print(f"Input file {input_path} does not exist. Exiting task.", file=sys.stderr, flush=True)
                return "Input file not found"

        log_output_path = Path("/output/structure_classification.log")

        if not os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)

        # Use a temp copy of the input file
        temp_input_path = output_path / "cleaned_data.csv"
        # Merge all input files
        df = pd.DataFrame()
        for input_path in input_paths:
            if input_path.exists():
                df = pd.concat([df, pd.read_csv(input_path)], ignore_index=True)

        df.drop_duplicates(subset=["spectrum_id"], inplace=True)
        df.to_csv(temp_input_path, index=False)

        params = {
            'structure_csv': temp_input_path,
            'output_directory_Classyfire': output_path / "Classyfire",
            'output_directory_Npclassifier': output_path / "Npclassifier",
            'output_directory_ChemInfoService': output_path / "ChemInfoService",
            'log_Classyfire': output_path / "Classyfire.log",
            'log_Npclassifier': output_path / "Npclassifier.log",
            'log_ChemInfoService': output_path / "ChemInfoService.log",
            'report_path': output_path_static / "api_caching_report.html",
        }

        cmd = " ".join([
            "nextflow", "run", path_to_script,
            "--structure_csv", str(params['structure_csv']),
            "--output_directory_Classyfire", str(params['output_directory_Classyfire']),
            "--output_directory_Npclassifier", str(params['output_directory_Npclassifier']),
            "--output_directory_ChemInfoService", str(params['output_directory_ChemInfoService']),
            "--log_Classyfire", str(params['log_Classyfire']),
            "--log_Npclassifier", str(params['log_Npclassifier']),
            "--log_ChemInfoService", str(params['log_ChemInfoService']),
            "-c", path_to_config,
        ])

        cmd = "export MAMBA_ALWAYS_YES='true' && {} >> {}".format(cmd, log_output_path)
        os.system(cmd)

        # Output to static output
        if not os.path.isdir(output_path_static):
            os.makedirs(output_path_static, exist_ok=True)
        shutil.copytree(output_path, output_path_static, dirs_exist_ok=True)

        return "Task completed successfully"

    finally:
        # Clean up temp input file
        if temp_input_path.exists():
            os.remove(temp_input_path)
        lock.release()
                    

celery_instance.conf.beat_schedule = {  # No schedule for now
    "structure_classification_daily": {
        "task": "tasks_api_request_worker.task_structure_classification",
        "schedule": RUN_EVERY
    }
}

celery_instance.conf.task_routes = {
    'tasks_api_request_worker.task_structure_classification': {'queue': 'api_request_worker'},
}