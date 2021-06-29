FROM continuumio/miniconda3:4.7.12
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update -y && apt-get install -y libxrender-dev build-essential
RUN conda create -n rdkit -c rdkit rdkit=2019.09.3.0

COPY requirements.txt /

RUN /bin/bash -c ". activate rdkit && pip install -r requirements.txt"


COPY . /app
WORKDIR /app
