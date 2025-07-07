#!/bin/bash

source activate web && gunicorn -w 24 --threads=4 -b 0.0.0.0:5000 --timeout 10 main:app \
--max-requests 100000 --max-requests-jitter 10000 \
--access-logfile /app/logs/access.log