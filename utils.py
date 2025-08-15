import requests
import json
import os
import sys
import time
import subprocess 
from pathlib import Path

import pandas as pd
try:
    from rdkit import Chem
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
except:
    pass

library_df = pd.read_csv("library_names.tsv")
LIBRARY_NAMES = list(library_df["library"])

def get_inchikey(smiles, inchi):
    inchikey_from_smiles = ""
    inchikey_from_inchi = ""
    try:
        if len(smiles) > 5:
            inchikey_from_smiles = str(Chem.MolToInchiKey(Chem.MolFromSmiles(smiles)))
        else:
            inchikey_from_smiles = ""
    except:
        inchikey_from_smiles = ""

    try:
        if len(inchi) > 5:
            inchikey_from_inchi = str(Chem.InchiToInchiKey(inchi))
        else:
            inchikey_from_inchi = ""
    except:
        inchikey_from_inchi = ""

    if len(inchikey_from_smiles) > 2 and len(inchikey_from_inchi) > 2:
        return inchikey_from_smiles, inchikey_from_inchi

    if len(inchikey_from_smiles) > 2:
        return inchikey_from_smiles, ""

    if len(inchikey_from_inchi) > 2:
        return inchikey_from_inchi, ""

    return "", ""

def get_formula(smiles, inchi):
    formula_from_smiles = ""
    formula_from_inchi = ""
    try:
        if len(smiles) > 5:
            formula_from_smiles = str(CalcMolFormula(Chem.MolFromSmiles(smiles)))
        else:
            formula_from_smiles = ""
    except:
        formula_from_smiles = ""

    try:
        if len(inchi) > 5:
            formula_from_inchi = str(CalcMolFormula(Chem.MolFromInchi(inchi)))
        else:
            formula_from_inchi = ""
    except:
        formula_from_inchi = ""

    if len(formula_from_smiles) > 2 and len(formula_from_inchi) > 2:
        return formula_from_smiles, formula_from_inchi

    if len(formula_from_smiles) > 2:
        return formula_from_smiles, ""

    if len(formula_from_inchi) > 2:
        return formula_from_inchi, ""

    return "", ""



def run_cleaning_pipeline(gnps_json_file, output_directory, no_massbank:bool=False):
    path_to_script  = "/app/pipelines/gnps_ml_processing_workflow/GNPS_ML_Processing/nf_workflow.nf"
    api_cache_path  = "/output/structure_classification/"
    conda_path = "/app/conda_envs/"
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory, exist_ok=True)

    if not os.path.isdir(conda_path):
        os.makedirs(conda_path, exist_ok=True)

    stdout_log = "/output/gnps_ml_processing_nextflow.log"
    
    #Making a specific location in the pipelines folder so its outside of docker
    conda_env_path = Path("/app/pipelines/conda_envs/gnps2_ml_processing_env")
    matchms_conda_path = Path("/app/pipelines/conda_envs/matchms_env")
    work_dir = Path("/data/gscratch/web-services/Cleaning_Pipelines/work")
    if not work_dir.exists():
        work_dir.mkdir(parents=True, exist_ok=True)

    if not conda_env_path.parent.exists():
        conda_env_path.parent.mkdir(parents=True, exist_ok=True)
    if not matchms_conda_path.parent.exists():
        matchms_conda_path.parent.mkdir(parents=True, exist_ok=True)

    # Run a Nextflow script to generate all everything we need in the current process
    cmd = " ".join([
                        "nextflow", "run", str(path_to_script),
                        "--GNPS_json_path", str(gnps_json_file),
                        "--output_dir", str(output_directory),
                        "--conda_path", str(conda_env_path),
                        "--matchms_conda_path", str(matchms_conda_path),
                        "--api_cache", str(api_cache_path),
                        "-with-report", str(os.path.join(output_directory, "ml_pipeline_report.html")),
                        "-with-timeline", str(os.path.join(output_directory, "ml_pipeline_timeline.html")),
                        "-w", str(work_dir),
                    ] + (["--include_massbank", "false"] if no_massbank else []),)

    cmd = "export MAMBA_ALWAYS_YES='true' && {} >> {}".format(cmd, stdout_log)
    os.system(cmd)

    return 
