# views.py
from flask import abort, jsonify, render_template, request, redirect, url_for, send_file, send_from_directory

from app import app

import json
import csv
import os
import requests
import requests_cache
import utils
import pandas as pd
import datetime

from models import *
from tasks_worker import task_updategnpslibrary, task_computeheartbeat

@app.route('/', methods=['GET'])
def homepage():
    # redirect to gnpslibrary
    return redirect(url_for('gnpslibrary'))

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{'status' : 'up'}"


@app.route('/gnpsspectrum', methods=['GET'])
def gnpsspectrum():
    gnpsid = request.values.get("SpectrumID")

    # we try to read from the database
    try:
        library_entry = LibraryEntry.get(LibraryEntry.libraryaccession == gnpsid)

        # checking the current time
        now = datetime.datetime.now()

        # load the time from the entry
        lastupdate = library_entry.lastupdate
        # parse into datetime
        lastupdate = datetime.datetime.strptime(lastupdate, "%Y-%m-%d %H:%M:%S")

        # if the last update was more than 5 day ago, we should update it
        #if (now - lastupdate).days > 5:
        if (now - lastupdate).days > 0:
            task_updategnpslibrary.delay(gnpsid)
    except:
        # this likely means it is not in the database, we should try to grab it for next time
        task_updategnpslibrary.delay(gnpsid)

        abort(404)

    return library_entry.libraryjson


#Making it easy to query for all of GNPS library spectra
@app.route('/gnpslibraryjson', methods=['GET'])
def gnpslibraryjson():
    return send_from_directory("/output", "gnpslibraries.json")

#This returns all the spectra
@app.route('/gnpslibraryformattedjson', methods=['GET'])
def gnpslibraryformattedjson():
    return send_from_directory("/output", "gnpslibraries_enriched_all.json")

#This returns all the spectra with peaks
@app.route('/gnpslibraryformattedwithpeaksjson', methods=['GET'])
def gnpslibraryformattedwithpeaksjson():
    return send_from_directory("/output", "ALL_GNPS.json")

# Download Page for Spectral Libraries
@app.route('/gnpslibrary', methods=['GET'])
def gnpslibrary():
    # This is a test
    task = task_computeheartbeat.delay()

    library_list = pd.read_csv("library_names.tsv").to_dict(orient="records")

    for library_dict in library_list:
        library_name = library_dict["library"]

        library_dict["libraryname"] = library_name
        library_dict["mgflink"] = "/gnpslibrary/{}.mgf".format(library_name)
        library_dict["msplink"] = "/gnpslibrary/{}.msp".format(library_name)
        library_dict["jsonlink"] = "/gnpslibrary/{}.json".format(library_name)

    library_name = "ALL_GNPS"
    library_dict = {}
    library_dict["libraryname"] = library_name
    library_dict["type"] = "AGGREGATION"
    library_dict["mgflink"] = "/gnpslibrary/{}.mgf".format(library_name)
    library_dict["msplink"] = "/gnpslibrary/{}.msp".format(library_name)
    library_dict["jsonlink"] = "/gnpslibrary/{}.json".format(library_name)
    library_list.append(library_dict)

    library_name = "ALL_GNPS_NO_PROPOGATED"
    library_dict = {}
    library_dict["libraryname"] = "ALL_GNPS_NO_PROPOGATED"
    library_dict["type"] = "AGGREGATION"
    library_dict["mgflink"] = "/gnpslibrary/{}.mgf".format(library_name)
    library_dict["msplink"] = "/gnpslibrary/{}.msp".format(library_name)
    library_dict["jsonlink"] = "/gnpslibrary/{}.json".format(library_name)
    library_list.append(library_dict)

    # We should check how many entries in our database
    number_of_spectra = LibraryEntry.select().count()

    # report when the last time we actually updated the GNPS exports
    filename = "/output/ALL_GNPS.json"

    # check the last modified date
    last_modified = str(datetime.datetime.fromtimestamp(os.path.getmtime(filename)))

    return render_template('gnpslibrarylist.html', library_list=library_list, number_of_spectra=number_of_spectra, last_modified=last_modified)


# Library List
@app.route('/gnpslibrary.json', methods=['GET'])
def gnpslibrarieslistjson():
    library_list = pd.read_csv("library_names.tsv").to_dict(orient="records")
    return json.dumps(library_list)

@app.route('/gnpslibrary/<library>.mgf', methods=['GET'])
def mgf_download(library):
    return send_from_directory("/output", "{}.mgf".format(library))

@app.route('/gnpslibrary/<library>.msp', methods=['GET'])
def msp_download(library):
    return send_from_directory("/output", "{}.msp".format(library))

@app.route('/gnpslibrary/<library>.json', methods=['GET'])
def json_download(library):
    return send_from_directory("/output", "{}.json".format(library))

# Admin
from tasks_gnps import generate_gnps_data
@app.route('/admin/updatelibraries', methods=['GET'])
def updatelibraries():
    generate_gnps_data.delay()
    return "Running"
    
@app.route('/admin/count', methods=['GET'])
def admincount():
    # This is a test
    task = task_computeheartbeat.delay()
    
    return str(LibraryEntry.select().count())

@app.route('/admin/matchms_cleaning', methods=['GET'])
def matchms_cleaning():
    """
    This API call is used to test the matchms cleaning pipeline in GNPS2
    """
    from utils import run_matchms_pipeline
    import glob
    
    output_str = ""
    
    def _stat_files(output_str):
        files =  glob.glob("/output/matchms_output/*")
        if not files:
            print("No files found in /output/matchms_output/", flush=True)
            output_str += "No files found in /output/matchms_output/ \n"
        for path in files:
            print(path, os.stat(path))
            output_str += "{} {}\n".format(path, os.stat(path))
        return output_str
    
    print("Running stat on current files...", flush=True)
    output_str += "Running stat on current files...\n"
    output_str = _stat_files(output_str)
    result = run_matchms_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/matchms_output/")
    # Print the stat of the current output files
    print("Running stat on new files...", flush=True)
    output_str += "Running stat on new files...\n"
    output_str = _stat_files(output_str)
    
    print(result, flush=True)
    
    return output_str
