"""
  Entry point for a fabric based application.
  Fabric tasks are organize in python module. So, here we just import dependencies to have task available from command
  line.
"""

"""
  Import Fabric fwk
"""
from fabric.api import *

"""
  Import misc task like checkout and load_settings
"""
from sauron import versionning, settings

"""
  Load Drupal tasks
"""
from sauron.drupal import code_style, update