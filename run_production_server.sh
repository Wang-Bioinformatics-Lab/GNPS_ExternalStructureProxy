#!/bin/bash
source activate rdkit && gunicorn -w 12 --threads=4 -b 0.0.0.0:5000 --timeout 600 main:app
