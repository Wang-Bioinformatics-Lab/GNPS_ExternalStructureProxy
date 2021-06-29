from celery import Celery
import os
import json
import requests
import utils
import pandas as pd

celery_instance = Celery('tasks', backend='rpc://externalstructureproxy-rabbitmq', broker='pyamqp://externalstructureproxy-rabbitmq')

@celery_instance.task()
def generate_gnps_data():
    # Loading all GNPS Library Spectra, without peaks
    gnps_libraries = utils.load_GNPS()

    print("Got all Libraries")

    with open("/output/gnpslibraries.json", "w") as output_file:
        output_file.write(json.dumps(gnps_libraries))

    encriched_gnps_libraries = utils.gnps_format_libraries(gnps_libraries)

    print("Enriched Libraries")

    with open("/output/gnpslibraries_enriched_all.json", "w") as output_file:
        output_file.write(json.dumps(utils.gnps_filter_for_key(encriched_gnps_libraries, filterKeysOut=False)))

    #Outputting for NPAtlas
    with open("/output/gnpslibraries_npatlas.json", "w") as output_file:
        output_file.write(json.dumps(utils.gnps_filter_for_key(encriched_gnps_libraries, filterKeysOut=True)))

    pd.DataFrame(utils.gnps_filter_for_key(encriched_gnps_libraries)).to_csv("/output/gnpslibraries_npatlas.tsv", sep="\t", index=False)

    print("NPAtlas Export")

    # Getting spectrum peaks for each library spectrum
    print("Individual Library Export")
    encriched_gnps_libraries_with_peaks = utils.output_all_gnps_individual_libraries(encriched_gnps_libraries, "/output/")

    with open("/output/ALL_GNPS.json", "w") as output_file:
        output_file.write(json.dumps(encriched_gnps_libraries_with_peaks))

    print("MGF Library Export")
    # Generating the MGF versions of it
    mgf_string = utils.get_full_mgf_string(encriched_gnps_libraries_with_peaks)
    with open("/output/ALL_GNPS.mgf", "wb") as output_file:
        output_file.write(mgf_string.encode("ascii", "ignore"))

    print("MSP Library Export")
    # TODO: Generating the MSP versions of it
    msp_string = utils.get_full_msp_string(encriched_gnps_libraries_with_peaks)
    with open("/output/ALL_GNPS.msp", "wb") as output_file:
        output_file.write(msp_string.encode("ascii", "ignore"))


celery_instance.conf.beat_schedule = {
    "generate_gnps_data": {
        "task": "gnps_tasks.generate_gnps_data",
        "schedule": 86400
    }
}

celery_instance.conf.task_routes = {
    'gnps_tasks.generate_gnps_data': {'queue': 'beat_worker'},
}