#.PHONY: install auth db tables clean clean-db clean-tables
# vim: ts=8 :

PSQL=psql

DB_NAME=nipap
DB_USER=nipap
# PGPASSWORD is the standard environment variable used by the PostgreSQL cli
# application to pass a password as it does not accept passwords via any
# arguments.  If PGPASSWORD is set then we use that for the password of our new
# user. Otherwise we default to generating a new random password.c
ifndef PGPASSWORD
PG_PASS_RAND=1
DB_PASS:=$(shell </dev/urandom tr -dc [:alpha:] | head -c16)
else
DB_PASS:=$(PGPASSWORD)
endif

# test database version
PG_VER := $(shell pg_config --version | awk '{print $$2}')
PG_VER_MAJOR := $(shell echo $(PG_VER) | awk -F. '{ print ($$1 + 0) }')
PG_VER_MINOR := $(shell echo $(PG_VER) | awk -F. '{ print ($$2 + 0) }')
PG_VER_PATCH := $(shell echo $(PG_VER) | awk -F. '{ print ($$3 + 0) }')
PG_VER_OK := $(shell if [ $(PG_VER_MAJOR)$(PG_VER_MINOR) -ge 84 ]; then echo 1; else echo 0; fi)
ifeq (0,$(PG_VER_OK))
	$(error "You are running PostgreSQL $(PG_VER) and you need at least 8.4")
endif


all:
	@echo "Please run \"make install\" as postgres user."

auth:
	createuser -S -D -R $(DB_USER)
	createdb -O $(DB_USER) $(DB_NAME)
	-psql -q -c "ALTER USER $(DB_USER) ENCRYPTED PASSWORD '$(DB_PASS)'"

db:
	-psql -d $(DB_NAME) -c "CREATE EXTENSION ip4r;"
	-psql -d $(DB_NAME) -c "CREATE EXTENSION hstore;"
	-psql -d $(DB_NAME) -c "CREATE EXTENSION citext;"

tables:
	PGPASSWORD=$(DB_PASS) cat ip_net.plsql | sed -e 's/%s/$(DB_NAME)/' | psql -q -h localhost -U $(DB_USER) -d $(DB_NAME)
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) < functions.plsql
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) < triggers.plsql


install: auth db tables
	@echo "##"
ifdef PG_PASS_RAND
	@echo "## A random password was generated '$(DB_PASS)'"
	@echo "## and be set on the new database user 'nipap'."
	@echo "##"
	@echo "## Please note this password as you will need to enter it"
	@echo "## into your nipap.conf configuration file."
else
	@echo "## Environment variable PGPASSWORD is set and its content"
	@echo "## will be used as password on the new database user 'nipap'"
endif
	@echo "##"


clean: clean-db


clean-db:
	dropdb $(DB_NAME)
	dropuser $(DB_USER)


clean-tables:
	PGPASSWORD=$(DB_PASS) psql -q -h localhost -U $(DB_USER) -d $(DB_NAME) < clean.plsql
# TODO: If no password is specified with PGPASSWORD, this operation
# 	will in all likeliness result in a failure, so we should
# 	require a PGPASSWORD
