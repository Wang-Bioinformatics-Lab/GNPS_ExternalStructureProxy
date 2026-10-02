from celery import Celery
import utils

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )


@celery_instance.task(time_limit=561600, acks_late=True)  # 6.5 days
def run_cleaning_pipeline():
    # Keep the task name registered so older queued messages cannot launch cleaning.
    utils.run_cleaning_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/cleaned_data/")

@celery_instance.task(time_limit=64800, acks_late=True)  # 18 hours
def run_cleaning_pipeline_library_specific(library):
    utils.run_cleaning_pipeline(f"/output/{library}.json", f"/output/cleaned_libraries/{library}/", no_massbank=True)


# No scheduled cleaning: the published snapshots are frozen.
celery_instance.conf.beat_schedule = {}

celery_instance.conf.task_routes = {
    'tasks_library_harmonization_worker.run_cleaning_pipeline': {'queue': 'tasks_library_harmonization_worker'},
    'tasks_library_harmonization_worker.run_cleaning_pipeline_library_specific': {'queue': 'tasks_library_harmonization_worker'},
}
