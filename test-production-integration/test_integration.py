import requests
import pandas as pd

PRODUCTION_URL = "external.gnps2.org"

def test_production():
    url = f"https://{PRODUCTION_URL}/heartbeat"
    r = requests.get(url)
    r.raise_for_status()



def test_gnps_library():
    url = f"https://{PRODUCTION_URL}/gnpslibraryjson"
    r = requests.get(url)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/gnpslibraryformattedjson"
    r = requests.get(url)
    spectra_list = r.json()
    assert(len(spectra_list) > 10)
    r.raise_for_status()

    # Likely Too Big
#     url = f"https://{PRODUCTION_URL}/gnpslibraryformattedwithpeaksjson"
#     r = requests.get(url)
#     spectra_list = r.json()
#     assert(len(spectra_list) > 10)
#     r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/gnpslibraryfornpatlasjson"
    r = requests.get(url)
    spectra_list = r.json()
    assert(len(spectra_list) > 10)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/gnpslibraryfornpatlastsv"
    r = requests.get(url)
    r.raise_for_status()
    
    url = f"https://{PRODUCTION_URL}/gnpslibrary/GNPS-LIBRARY.mgf"
    r = requests.get(url)
    r.raise_for_status()


def test_all_small_gnps_library():
    LIBRARY_NAMES = list(pd.read_csv("../library_names.tsv")["library"])

    for library_name in LIBRARY_NAMES:
        url = f"https://{PRODUCTION_URL}/gnpslibrary/{library_name}.mgf"
        r = requests.get(url)
        r.raise_for_status()

        url = f"https://{PRODUCTION_URL}/gnpslibrary/{library_name}.msp"
        r = requests.get(url)
        r.raise_for_status()

        url = f"https://{PRODUCTION_URL}/gnpslibrary/{library_name}.json"
        r = requests.get(url)
        r.raise_for_status()



