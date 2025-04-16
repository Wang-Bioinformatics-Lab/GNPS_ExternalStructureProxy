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

    # Lock times out synchronously with task time limit
    lock = redis_client.lock("structure_classification_lock", timeout=TASK_TIME_LIMIT, blocking_timeout=5)
    got_lock = lock.acquire(blocking=True)
    if not got_lock:
        print("Another instance of task_structure_classification() already running. Exiting.")
        return
    
    try:
        path_to_script = ""
        input_path = Path("/output/cleaned_data/ALL_GNPS_cleaned.csv")
        output_path = Path("/output/structure_classification")

        if not input_path.exists():
            print(f"Input file {input_path} does not exist. Exiting task.")
            return

        if not os.path.isdir(output_path):
            os.makedirs(output_path, exist_ok=True)

        # Use a temp copy of the input file
        temp_input_path = output_path / "ALL_GNPS_cleaned.csv"
        shutil.copy(input_path, temp_input_path)

        params = {
            'structure_csv': temp_input_path,
            'output_directory_Classyfire': output_path / "Classyfire",
            'output_directory_Npclassifier': output_path / "NPClassyfire",
            'output_directory_ChemInfoService': output_path / "ChemInfoService",
            'log_Classyfire': output_path / "Classyfire" / "log.txt",
            'log_Npclassifier': output_path / "NPClassyfire" / "log.txt",
            'log_ChemInfoService': output_path / "ChemInfoService" / "log.txt",
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
        ])

    finally:
        lock.release()
                    

celery_instance.conf.beat_schedule = {
    "structure_classification_daily": {
        "task": "tasks_api_request_worker.task_structure_classification",
        "schedule": RUN_EVERY
    }
}
