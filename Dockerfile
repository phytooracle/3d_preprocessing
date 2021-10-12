FROM ubuntu:18.04

WORKDIR /opt
COPY . /opt

USER root

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update -y
RUN apt-get install -y python3.6-dev \
                       python3-pip \
                       wget \
                       gdal-bin \
                       libgdal-dev \
                       libspatialindex-dev \
                       build-essential \
                       software-properties-common \
                       apt-utils \
                       libsm6 \
                       libxext6 \
                       libxrender-dev \
                       libgl1-mesa-dev

RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update --fix-missing
RUN apt-get install -y --fix-missing libgdal-dev
RUN pip3 install cython
RUN pip3 install --upgrade cython

RUN pip3 install pyproj==1.9.6
RUN pip3 install numpy==1.19.1
RUN pip3 install opencv-python==3.4.2.16
RUN pip3 install opencv-contrib-python==3.4.2.16
RUN pip3 install open3d==0.11.2

ENTRYPOINT [ "python3", "/opt/main.py" ]