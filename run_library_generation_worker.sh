#!/bin/bash
source activate rdkit && celery -A tasks_library_generation_worker worker --loglevel INFO -B -c 1 -Q tasks_library_generation_worker --max-tasks-per-child 4