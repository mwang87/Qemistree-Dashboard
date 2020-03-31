FROM continuumio/miniconda3:latest
MAINTAINER Mingxun Wang "mwang87@gmail.com"

WORKDIR /app
RUN apt-get update -y
RUN wget https://data.qiime2.org/distro/core/qiime2-2019.10-py36-linux-conda.yml
RUN conda env create -n qiime2-2019.10-qemistree --file qiime2-2019.10-py36-linux-conda.yml
RUN conda install -n qiime2-2019.10-qemistree -c conda-forge dash
RUN /bin/bash -c ". activate qiime2-2019.10-qemistree && \
    pip install git+https://github.com/biocore/q2-qemistree"
RUN conda install -n qiime2-2019.10-qemistree -c anaconda beautifulsoup4

#RUN /bin/bash -c ". activate qiime2-2019.10-qemistree && \
#    pip install https://github.com/biocore/q2-qemistree/archive/2020.1.2.tar.gz"
#RUN /bin/bash -c ". activate qiime2-2019.10-qemistree && \
#    pip install dash-bootstrap-components"



COPY . /app
WORKDIR /app

