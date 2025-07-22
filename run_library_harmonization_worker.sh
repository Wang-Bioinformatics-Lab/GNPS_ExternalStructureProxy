#!/bin/bash
source activate rdkit && \
    celery -A tasks_library_harmonization_worker worker \
    --loglevel INFO \
    -c 1 \
    -Q tasks_library_harmonization_worker \
    --max-tasks-per-child 4
