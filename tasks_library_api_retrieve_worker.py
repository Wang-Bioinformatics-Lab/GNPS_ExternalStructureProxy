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
    print("On Start, doing nothing now", file=sys.stderr, flush=True)

@celery_instance.task(time_limit=60)
def task_computeheartbeat():
    print("UP", file=sys.stderr, flush=True)

    # This is to warm everything up
    LibraryEntry.get(LibraryEntry.libraryaccession == "CCMSLIB00000001547")

    return "Up"

# Here we need to update the library entry for GNPS the library entry, rate limit to 10 a minute
@celery_instance.task(time_limit=60, rate_limit='10/m')
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
        # This means we couldnt find it, so we create a new one
        print("Creating new entry {} {}".format(accession, now))

        # this likely means it is not in the database
        library_entry = LibraryEntry.create(libraryaccession=accession, libraryname=json_entry["spectruminfo"]["library_membership"], libraryjson=_library_entry, librarysource="GNPS", lastupdate=now)

        # save the entry
        library_entry.save()
        
    return


### GNPS Spectral Library Delivery Endpoints that will be constantly updated
def _get_gnps_spectrum(gnpsid):
    print("GRABBING GNPS Entry via URL {}".format(gnpsid), file=sys.stderr, flush=True)

    r = requests.get("https://gnps.ucsd.edu/ProteoSAFe/SpectrumCommentServlet?SpectrumID={}".format(gnpsid.rstrip().lstrip()))
    r.raise_for_status()

    return r.text


celery_instance.conf.task_routes = {
    'tasks_library_api_retrieve_worker.task_updategnpslibrary': {'queue': 'worker'},
    'tasks_library_api_retrieve_worker.task_computeheartbeat': {'queue': 'worker'},
}