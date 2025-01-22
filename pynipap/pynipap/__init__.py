from .pynipap import *

__version__     = "0.32.7"
__author__      = "Kristian Larsson, Lukas Garberg"
__author_email__= "kll@tele2.net, lukas@spritelink.net"
__copyright__   = "Copyright 2011, Kristian Larsson, Lukas Garberg"
__license__     = "MIT"
__status__      = "Development"
__url__         = "http://SpriteLink.github.io/NIPAP"


# This variable holds the URI to the nipap XML-RPC service which will be used.
# It must be set before the Pynipap can be used!
xmlrpc_uri = None

# If set, the value assigned to the variable below will be used as a bearer
# token.
bearer_token = None

# Caching of objects is enabled per default but can be disabled for certain
# scenarios. Since we don't have any cache expiration time it can be useful to
# disable for long running applications.
CACHE = True
