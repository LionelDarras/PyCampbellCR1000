# -*- coding: utf-8 -*-
'''
    PyCampbellCR1000.logger
    -----------------------

    Logging setup.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals
import logging
from .compat import NullHandler


LOGGER = logging.getLogger('pycampbellcr1000')
LOGGER.addHandler(NullHandler())


def active_logger():
    '''Initialize a speaking logger with stream handler (stderr).'''
    LOGGER = logging.getLogger('pycampbellcr1000')

    LOGGER.setLevel(logging.INFO)

    # Default to logging to stderr.
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s ')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    LOGGER.addHandler(stream_handler)
