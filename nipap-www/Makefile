# $Id: Makefile,v 1.6 2011/04/18 17:14:00 lukagarb Exp $
#

PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/nipap-www-build
PROJECT=nipap-www

all:
#	$(PYTHON) setup.py build
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist

install:
	$(PYTHON) setup.py install

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist --dist-dir=../ # --prune
	rename -f 's/$(PROJECT)-(\d.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	debuild -us -uc -sa

distclean:
realclean:
test:
check:

upload:
	python setup.py sdist upload

clean:
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST dist/ debian/$(PROJECT)* debian/files .pc/ debian/patches
	find . -name '*.pyc' -delete
	rm -rf data/sessions/container_file/*
	rm -rf data/sessions/container_file_lock/*
