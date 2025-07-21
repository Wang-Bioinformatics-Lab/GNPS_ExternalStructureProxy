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

@celery_instance.task(time_limit=561600, acks_late=True) # 6.5 Day Timeout
def run_cleaning_pipeline():
    print("Executing matchms cleaning pipeline", flush=True)

    utils.run_cleaning_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/cleaned_data/") # Blocking Call

    return "Finished matchms cleaning pipeline"


@celery_instance.task(time_limit=64_800, acks_late=True) # 6.5 Day Timeout
def run_cleaning_pipeline_library_specific(library):
    print(f"Executing cleaning pipeline for library: {library}", flush=True)

    output_dir = Path(f"/output/cleaned_libraries/{library}/")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    utils.run_cleaning_pipeline(f"/output/{library}.json", output_dir, no_massbank=True) # Blocking Call
    
    return f"Finished matchms cleaning pipeline for {library}"


celery_instance.conf.beat_schedule = {
    "harmonize_gnps_data": {
        "task": "tasks_library_harmonization_worker.run_cleaning_pipeline",
        "schedule": 604800   # Every 7 days (once per week)
    }
}

celery_instance.conf.task_routes = {
    'tasks_library_harmonization_worker.run_cleaning_pipeline': {'queue': 'tasks_library_harmonization_worker'},
    'tasks_library_harmonization_worker.run_cleaning_pipeline_library_specific': {'queue': 'tasks_library_harmonization_worker'},
}