#!/bin/bash
source activate web && gunicorn -w 24 --threads=4 -b 0.0.0.0:5000 --timeout 60 main:app --max-requests 10000 --max-requests-jitter 1000 --access-logfile /app/logs/access.log
