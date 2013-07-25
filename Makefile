# $Id: Makefile,v 1.6 2011/04/18 17:14:00 lukagarb Exp $
#

# for use lates, when we have cleaned up a bit!
#SUBPROJ=`find $(CURDIR)/* -maxdepth 0 -type d`
SUBPROJ=nipap pynipap nipap-www nipap-cli
APTDIR=apt
CURBRANCH=$(shell git branch --no-color 2> /dev/null | awk '/\\*/ { printf("%s", $$2); }')

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make debrepo - Create Packages.gz file suitable for github apt repo"

source:
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make source; cd ..; \
	done

install:
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make install; cd ..; \
	done

buildrpm:
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make buildrpm; cd ..; \
	done

builddeb:
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make builddeb; cd ..; \
	done

debrepo:
ifeq ($(CURBRANCH), $(shell echo -n 'gh-pages'))
	for CHANGEFILE in `ls *.changes`; do \
		cd repos/apt; \
		reprepro --ignore=wrongdistribution -Vb . include stable ../../$$CHANGEFILE; \
		cd ../.. ; \
	done
else
	@echo "Please switch to branch: gh-pages"
endif

clean:
	rm -f *.deb
	rm -f *.tar.gz
	rm -f *.build
	rm -f *.changes
	rm -f *.dsc
	rm -f *.diff.gz
	rm -rf repos/apt/db repos/apt/dist repos/apt/pool
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make clean; cd ..; \
	done
