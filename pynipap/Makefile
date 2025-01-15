# $Id: Makefile,v 1.6 2011/04/18 17:14:00 lukagarb Exp $
#

PYTHON=`which python3`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/python-pynipap-build
PROJECT=pynipap

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make bumpversion - Bump version to latest in ../NEWS file"
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
	$(PYTHON) setup.py sdist --dist-dir=../
	rename -f 's/$(PROJECT)-(\d.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	debuild -us -uc

distclean:
realclean:
test:
check:

upload:
	$(PYTHON) setup.py sdist upload

clean:
	$(PYTHON) setup.py clean
	rm -rf .pybuild/ MANIFEST dist/ debian/files debian/python-pynipap* \
		debian/python3-pynipap* debian/$(PROJECT).substvars debian/.debhelper \
		debian/debhelper-build-stamp
	find . -name '*.pyc' -delete

VER := $(shell head -n1 ../NEWS | awk '{print $$2}')
bumpversion:
	# replace version number in pynipap.py
	sed -i 's/\(__version__\s*= \)"[^"]\+"/\1"$(VER)"/' pynipap/__init__.py
	#         # update debian/changelog
	../utilities/news2dch.py ../NEWS debian/changelog
