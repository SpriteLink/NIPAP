# $Id: Makefile,v 1.6 2011/04/18 17:14:00 lukagarb Exp $
#

SUBPROJ=nipap pynipap nipap-www nipap-cli whoisd
APTDIR=apt
CURBRANCH=$(shell git branch --no-color 2> /dev/null | awk '/\\*/ { printf("%s", $$2); }')

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"
	@echo "make bumpversion - Bump version to latest in NEWS file"
	@echo "make debrepo-stable - Copy packages from testing repo into stable repo"
	@echo "make debrepo-testing - Create or update the testing repo"

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

ifeq ($(CURBRANCH), $(shell echo -n 'gh-pages'))
debrepo-stable: debrepo-stable-run
else
debrepo-stable:
	@echo "Please switch to branch: gh-pages"
	@echo "If you want to force the building of a debrepo, run 'make debrepo-run'"
endif

ifeq ($(CURBRANCH), $(shell echo -n 'gh-pages'))
debrepo-testing: debrepo-testing-run
else
debrepo-testing:
	@echo "Please switch to branch: gh-pages"
	@echo "If you want to force the building of a debrepo, run 'make debrepo-testing-run'"
endif

debrepo-stable-run:
	cd repos/apt; \
	for PACKAGE in `reprepro list testing | awk '{ print $$2 }' | sort | uniq`; do \
		reprepro copy stable testing $$PACKAGE; \
	done; \
	cd ../..

debrepo-testing-run:
	for CHANGEFILE in `ls *.changes`; do \
		cd repos/apt; \
		reprepro --ignore=wrongdistribution -Vb . include testing ../../$$CHANGEFILE; \
		cd ../.. ; \
	done

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

bumpversion:
	for PROJ in $(SUBPROJ); do \
		cd $$PROJ; make bumpversion; cd ..; \
	done
