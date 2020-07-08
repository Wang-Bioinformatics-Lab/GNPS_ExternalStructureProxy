import requests
import pandas as pd

PRODUCTION_URL = "gnps-external.ucsd.edu"

def test_production():
    url = f"https://{PRODUCTION_URL}/heartbeat"
    r = requests.get(url)
    r.raise_for_status()


def test_datasets():
    url = f"https://{PRODUCTION_URL}/datasets/metabolights"
    r = requests.get(url)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/datasets/metabolomicsworkbench"
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

    url = f"https://{PRODUCTION_URL}/gnpslibraryformattedwithpeaksjson"
    r = requests.get(url)
    spectra_list = r.json()
    assert(len(spectra_list) > 10)
    r.raise_for_status()

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


def test_redirects():
    url = f"https://{PRODUCTION_URL}/structureproxy?smiles=CC(C)CC1NC(=O)C(C)NC(=O)C(=C)N(C)C(=O)CCC(NC(=O)C(C)C(NC(=O)C(CCCNC(N)=N)NC(=O)C(C)C(NC1=O)C(O)=O)\\C=C\\C(\\C)=C\\C(C)C(O)Cc1ccccc1)C(O)=O"
    r = requests.get(url)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/npatlasproxy?smiles=CC(C)CC1NC(=O)C(C)NC(=O)C(=C)N(C)C(=O)CCC(NC(=O)C(C)C(NC(=O)C(CCCNC(N)=N)NC(=O)C(C)C(NC1=O)C(O)=O)\\C=C\\C(\\C)=C\\C(C)C(O)Cc1ccccc1)C(O)=O"
    r = requests.get(url, verify=False)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/mibigproxy?smiles=C[C@H]1[C@@H](OC(C2=CSC([C@H](C(C)(OC(C3=CSC([C@H](C(C)(O)C)OC1=O)=N3)=O)C)OC(C)=O)=N2)=O)CCCC([37Cl])(Cl)C"
    r = requests.get(url)
    r.raise_for_status()

    url = f"https://{PRODUCTION_URL}/gnpsproxy?smiles=C[C@H]1[C@@H](OC(C2=CSC([C@H](C(C)(OC(C3=CSC([C@H](C(C)(O)C)OC1=O)=N3)=O)C)OC(C)=O)=N2)=O)CCCC([37Cl])(Cl)C"
    r = requests.get(url)
    r.raise_for_status()


def test_ftp_proxy():
    url = f"https://{PRODUCTION_URL}/massiveftpproxy?ftppath=ftp://massive.ucsd.edu/MSV000085699/peak/S6.mgf"
    r = requests.get(url)
    r.raise_for_status()