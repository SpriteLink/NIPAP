#!/bin/sh

# set the postgres password we'll be using in our testing
export PGPASSWORD=papin

# create the database
cd nipap/sql/
sudo -u postgres PGPASSWORD=papin make db
cd ../..

# install ip4r
mkdir ip4r
cd ip4r
wget http://pgfoundry.org/frs/download.php/3380/ip4r-2.0.tgz
tar zxf ip4r-2.0.tgz
cd ip4r-2.0
make
sudo make install > ip4r-make.log 2>&1
sudo -u postgres psql -d nipap -f sql/ip4r.sql > ip4r-sql-install.log 2>&1
cd ../..

# create the nipap tables
cd nipap/sql/
sudo -u postgres PGPASSWORD=papin make tables
