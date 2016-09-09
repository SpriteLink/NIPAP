# This file describes a docker image for running nipap-www in docker
#
# Build the docker image:
#     docker build -t nipap-www -f Dockerfile.www .
#
# Run by linking to the container running nipapd. -i -t is for interactive,
# use -d if you wish to run the container in the background:
#     docker run -i -t --link nipapd --name nipap-www nipap-www
#
# Most configuration variables are provided via environment variables.
#   NIPAPD_USERNAME     username to authenticate to nipapd
#   NIPAPD_PASSWORD     password to authenticate to nipapd
#   NIPAPD_HOST         host where nipapd is running [nipapd]
#   NIPAPD_PORT         port of nipapd [1337]
#   WWW_USERNAME        web UI username [guest]
#   WWW_PASSWORD        web UI password [guest]
#
# Some variables have a default, indicated in square brackets, the rest you need
# to fill in. If you are linking to a container running nipapd, just enter the
# name of the container as NIPAPD_HOST.
#
# WWW_USERNAME & WWW_PASSWORD is used to create a new account in the local auth
# database so that you can later login to the web interface.
#

FROM ubuntu:xenial

MAINTAINER Lukas Garberg <lukas@spritelink.net>

ENV NIPAPD_HOST=nipapd NIPAPD_PORT=1337 WWW_USERNAME=guest WWW_PASSWORD=guest

# apt update, upgrade & install packages
RUN apt-get update -qy && apt-get upgrade -qy \
 && apt-get install -qy apache2 \
    libapache2-mod-wsgi \
    devscripts \
    make \
    libpq-dev \
    libsqlite3-dev \
    postgresql-client \
    python \
    python-all \
    python-docutils \
    python-pip \
    python-dev \
 && pip --no-input install envtpl \
 && rm -rf /var/lib/apt/lists/*

# Install pynipap, nipap and nipap-www
COPY pynipap /pynipap
COPY nipap /nipap
COPY nipap-www /nipap-www
RUN cd /pynipap && python setup.py install && \
    cd /nipap && pip --no-input install -r requirements.txt && python setup.py install && \
    cd /nipap-www && pip --no-input install -r requirements.txt && python setup.py install && \
    cd ..

EXPOSE 80
VOLUME [ "/var/log/apache2" ]

ENTRYPOINT [ "/nipap-www/entrypoint.sh" ]
