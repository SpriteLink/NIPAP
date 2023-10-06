Custom CA Certs for docker containers
=====================================
If you need to include specific CA certs which you must trust, place them here
in PEM format, named \*.crt.

This may be required if you need to build the container from inside a network
which uses a proxy or similar, or other dependencies towards internal services
are included in your containers.