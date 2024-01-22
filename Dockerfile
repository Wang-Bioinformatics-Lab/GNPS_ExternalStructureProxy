FROM ubuntu:22.04
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update -y && apt-get install -y libxrender-dev build-essential libarchive-dev wget vim

# Install Mamba
ENV CONDA_DIR /opt/conda
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && /bin/bash ~/miniforge.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Install git, requirement for HMDB integration into matchms workflow
RUN apt install -y git

# Install Java
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Install Nextflow
RUN wget -q  https://get.nextflow.io -O /nextflow
RUN chmod +x /nextflow
RUN /nextflow

# Adding to bashrc
RUN echo "export PATH=$CONDA_DIR:$PATH" >> ~/.bashrc

# Add nextflow to path
RUN echo "export PATH=/nextflow:$PATH" >> ~/.bashrc
ENV PATH=/nextflow:$PATH

RUN mamba create -n rdkit -c rdkit rdkit=2019.09.3.0

COPY requirements.txt /

RUN /bin/bash -c ". activate rdkit && pip install -r requirements.txt"


COPY . /app
WORKDIR /app
