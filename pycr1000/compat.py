# coding: utf8
"""
    pycr1000.compat
    ---------------

    Workarounds for compatibility with Python 2 and 3 in the same code base.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

"""

import sys

# -------
# Pythons
# -------

# Syntax sugar.
_ver = sys.version_info

#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)

#: Python 3.0.x
is_py30 = (is_py3 and _ver[1] == 0)

#: Python 3.1.x
is_py31 = (is_py3 and _ver[1] == 1)

#: Python 3.2.x
is_py32 = (is_py3 and _ver[1] == 2)

#: Python 3.3.x
is_py33 = (is_py3 and _ver[1] == 3)

#: Python 3.4.x
is_py34 = (is_py3 and _ver[1] == 4)

#: Python 2.7.x
is_py27 = (is_py2 and _ver[1] == 7)

#: Python 2.6.x
is_py26 = (is_py2 and _ver[1] == 6)

# ---------
# Specifics
# ---------

if is_py2:
    if is_py26:
        from logging import Handler

        class NullHandler(Handler):
            def emit(self, record):
                pass
    else:
        from logging import NullHandler
    from StringIO import StringIO

    def to_char(string):
        if len(string) == 0:
            return bytes('')
        return bytes(string[0])

    bytes = str
    str = unicode
    stdout = sys.stdout
    xrange = xrange


elif is_py3:
    from logging import NullHandler
    from io import StringIO

    def to_char(string):
        if len(string) == 0:
            return str('')
        return str(string[0])

    str = str
    bytes = bytes
    stdout = sys.stdout.buffer
    xrange = range
