#.PHONY: install

PSQL=psql

DB_NAME=nipap
DB_USER=nipap
# TODO: enable this! it's a random password generated at install time, but
# nipapd needs to support a configuration file that we can put it in before we
# enable it!
DB_PASS=$(shell </dev/urandom tr -dc [:alpha:] | head -c16)
# use this supersecure static password until further
DB_PASS=papin

#
# TODO: need install thingy for ip4r
# psql -f /usr/lib/postgresql/8.4/lib/ip4r.so nipap
#
# 	- how do we determine if the system has ip4r modules at all?
# 		* can we ask psql?
# 			- Yes we can, just run a iprange() function and see what happens
# 		* if it's a debian / ubuntu system we can use apt-cache
# 	- how do we determine where the .sql file is?
# 		* we can guess on a few well known paths
# 		* we know where it's at on debian like systems
#


# test database version
PG_VER = $(shell pg_config --version | awk '{print $$2}')
PG_VER_MAJOR = $(shell echo $(PG_VER) | awk -F. '{ print ($$1 + 0) }')
PG_VER_MINOR = $(shell echo $(PG_VER) | awk -F. '{ print ($$2 + 0) }')
PG_VER_PATCH = $(shell echo $(PG_VER) | awk -F. '{ print ($$3 + 0) }')
PG_VER_OK = $(shell if [ $(PG_VER_MAJOR)$(PG_VER_MINOR) -ge 84 ]; then echo 1; else echo 0; fi)
ifeq (0,$(PG_VER_OK))
	$(error "You are running PostgreSQL $(PG_VER) and you need at least 8.4")
endif


all:
	@echo "Run this as the postgres user!"



db:
	createuser -S -D -R $(DB_USER)
	createdb -O $(DB_USER) $(DB_NAME)
	psql -q -c "ALTER USER $(DB_USER) ENCRYPTED PASSWORD '$(DB_PASS)'"

install:
	-createlang -d $(DB_NAME) plpgsql
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) -f find_free_prefix.plsql
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) -f get_prefix.plsql
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) -f calc_indent.plsql
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) -f ip_net.plsql

clean:
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) -f clean.plsql
