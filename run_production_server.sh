#!/bin/bash

gunicorn -w 1 --threads=4 -b 0.0.0.0:5000 --timeout 3600 main:app
