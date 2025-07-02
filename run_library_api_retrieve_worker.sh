#!/bin/bash

# Creating the tables
source activate rdkit && python create_tables.py

# Running the actual worker
source activate rdkit && celery -A tasks_library_api_retrieve_worker worker -c 1 -Q worker --loglevel INFO --max-tasks-per-child 1000

