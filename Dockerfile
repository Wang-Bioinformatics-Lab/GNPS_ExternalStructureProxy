FROM ubuntu:22.04
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update -y && apt-get install -y libxrender-dev build-essential libarchive-dev wget vim git unzip

# Install Mamba
ENV CONDA_DIR /opt/conda
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && /bin/bash ~/miniforge.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Set RabbitMQ consumer timeout
ENV RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS="-rabbit consumer_timeout 36000000"

# Install Java
RUN apt-get update && \
    apt-get install -y openjdk-21-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Adding to bashrc
RUN echo "export PATH=$CONDA_DIR:$PATH" >> ~/.bashrc

# Set Conda/Mamba to be non-interactive
ENV CONDA_ALWAYS_YES="true"
ENV MAMBA_ALWAYS_YES="true"

# Creating env
RUN mamba create -n rdkit -c rdkit rdkit=2019.09.3.0
RUN mamba create -n web python=3.9

# Installing Nextflow
RUN mamba install -n rdkit -c bioconda nextflow==24.04.4 -y

# Installing RDkit
COPY requirements.txt /
RUN /bin/bash -c ". activate rdkit && pip install -r requirements.txt"

# Installing web server
RUN /bin/bash -c ". activate web && pip install -r requirements.txt"

COPY . /app
WORKDIR /app
