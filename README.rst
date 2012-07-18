PyCampbellCR1000 : Query the Campbell CR1000-type Dataloggers
=============================================================

PyCampbellCR1000 is a python project which aims to allow the communication with
Campbell CR1000 Type Datalogger

The main features include automatic collecting of data and settings (read only)
as a list of dictionnaries.

The tool can be used in your python scripts for data post-processing,
or in command line mode to collect data as CSV.

We don't update anything from PyCampbellCR1000 besides time,
because we are assuming that the dataloggers are already configured.

**Note:** PyCampbellCR1000 uses the `PyLink <http://pypi.python.org/pypi/PyLink>`_ lib, offers a universal communication interface with File-Like API.


Examples
--------

We init communication by giving the datalogger URL.


::

  >>> from pycampbellcr1000 import CR1000
  >>> device = CR1000.from_url('tcp:host-ip:port')
  >>> # or with Serial connection
  >>> device = CR1000.from_url('serial:/dev/ttyUSB0:38400')

To get time, use:

::

  >>> device.gettime()
  datetime.datetime(2012, 7, 16, 12, 27, 55)

To get data, you have to enter the table name where it is stored.
If you don't know the table name, you cannot collect the list of available
tables in the datalogger.


::

  >>> device.list_tables()
  ['Status', 'Table1', 'Public']

Choose the time period to get your data from `start date` to `stop date`.


::

  >>> import datetime
  >>> start = datetime.datetime(2012, 7, 16, 11, 0, 0)
  >>> stop = datetime.datetime(2012, 7, 16, 12, 0, 0)
  >>> data = device.get_data('Table1', start, stop)
  >>> data[0]["Datetime"]
  datetime.datetime(2012, 7, 16, 11, 0)

::

  >>> data[0]["CurSensor1_mVolt_Avg"]
  2508.0

::

  >>> print(data.filter(('Datetime', 'CurSensor3_mAmp_Avg')).to_csv())
  Datetime,CurSensor3_mAmp_Avg
  2012-07-16 11:00:00,18.7
  2012-07-16 11:01:00,18.48
  ...
  2012-07-16 11:59:00,17.25


Features
--------

* Collecting data as a list of dictionaries
* Collecting data in a CSV file
* Reading and adjusting the data logger's internal clock
* Retrieving table definitions
* Listing table names
* Reading settings
* Collect file list and download file content
* Tested with CR1000 and CR800 dataloggers (should work with CR3000 datalogger)
* Various types of connections are supported (TCP, UDP, Serial, GSM)
* Comes with a command-line script
* Compatible with Python 2.6+ and 3.x


Installation
------------

You can install, upgrade, uninstall PyVantagePro with these commands

::

    $ pip install pycampbellcr1000
    $ pip install --upgrade pycampbellcr1000
    $ pip uninstall pycampbellcr1000

Or if you don't have pip

::

  $ easy_install pycampbellcr1000

Or you can get the `source code from github
<https://github.com/SalemHarrache/PyCampbellCR1000>`_.

::

  $ git clone https://github.com/SalemHarrache/PyCampbellCR1000.git
  $ cd PyCampbellCR1000
  $ python setup.py install


Documentation
-------------

See documentation here: http://pycampbellcr1000.readthedocs.org
