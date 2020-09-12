#!/bin/bash

if ls /usr/share/ca-certificates/extra/*.crt 1> /dev/null 2>&1; then
    echo "installing certs"
    ls /usr/share/ca-certificates/extra/*.crt | sed 's/\/usr\/share\/ca-certificates\///g' >> /etc/ca-certificates.conf
    update-ca-certificates
    python3 -m pip install --upgrade pip
    pip3 config set global.cert /etc/ssl/certs/ca-certificates.crt
else
    echo "No certs found - skipping"
    python3 -m pip install --upgrade pip
fi
