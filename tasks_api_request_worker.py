import sys
from celery import Celery
import redis
from redis.exceptions import LockError
import os
from pathlib import Path
import shutil
import subprocess

from models import *

from celery.signals import worker_ready

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

redis_client = redis.Redis(host='externalstructureproxy-redis', port=6379, db=0)

RUN_EVERY = 86400  # 24 hours
TASK_TIME_LIMIT = 604800 # One week

@celery_instance.task(time_limit=TASK_TIME_LIMIT)
def task_structure_classification():
    """
    This task enriches the structure database with information from multiple APIs including
    classyfire, NPclassyfire and ChemInfoService.

    This task runs periodically, rather than triggered, and may be long-running if a significant number
    of new structures are added to the database.
    """

    # DEBUG
    # redis_client.delete("structure_classification_lock")

    # Lock times out synchronously with task time limit
    lock = redis_client.lock("structure_classification_lock", timeout=TASK_TIME_LIMIT, blocking_timeout=5)
    got_lock = lock.acquire(blocking=True)
    if not got_lock:
        print("Another instance of task_structure_classification() already running. Exiting.", file=sys.stderr, flush=True)
        return "Task already running"
    
    try:
        path_to_script = "/app/pipelines/structureClassification/nf_workflow.nf"
        path_to_config = "/app/pipelines/structureClassification/nextflow.config"
        input_path = Path("/output/cleaned_data/ALL_GNPS_cleaned.csv")
        output_path_static = Path("/output/structure_classification")
        output_path = Path("/internal-outputs/structure_classification")

        if not input_path.exists():
            print(f"Input file {input_path} does not exist. Exiting task.", file=sys.stderr, flush=True)
            return "Input file not found"

        if not os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)

        # Use a temp copy of the input file
        temp_input_path = output_path / "ALL_GNPS_cleaned.csv"
        shutil.copy(input_path, temp_input_path)

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

        subprocess.run([
            "/nextflow", "run", path_to_script,
            "--structure_csv", str(params['structure_csv']),
            "--output_directory_Classyfire", str(params['output_directory_Classyfire']),
            "--output_directory_Npclassifier", str(params['output_directory_Npclassifier']),
            "--output_directory_ChemInfoService", str(params['output_directory_ChemInfoService']),
            "--log_Classyfire", str(params['log_Classyfire']),
            "--log_Npclassifier", str(params['log_Npclassifier']),
            "--log_ChemInfoService", str(params['log_ChemInfoService']),
            "-c", path_to_config,
        ])

        # Print the output of /nextflow log to sys.stderr
        log_output = subprocess.run(["/nextflow", "log", path_to_script], capture_output=True, text=True)


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