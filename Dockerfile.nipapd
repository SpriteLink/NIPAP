# This file describes a docker image for running nipapd in docker
#
# Build the docker image:
#     docker build -t nipapd -f Dockerfile.nipapd .
#
# Run by linking to the container running postgres. -i -t is for interactive,
# use -d if you wish to run the container in the background:
#     docker run -i -t --link nipap-db --name nipapd nipapd
#
# Most configuration variables are provided via environment variables.
#   LISTEN_ADDRESS      address on which nipapd should listen [0.0.0.0]
#   LISTEN_PORT         port on which nipapd should listen [1337]
#   SYSLOG              true / false enable syslog? [false]
#   DB_HOST             host where database is running
#   DB_PORT             port of database [5432]
#   DB_NAME             name of database
#   DB_USERNAME         username to authenticate to database
#   DB_PASSWORD         password to authenticate to database
#   DB_SSLMODE          require ssl? [disable]
#   NIPAP_USERNAME      name of account to create
#   NIPAP_PASSWORD      password of account to create
#
# Some values have a default, indicated in square brackets, the rest you need
# to fill in. If you are linking to a container running postgres, just enter
# the name of the container as DB_HOST and use the credentials with which you
# started that container.
#
# NIPAP_USERNAME & NIPAP_PASSWORD is used to create a new account in the local
# auth database of nipapd so that you can later authenticate towards nipapd. It
# is only possible to add a single account. If you wish to add more accounts
# you should administrate the database outside and share it with the container
# via a volume.
#

FROM ubuntu:xenial
MAINTAINER Kristian Larsson <kristian@spritelink.net>

ENV DEBIAN_FRONTEND=noninteractive

# apt update, upgrade & install packages
RUN apt-get update -qy && apt-get upgrade -qy \
 && apt-get install -qy devscripts \
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


COPY nipap /nipap
WORKDIR /nipap
RUN pip --no-input install -r requirements.txt \
 && python setup.py install

EXPOSE 1337
ENV LISTEN_ADDRESS=0.0.0.0 LISTEN_PORT=1337 SYSLOG=false DB_PORT=5432 DB_SSLMODE=disable

ENTRYPOINT ["/nipap/entrypoint.sh"]
