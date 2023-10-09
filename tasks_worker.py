from celery import Celery
import glob
import sys
import os
import uuid
import requests
import pandas as pd
import utils
import datetime
import json

from models import *

from celery.signals import worker_ready

celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

@worker_ready.connect
def onstart(**k):
    #_gnps_list = utils.load_GNPS(library_names=["GNPS-LIBRARY"])
    #_gnps_list, library_list_df = utils.load_GNPS()
    #_gnps_list = utils.gnps_format_libraries(_gnps_list)

    #gnps_df = pd.DataFrame(_gnps_list)
    #gnps_df.to_feather("gnps_list.feather")

    print("On Start, doing nothing now", file=sys.stderr, flush=True)

@celery_instance.task(time_limit=60)
def task_computeheartbeat():
    print("UP", file=sys.stderr, flush=True)
    return "Up"


# Here we need to update the library entry for GNPS the library entry
@celery_instance.task(time_limit=60)
def task_updategnpslibrary(accession):
    # We don't decide if we should, someone else decides, here we just do it

    # What time is it now
    now = datetime.datetime.now()
    # making into string
    now = now.strftime("%Y-%m-%d %H:%M:%S")


    _library_entry = _get_gnps_spectrum(accession)
    json_entry = json.loads(_library_entry)

    # Get the library entry
    try:
        library_entry = LibraryEntry.get(LibraryEntry.libraryaccession == accession)

        # update the json
        library_entry.libraryjson = _library_entry
        library_entry.lastupdate = now

        # save the entry
        library_entry.save()
    except:
        print("Creating new entry", accession, now)

        # this likely means it is not in the database
        library_entry = LibraryEntry.create(libraryaccession=accession, libraryname=json_entry["spectruminfo"]["library_membership"], libraryjson=_library_entry, librarysource="GNPS", lastupdate=now)

        # save the entry
        library_entry.save()
    
    return



### GNPS Spectral Library Delivery Endpoints that will be constantly updated
def _get_gnps_spectrum(gnpsid):
    r = requests.get("https://gnps.ucsd.edu/ProteoSAFe/SpectrumCommentServlet?SpectrumID={}".format(gnpsid))
    r.raise_for_status()

    return r.text

#from expiringdict import ExpiringDict
#memory_cache = ExpiringDict(max_len=100, max_age_seconds=84600)

@celery_instance.task(time_limit=60)
def get_gnps_by_structure_task(smiles, inchi, inchikey):
    raise Exception("Deprecated")

    # I'm not sure we need this anymore

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
    'tasks_worker.get_gnps_by_structure_task': {'queue': 'worker'},
    'tasks_worker.task_updategnpslibrary': {'queue': 'worker'},
}