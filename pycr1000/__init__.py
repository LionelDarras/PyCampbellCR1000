# -*- coding: utf-8 -*-
'''
    PyCR1000
    --------

    The public API and command-line interface to PyCR1000.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

'''
# Make sure the logger is configured early:
from .logger import LOGGER, active_logger

VERSION = '0.1dev'
__version__ = VERSION
