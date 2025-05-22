#!/bin/bash
source activate rdkit && \
        celery  -A tasks_api_request_worker worker \
                --loglevel INFO \
                -B \
                -c 1 \
                -Q api_request_worker \
                --max-tasks-per-child 4