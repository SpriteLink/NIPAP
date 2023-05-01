#
# Set up a wsgi environment for mod_wsgi
#

import os, sys

from nipapwww import create_app

application = create_app()
