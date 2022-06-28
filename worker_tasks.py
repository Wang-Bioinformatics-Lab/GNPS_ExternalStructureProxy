from celery import Celery
import glob
import sys
import os
import uuid
import requests
import pandas as pd
import utils
from celery.signals import worker_ready

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq//', )

@worker_ready.connect
def onstart(**k):
    #_gnps_list = utils.load_GNPS(library_names=["GNPS-LIBRARY"])
    _gnps_list, library_list_df = utils.load_GNPS()
    _gnps_list = utils.gnps_format_libraries(_gnps_list)

    gnps_df = pd.DataFrame(_gnps_list)
    gnps_df.to_feather("gnps_list.feather")

@celery_instance.task(time_limit=60)
def task_computeheartbeat():
    print("UP", file=sys.stderr, flush=True)
    return "Up"

from expiringdict import ExpiringDict
memory_cache = ExpiringDict(max_len=100, max_age_seconds=84600)

@celery_instance.task(time_limit=60)
def get_gnps_by_structure_task(smiles, inchi, inchikey):
    inchikey_from_smiles, inchikey_from_inchi = utils.get_inchikey(smiles, inchi)

    if "gnps_list" in memory_cache:
        gnps_list = memory_cache["gnps_list"]
    else:
        gnps_df = pd.read_feather("gnps_list.feather")
        gnps_df["InChIKey_smiles"] = gnps_df["InChIKey_smiles"].astype(str)
        gnps_df["InChIKey_inchi"] = gnps_df["InChIKey_inchi"].astype(str)

        gnps_list = gnps_df.to_dict(orient="records")
        memory_cache["gnps_list"] = gnps_list

    acceptable_key = set([inchikey, inchikey_from_smiles, inchikey_from_inchi])

    found_spectrum_list = []

    for gnps_spectrum in gnps_list:
        if len(gnps_spectrum["InChIKey_smiles"]) > 2 and gnps_spectrum["InChIKey_smiles"] in acceptable_key:
            found_spectrum_list.append(gnps_spectrum)
        elif len(gnps_spectrum["InChIKey_inchi"]) > 2 and gnps_spectrum["InChIKey_inchi"] in acceptable_key:
            found_spectrum_list.append(gnps_spectrum)
    
    return found_spectrum_list



celery_instance.conf.task_routes = {
    'worker_tasks.get_gnps_by_structure_task': {'queue': 'worker'},
}