"""Pylons environment configuration"""
import os

from jinja2 import Environment, FileSystemLoader
from pylons.configuration import PylonsConfig

import nipapwww.lib.app_globals as app_globals
import nipapwww.lib.helpers
from nipapwww.config.routing import make_map

import pynipap
from nipap.nipapconfig import NipapConfig

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    config = PylonsConfig()
    
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='nipapwww', paths=paths)

    config['routes.map'] = make_map(config)
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.h'] = nipapwww.lib.helpers
    
    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)
    

    # Create the Jinja2 Environment
    jinja2_env = Environment(autoescape=True,
            extensions=['jinja2.ext.autoescape'],
            loader=FileSystemLoader(paths['templates']))
    config['pylons.app_globals'].jinja2_env = jinja2_env

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
    config['pylons.strict_c'] = False

    # Make sure that there is a configuration object
    cfg = NipapConfig(config['nipap_config_path'], 
        { 'auth_cache_timeout': '3600' })

    # set XML-RPC URI in pynipap module
    pynipap.xmlrpc_uri = cfg.get('www', 'xmlrpc_uri')

    return config
