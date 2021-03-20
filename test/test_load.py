import json
import requests
from tqdm import tqdm

def test():
    library_spectra = requests.get("https://gnps-external.ucsd.edu/gnpslibrary/GNPS-LIBRARY.json").json()
    for spectrum in tqdm(library_spectra):
        gnpsid = spectrum["spectrum_id"]
        #print(gnpsid)
        #url = "http://mingwangbeta.ucsd.edu:5010/gnpsspectrum?SpectrumID={}".format(gnpsid)
        url = "https://gnps-external.ucsd.edu/gnpsspectrum?SpectrumID={}".format(gnpsid)
        #print(url)
        requests.get(url)