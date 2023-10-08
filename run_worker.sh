#!/bin/bash
source activate rdkit && celery -A tasks_worker worker -l info -c 1 -Q worker --loglevel INFO --max-tasks-per-child 1000

