# -*- coding: utf-8 -*-

__author__ = 'Daniel Williams'
__email__ = 'mail@daniel-williams.co.uk'
__version__ = '0.1.0'
__packagename__ = "acreroad_1420"

from pkg_resources import resource_string, resource_stream, resource_filename
import ConfigParser, os
default_config = resource_stream(__name__, '{}.conf'.format(__packagename__))
CONFIGURATION = ConfigParser.ConfigParser()
#if not config_file:
CONFIGURATION.readfp(default_config)
CONFIGURATION.read([os.path.join(direc, ".{}".format(__packagename__)) for direc in (os.curdir, os.path.expanduser("~"), "/etc/{}".format(__packagename__))])

# Load the radio sources catalogue
CATALOGUE = resource_filename(__name__, 'radiosources.cat')
# SOURCES = 
# #if not config_file:
# CONFIGURATION.readfp(default_config)
# CONFIGURATION.read([os.path.join(direc, ".{}_radiosources.cat".format(__packagename__)) for direc in (os.curdir, os.path.expanduser("~"), "/etc/{}".format(__packagename__))])
