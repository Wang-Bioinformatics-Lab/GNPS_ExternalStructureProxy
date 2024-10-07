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
        library_dict["browselink"] = "https://gnps.ucsd.edu/ProteoSAFe/gnpslibrary.jsp?library={}".format(library_name)

    library_name = "ALL_GNPS"
    library_dict = {}
    library_dict["libraryname"] = library_name
    library_dict["type"] = "AGGREGATION"
    library_dict["mgflink"] = "/gnpslibrary/{}.mgf".format(library_name)
    library_dict["msplink"] = "/gnpslibrary/{}.msp".format(library_name)
    library_dict["jsonlink"] = "/gnpslibrary/{}.json".format(library_name)
    library_dict["browselink"] = "https://library.gnps2.org/"
    library_list.append(library_dict)

    library_name = "ALL_GNPS_NO_PROPOGATED"
    library_dict = {}
    library_dict["libraryname"] = "ALL_GNPS_NO_PROPOGATED"
    library_dict["type"] = "AGGREGATION"
    library_dict["mgflink"] = "/gnpslibrary/{}.mgf".format(library_name)
    library_dict["msplink"] = "/gnpslibrary/{}.msp".format(library_name)
    library_dict["jsonlink"] = "/gnpslibrary/{}.json".format(library_name)
    library_dict["browselink"] = "https://library.gnps2.org/"
    library_list.append(library_dict)

    # We should check how many entries in our database
    number_of_spectra = LibraryEntry.select().count()

    # report when the last time we actually updated the GNPS exports
    filename = "/output/ALL_GNPS.json"

    # check the last modified date
    last_modified = str(datetime.datetime.fromtimestamp(os.path.getmtime(filename)))
    
    #### Preprocessed Data ####
    preprocessed_list = []
    
    # GNPS Cleaning
    library_dict = {}
    library_dict["libraryname"] = "ALL_GNPS_NO_PROPOGATED"
    library_dict["processingpipeline"] = 'GNPS Cleaning'
    library_dict["csvlink"] = "/processed_gnps_data/gnps_cleaned.csv"
    library_dict["mgflink"] = "/processed_gnps_data/gnps_cleaned.mgf"
    library_dict["jsonlink"] = "/processed_gnps_data/gnps_cleaned.json"
    preprocessed_list.append(library_dict)

    # MatchMS Cleaning
    library_dict = {}
    library_dict["libraryname"] = "ALL_GNPS_NO_PROPOGATED"
    library_dict["processingpipeline"] = 'GNPS Cleaning + MatchMS'
    library_dict["csvlink"] = None
    library_dict["mgflink"] = "/processed_gnps_data/matchms.mgf"
    library_dict["jsonlink"] = None
    preprocessed_list.append(library_dict)
    
    ####    ####
    
    return render_template('gnpslibrarylist.html',
                           library_list=library_list,
                           number_of_spectra=number_of_spectra,
                           last_modified=last_modified,
                           preprocessed_list=preprocessed_list)


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

# Preprocessed Data List
# TODO: Create a endpoint for list of preprocessed data
@app.route('/processed_gnps_data/matchms.mgf', methods=['GET']) # TODO: No parameters for now 
def processed_gnps_data_mgf_download():
    return send_from_directory("/output/cleaned_data/matchms_output", "cleaned_spectra.mgf")

@app.route('/processed_gnps_data/gnps_cleaned.csv', methods=['GET']) # TODO: No parameters for now
def processed_gnps_data_gnps_cleaned_csv_download():
    return send_from_directory("/output/cleaned_data", "ALL_GNPS_cleaned.csv")

@app.route('/processed_gnps_data/gnps_cleaned.mgf', methods=['GET']) # TODO: No parameters for now
def processed_gnps_data_gnps_cleaned_mgf_download():
    return send_from_directory("/output/cleaned_data", "ALL_GNPS_cleaned.mgf")

@app.route('/processed_gnps_data/gnps_cleaned.json', methods=['GET']) # TODO: No parameters for now
def processed_gnps_data_gnps_cleaned_json_download():
    return send_from_directory("/output/cleaned_data/json_outputs", "ALL_GNPS_cleaned.json")

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

@app.route('/admin/run_pipelines', methods=['GET'])
def run_pipelines():
    """
    This API call is used to test the matchms cleaning pipeline in GNPS2
    """
    from tasks_gnps import run_cleaning_pipeline
    result = run_cleaning_pipeline.delay()
    print("Running  cleaning pipeline, result:", result, flush=True)
    return "Running  cleaning pipeline"

@app.route('/admin/download_cleaning_report', methods=['GET']) # TODO: No parameters for now
def download_cleaning_report():
    return send_from_directory(directory="/output/cleaned_data/", path="ml_pipeline_report.html")
