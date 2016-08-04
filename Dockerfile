# This file describes the standard way to build NIPAP, using docker
#
# Usage:
#
# # Assemble the full dev environment. This is slow the first time.
# docker build -t nipap-devenv .
#
# # Mount your source in an interactive container for quick testing:
# docker run -v `pwd`:/nipap -i -t nipap-devenv bash
#
# # Build debian packages
# docker run nipap-devenv make builddeb
#

FROM debian:stable
MAINTAINER Kristian Larsson <kristian@spritelink.net>

ENV DEBIAN_FRONTEND=noninteractive

# apt update, upgrade & install packages
RUN apt-get update -qy && apt-get upgrade -qy 

RUN apt-get install -qy devscripts make python python-all python-docutils

WORKDIR /nipap
