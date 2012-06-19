# -*- coding: utf-8 -*-
'''
    pycr1000.parser
    ---------------

    Allows parsing CR1000 data.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import division, unicode_literals
import struct
from datetime import datetime
from array import array

from .compat import bytes
from .logger import LOGGER
from .utils import (cached_property, bytes_to_hex, Dict, bytes_to_binary,
                    binary_to_int)
