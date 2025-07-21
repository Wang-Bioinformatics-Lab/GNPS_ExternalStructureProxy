from celery import Celery
from pathlib import Path
import utils

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )


@celery_instance.task(time_limit=561600, acks_late=True)  # 6.5 days
def run_cleaning_pipeline():
    print("Executing matchms cleaning pipeline", flush=True)
    utils.run_cleaning_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/cleaned_data/")
    return "Finished matchms cleaning pipeline"

@celery_instance.task(time_limit=64800, acks_late=True)  # 18 hours
def run_cleaning_pipeline_library_specific(library):
    print(f"Executing cleaning pipeline for library: {library}", flush=True)
    output_dir = Path(f"/output/cleaned_libraries/{library}/")
    output_dir.mkdir(parents=True, exist_ok=True)
    utils.run_cleaning_pipeline(f"/output/{library}.json", output_dir, no_massbank=True)
    return f"Finished matchms cleaning pipeline for {library}"

# Schedule using beat
celery_instance.conf.beat_schedule = {
    "harmonize_gnps_data": {
        "task": "tasks_library_harmonization_worker.run_cleaning_pipeline",
        "schedule": 604800,  # every 7 days
        "options": {"queue": "tasks_library_harmonization_worker"},
    }
}

celery_instance.conf.task_routes = {
    'tasks_library_harmonization_worker.run_cleaning_pipeline': {'queue': 'tasks_library_harmonization_worker'},
    'tasks_library_harmonization_worker.run_cleaning_pipeline_library_specific': {'queue': 'tasks_library_harmonization_worker'},
}
