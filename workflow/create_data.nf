#!/usr/bin/env nextflow

params.input = ''
TOOL_FOLDER = "$baseDir/bin"

process getMIBIG {
    publishDir "$baseDir", mode: 'copy', overwrite: true

    input:
    val accession from Channel.from(params.input)

    output:
    file "mibig.tsv" into table_ch
    
    """
    wget https://dl.secondarymetabolites.org/mibig/mibig_json_2.0.tar.gz
    tar -xzvf mibig_json_2.0.tar.gz
    python $TOOL_FOLDER/convert_mibig.py mibig.tsv
    """
}

process createDB {

     publishDir "$baseDir", mode: 'copy', overwrite: true

    input:
    file table from table_ch

    output:
    file "database.db"
    
    """
    csvs-to-sqlite mibig.tsv database.db --separator '\t'
    """

    
}
