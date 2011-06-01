DB_NAME=nap
NAPD_USER=napd
NAPD_PASS=dpan

all:
	echo "Run this as the postgres user!"


db:
	createuser -S -D -R $(NAPD_USER)
	createdb -O $(NAPD_USER) $(DB_NAME)
	psql -q -c "ALTER USER napd ENCRYPTED PASSWORD '$(NAPD_PASS)'"

install:
	psql -q -d $(DB_NAME) -c 'CREATE LANGUAGE plpgsql' || true
	psql -q -d $(DB_NAME) -f find_free_prefix.plsql
	psql -q -d $(DB_NAME) -f get_prefix.plsql
	psql -q -d $(DB_NAME) -f calc_indent.plsql
	psql -q -d $(DB_NAME) -f ip_net.plsql

clean:
	psql -q -d $(DB_NAME) -f clean.plsql
