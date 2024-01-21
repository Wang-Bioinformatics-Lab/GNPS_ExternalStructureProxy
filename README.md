# GNPS - External Proxy

![production-integration](https://github.com/mwang87/GNPS_ExternalStructureProxy/workflows/production-integration/badge.svg)

External Structure Proxy for GNPS. The goal of this software to enable GNPS to link out to other resources as well as provide end points for GNPS to export data. 

## All GNPS Spectra

1. https://gnps-external.ucsd.edu/gnpslibraryjson - All Library Spectra in GNPS
1. https://gnps-external.ucsd.edu/gnpslibraryformattedwithpeaksjson - All Library Spectra in GNPS with Peaks
1. https://gnps-external.ucsd.edu/gnpslibraryfornpatlasjson - All Library Spectra in GNPS formatted for NPAtlas to consume
1. https://gnps-external.ucsd.edu/gnpslibraryfornpatlastsv - All Library Spectra in GNPS formatted for NPAtlas to consume

## GNPS Libraries as MGF Files

1. https://gnps-external.ucsd.edu/gnpslibrary/ALL_GNPS.mgf - MGF for ALL GNPS
1. https://gnps-external.ucsd.edu/gnpslibrary/GNPS-LIBRARY.mgf - MGF for GNPS-LIBRARY

## Linking out to external services from GNPS

1. Link to External Resources - [Example](https://gnps-external.ucsd.edu/structureproxy?smiles=CC(C)CC1NC(=O)C(C)NC(=O)C(=C)N(C)C(=O)CCC(NC(=O)C(C)C(NC(=O)C(CCCNC(N)=N)NC(=O)C(C)C(NC1=O)C(O)=O)\\C=C\\C(\\C)=C\\C(C)C(O)Cc1ccccc1)C(O)=O)
1. Link to NPAtlas - [Example](https://gnps-external.ucsd.edu/npatlasproxy?smiles=CC(C)CC1NC(=O)C(C)NC(=O)C(=C)N(C)C(=O)CCC(NC(=O)C(C)C(NC(=O)C(CCCNC(N)=N)NC(=O)C(C)C(NC1=O)C(O)=O)\\C=C\\C(\\C)=C\\C(C)C(O)Cc1ccccc1)C(O)=O)
1. Link to MIBIG - [Example](https://gnps-external.ucsd.edu/mibigproxy?smiles=C[C@H]1[C@@H](OC(C2=CSC([C@H](C(C)(OC(C3=CSC([C@H](C(C)(O)C)OC1=O)=N3)=O)C)OC(C)=O)=N2)=O)CCCC([37Cl])(Cl)C)

## Dataset in GNPS

1. List of Metabolights Imported Datasets - https://gnps-external.ucsd.edu/datasets/metabolights
1. List of Metabolomics Workbench Imported Datasets - https://gnps-external.ucsd.edu/datasets/metabolomicsworkbench

## GNPS-MassIVE Dataset FTP to HTTPS proxy

This is accessible at 

```
/massiveftpproxy?ftppath=<massive path to file>
```

[Test Link](https://gnps-external.ucsd.edu/massiveftpproxy?ftppath=ftp://massive.ucsd.edu/MSV000085699/peak/S6.mgf)

## Local Deployment/Testing
1. Run the server with `make-server-compose-interactive`
2. Check the active ports (typically 5010, but can be seen in `docker ps`) and ensure they're forwarded if needed
3. Web serivce is now live at [http://localhost:5010](http://localhost:5010)
4. If starting for the first time, collect the GNPS libraries by visiting [http://localhost:5010](http://localhost:5010/admin/updatelibraries)
