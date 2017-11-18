# coding: utf8
'''
    PyCampbellCR1000
    ----------------

    Communication tools for Campbell CR1000-type Dataloggers.

    :copyright: Copyright 2012 Salem Harrache and contributors, see AUTHORS.
    :license: BSD, see LICENSE for details.

'''
import re
import sys
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

README = ''
CHANGES = ''
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except:
    pass

REQUIREMENTS = [
    'pylink',
]

if sys.version_info < (2, 7):
    REQUIREMENTS.append('ordereddict')


if sys.version_info < (2, 7) or (3,) <= sys.version_info < (3, 4):
    # In the stdlib from 2.7:
    REQUIREMENTS.append('argparse')


with open(os.path.join(os.path.dirname(__file__), 'pycampbellcr1000',
                       '__init__.py')) as init_py:
    release = re.search("VERSION = '([^']+)'", init_py.read()).group(1)
# The short X.Y version.
version = release.rstrip('dev')


setup(
    name='PyCampbellCR1000',
    version=version,
    url='https://github.com/LionelDarras/PyCampbellCR1000',
    license='GNU GPL v3',
    description='Communication tools for Campbell CR1000-type Dataloggers',
    long_description=README + '\n\n' + CHANGES,
    author='Salem Harrache',
    author_email='salem.harrache@gmail.com',
    maintainer='Lionel Darras',
    maintainer_email='lionel.darras@mom.fr',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=find_packages(),
    zip_safe=False,
    install_requires=REQUIREMENTS,
    test_suite='pycampbellcr1000.tests',
    entry_points={
        'console_scripts': [
            'pycr1000 = pycampbellcr1000.__main__:main'
        ],
    },
)
