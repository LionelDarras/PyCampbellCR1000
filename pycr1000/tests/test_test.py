# coding: utf8
'''
    pyvantagepro.tests.test_link
    ----------------------------

    The pyvantagepro test suite.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: GNU GPL v3.

'''
from __future__ import unicode_literals

from ..logger import active_logger


# active logging for tests
active_logger()


class TestTest:
    ''' Test test.'''
    def setup_class(self):
        '''Setup common data.'''
        pass

    def test_test(self):
        '''Test test.'''
        assert 5 + 5 == 10
