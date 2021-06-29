#!/bin/bash

celery -A gnps_tasks worker -l info -B -c 1 -Q beat_worker --max-tasks-per-child 4