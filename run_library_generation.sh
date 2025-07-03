#!/bin/bash
source activate rdkit && celery -A task_library_generation worker --loglevel INFO -B -c 1 -Q beat_worker --max-tasks-per-child 4