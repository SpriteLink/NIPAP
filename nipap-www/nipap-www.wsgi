#
# Set up a wsgi environment for mod_wsgi
#

import os, sys
sys.path.append('/path/to/nipap/NIPAP/nipap-www/')
os.environ['PYTHON_EGG_CACHE'] = '/var/cache/nipap-www/eggs'

from paste.deploy import loadapp

application = loadapp('config:/etc/nipap/nipap-www.ini')
