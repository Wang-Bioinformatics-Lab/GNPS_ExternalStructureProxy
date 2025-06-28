#!/bin/bash
source activate web && gunicorn -w 24 --threads=4 -b 0.0.0.0:5000 --timeout 60 main:app
