from celery import Celery
import json
import utils
from pathlib import Path
from celery import chain, signature


celery_instance = Celery('tasks', backend='redis://externalstructureproxy-redis', broker='pyamqp://guest@externalstructureproxy-rabbitmq/', )

@celery_instance.task()
def generate_gnps_data():
    # Loading all GNPS Library Spectra, without peaks
    gnps_libraries, library_list_df = utils.load_GNPS()

    print("Got all Libraries")

    with open("/output/gnpslibraries.json", "w") as output_file:
        output_file.write(json.dumps(gnps_libraries))

    encriched_gnps_libraries = utils.gnps_format_libraries(gnps_libraries)

    print("Enriched Libraries")

    with open("/output/gnpslibraries_enriched_all.json", "w") as output_file:
        output_file.write(json.dumps(utils.gnps_filter_for_key(encriched_gnps_libraries, filterKeysOut=False)))

    #Outputting for NPAtlas
    #with open("/output/gnpslibraries_npatlas.json", "w") as output_file:
    #    output_file.write(json.dumps(utils.gnps_filter_for_key(encriched_gnps_libraries, filterKeysOut=True)))

    #pd.DataFrame(utils.gnps_filter_for_key(encriched_gnps_libraries)).to_csv("/output/gnpslibraries_npatlas.tsv", sep="\t", index=False)

    print("NPAtlas Export Finished")

    # Getting spectrum peaks for each library spectrum
    print("Individual Library Export")
    encriched_gnps_libraries_with_peaks = utils.output_all_gnps_individual_libraries(encriched_gnps_libraries, "/output/")

    # Lets make separate spectra aggregations
    non_propogated_library_list = set(library_list_df[library_list_df["type"].isin(["GNPS", "IMPORT"])]["library"])
    non_propogated_encriched_gnps_libraries_with_peaks = [spectrum_dict for spectrum_dict in encriched_gnps_libraries_with_peaks if spectrum_dict["library_membership"] in non_propogated_library_list]
    
    utils._output_library_files(non_propogated_encriched_gnps_libraries_with_peaks, "/output/", "ALL_GNPS_NO_PROPOGATED")

    utils._output_library_files(encriched_gnps_libraries_with_peaks, "/output/", "ALL_GNPS")

    # MULTIPLEX-SYNTHESIS-LIBRARY-ALL
    multiplex_all_re = r"MULTIPLEX-SYNTHESIS-LIBRARY-ALL-PARTITION-\d+"
    multiplex_all_library_list = set(library_list_df[library_list_df["library"].str.contains(multiplex_all_re, regex=True)]["library"])
    multiplex_all_encriched_gnps_libraries_with_peaks = [spectrum_dict for spectrum_dict in encriched_gnps_libraries_with_peaks if spectrum_dict["library_membership"] in multiplex_all_library_list]
    
    utils._output_library_files(multiplex_all_encriched_gnps_libraries_with_peaks, "/output/", "MULTIPLEX_ALL")

    # MULTIPLEX-SYNTHESIS-LIBRARY-FILTERED
    multiplex_filtered_re = r"MULTIPLEX-SYNTHESIS-LIBRARY-FILTERED-PARTITION-\d+"
    multiplex_filtered_library_list = set(library_list_df[library_list_df["library"].str.contains(multiplex_filtered_re, regex=True)]["library"])
    multiplex_filtered_encriched_gnps_libraries_with_peaks = [spectrum_dict for spectrum_dict in encriched_gnps_libraries_with_peaks if spectrum_dict["library_membership"] in multiplex_filtered_library_list]

    utils._output_library_files(multiplex_filtered_encriched_gnps_libraries_with_peaks, "/output/", "MULTIPLEX_FILTERED")
    # with open("/output/ALL_GNPS.json", "w") as output_file:
    #     output_file.write(json.dumps(encriched_gnps_libraries_with_peaks))

    # print("MGF Library Export")
    # # Generating the MGF versions of it
    # mgf_string = utils.get_full_mgf_string(encriched_gnps_libraries_with_peaks)
    # with open("/output/ALL_GNPS.mgf", "wb") as output_file:
    #     output_file.write(mgf_string.encode("ascii", "ignore"))

    # print("MSP Library Export")
    # # TODO: Generating the MSP versions of it
    # msp_string = utils.get_full_msp_string(encriched_gnps_libraries_with_peaks)
    # with open("/output/ALL_GNPS.msp", "wb") as output_file:
    #     output_file.write(msp_string.encode("ascii", "ignore"))
    
    #### MatchMS/ML Prep Pipeline ####
    run_cleaning_pipeline.delay()
    run_cleaning_pipeline_library_specific.delay("MULTIPLEX_ALL")
    run_cleaning_pipeline_library_specific.delay("MULTIPLEX_FILTERED")

@celery_instance.task(time_limit=64_800) # 18 Hour Timeout
def run_cleaning_pipeline():
    utils.run_cleaning_pipeline("/output/ALL_GNPS_NO_PROPOGATED.json", "/output/cleaned_data/")
    
    return "Finished matchms cleaning pipeline"

@celery_instance.task(time_limit=64_800) # 18 Hour Timeout
def run_cleaning_pipeline_library_specific(library):

    output_dir = Path(f"/output/cleaned_libraries/{library}/")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    utils.run_cleaning_pipeline(f"/output/{library}.json", output_dir, no_massbank=True)
    
    return f"Finished matchms cleaning pipeline for {library}"

celery_instance.conf.beat_schedule = {
    "generate_gnps_data": {
        "task": "tasks_gnps.generate_gnps_data",
        "schedule": 86400   # Every 24 hours
    }
}

celery_instance.conf.task_routes = {
    'tasks_gnps.generate_gnps_data': {'queue': 'beat_worker'},
    'tasks_gnps.run_cleaning_pipeline': {'queue': 'beat_worker'},
    'tasks_gnps.run_cleaning_pipeline_library_specific': {'queue': 'beat_worker'},
}