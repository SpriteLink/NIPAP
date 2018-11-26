#
# Set up a wsgi environment for mod_wsgi
#
import os, sys, logging.config

APP_CONFIG="/etc/nipap/nipap-www.ini"

logging.config.fileConfig(APP_CONFIG)

os.environ['PYTHON_EGG_CACHE'] = '/var/cache/nipap-www/eggs'

from paste.deploy import loadapp
application = loadapp('config:%s' % APP_CONFIG)
