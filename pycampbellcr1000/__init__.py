# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000
    ----------------

    The public API and command-line interface to PyCampbellCR1000.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
# Make sure the logger is configured early:
from .logger import LOGGER, active_logger
from .pakbus import PakBus
from .device import CR1000


VERSION = '0.4dev'
__version__ = VERSION
