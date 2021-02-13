import requests
import sys
import json
import pandas as pd
import glob
import requests_cache
from tqdm import tqdm
import urllib.parse
requests_cache.install_cache('demo_cache')


def get_inchikey(smiles):
    url = "https://gnps-structure.ucsd.edu/inchikey?smiles={}".format(urllib.parse.quote(smiles))
    r = requests.get(url)
    return r.text


output_filename = sys.argv[1]

all_json = glob.glob("**/*.json", recursive=True)

output_list = []
for json_filename in tqdm(all_json):
    mibig_entry = json.loads(open(json_filename).read())
    #print(json.dumps(mibig_entry["cluster"], indent=4))

    mibig_accession = mibig_entry["cluster"].get("mibig_accession", "")
    organism_name = mibig_entry["cluster"].get("organism_name", "")
    ncbi_tax_id = mibig_entry["cluster"].get("ncbi_tax_id", "")

    for compound in mibig_entry["cluster"].get("compounds", []):
        if not "chem_struct" in compound:
            continue

        smiles = compound["chem_struct"]
        compound_name = compound["compound"]
        molecular_formula = compound["molecular_formula"]
        inchikey = get_inchikey(smiles)
        no_stereo_inchikey = inchikey.split("-")[0]

        output_dict = {}
        output_dict["mibig_accession"] = mibig_accession
        output_dict["organism_name"] = organism_name
        output_dict["ncbi_tax_id"] = ncbi_tax_id

        output_dict["smiles"] = smiles
        output_dict["inchikey"] = inchikey
        output_dict["no_stereo_inchikey"] = no_stereo_inchikey
        output_dict["compound_name"] = compound_name
        output_dict["molecular_formula"] = molecular_formula


        output_list.append(output_dict)

pd.DataFrame(output_list).to_csv(output_filename, sep="\t", index=False)