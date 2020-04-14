import sys
import os
import json
import requests
import requests_cache
requests_cache.install_cache('demo_cache')
sys.path.insert(0, "..")

def test_filtered_spectra():
    import utils
    spectra_list = utils.load_GNPS(library_names=["GNPS-LIBRARY"])
    spectra_list = utils.gnps_format_libraries(spectra_list)

    with open("output_enriched_list.json", "w") as output_file:
        output_file.write(json.dumps(spectra_list, indent=4))

    filtered_list = utils.gnps_filter_for_key(spectra_list)

    with open("output_filtered_list.json", "w") as output_file:
        output_file.write(json.dumps(filtered_list, indent=4))
    
    print(len(filtered_list))

def test_get_library_peaks():
    import utils
    spectra_list = utils.load_GNPS(library_names=["GNPS-LIBRARY"])[:100]
    spectra_list = utils.gnps_format_libraries(spectra_list)
    spectra_list_with_peaks = utils.output_all_gnps_individual_libraries(spectra_list, ".")

    print(len(spectra_list_with_peaks))

    with open("ALL_GNPS.json", "w") as output_file:
        output_file.write(json.dumps(spectra_list_with_peaks, indent=4))

    mgf_string = utils.get_full_mgf_string(spectra_list_with_peaks)
    with open("ALL_GNPS.mgf", "wb") as output_file:
        output_file.write(mgf_string.encode("ascii", "ignore"))

    msp_string = utils.get_full_msp_string(spectra_list_with_peaks)
    with open("ALL_GNPS.msp", "wb") as output_file:
        output_file.write(msp_string.encode("ascii", "ignore"))

def test_get_library_peaks_full():
    import utils
    output_folder = "."
    spectra_list = utils.load_GNPS()
    spectra_list = utils.gnps_format_libraries(spectra_list)

    spectra_list_with_peaks = utils.output_all_gnps_individual_libraries(spectra_list, ".")

    with open("ALL_GNPS.json", "w") as output_file:
        output_file.write(json.dumps(spectra_list_with_peaks, indent=4))

    mgf_string = utils.get_full_mgf_string(spectra_list_with_peaks)
    with open("ALL_GNPS.mgf", "wb") as output_file:
        output_file.write(mgf_string.encode("ascii", "ignore"))

    msp_string = utils.get_full_msp_string(spectra_list_with_peaks)
    with open("ALL_GNPS.msp", "wb") as output_file:
        output_file.write(msp_string.encode("ascii", "ignore"))


