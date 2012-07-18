=============================================================
PyCampbellCR1000 : Query the Campbell CR1000-type Dataloggers
=============================================================

.. module:: pycampbellcr1000

PyCampbellCR1000 is a python project which aims to allow the communication with
Campbell CR1000 Type Datalogger

The main features include automatic collecting of data and settings (read only)
as a list of dictionnaries.

The tool can be used in your python scripts for data post-processing,
or in command line mode to collect data as CSV.

We don't update anything from PyCampbellCR1000 besides time,
because we are assuming that the dataloggers are already configured.

**Note:** PyCampbellCR1000 uses the `PyLink <http://pypi.python.org/pypi/PyLink>`_ lib, offers a universal communication interface with File-Like API.

--------
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


--------
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


------------
Installation
------------

You can install, upgrade, uninstall PyVantagePro with these commands

.. code-block:: console

    $ pip install pycampbellcr1000
    $ pip install --upgrade pycampbellcr1000
    $ pip uninstall pycampbellcr1000

Or if you don't have pip

.. code-block:: console

  $ easy_install pycampbellcr1000

Or you can get the `source code from github
<https://github.com/SalemHarrache/PyCampbellCR1000>`_.

.. code-block:: console

  $ git clone https://github.com/SalemHarrache/PyCampbellCR1000.git
  $ cd PyCampbellCR1000
  $ python setup.py install

----------------------------
About CR1000 Type Datalogger
----------------------------

This can be read in the `BMP5 Transparent Commands Manual Rev 9/08`_ :

.. _`BMP5 Transparent Commands Manual Rev 9/08`: https://github.com/SalemHarrache/PyCampbellCR1000/blob/master/docs/references/bmp5-transparent-commands.pdf?raw=true

.. note::
    The CR1000 type datalogger (CR1000, CR3000, and CR800) is a rugged and versatile
    measurement device. This datalogger contains a CPU and both digital and analog inputs
    and outputs. The CR1000 type datalogger uses a PakBus operating system and
    communicates with applications via the BMP5 message protocol. Programs sent to the
    datalogger are written in a BASIC-like language that includes data processing and
    analysis routines. These programs run on a precise execution interval and will store
    measurements and data in tables.


PyCampbellCR1000 implement part of `Pakbus`_ protocol and can thus
communicate with this type of datalogger.

.. _`Pakbus`: http://www.campbellsci.com/cr100-enhance-pakbus

We only tested it with CR1000 and CR800 dataloggers. If you have a CR3000
datalogger, feel free to test the tool and inform us about the compatibility
with your machine.


------------------
Command-line usage
------------------

PyCampbellCR1000 has a command-line script that interacts with the datalogger.

.. code-block:: console

  $ pycr1000 -h
  usage: pycr1000 [-h] [--version] {gettime,settime,getprogstat,getsettings,
                                    listfiles, getfile,listtables,getdata,
                                    update} ...

  Communication tools for Campbell CR1000-type Datalogger

  optional arguments:
    -h, --help            Show this help message and exit
    --version             Print PyCR1000’s version number and exit.

  The PyCR1000 commands:
      gettime             Print the current datetime of the datalogger.
      settime             Set the given datetime argument on the datalogger.
      getprogstat         Retrieve available programming statistics information
                          from the datalogger.
      getsettings         Retrieve the datalogger settings.
      listfiles           List all files stored in the datalogger.
      getfile             Get the file content from the datalogger.
      listtables          List all tables stored in the datalogger.
      getdata             Extract data from the datalogger between start
                          datetime and stop datetime.By default the entire
                          contents of the data will be downloaded.
      update              Update CSV database records with getting automatically
                          new records.


Gettime
-------

The `gettime` command gives, as its name suggests, the current datetime of
the datalogger.

.. code-block:: console

    $ pycr1000 gettime -h
    usage: pycr1000 gettime [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                            [--code CODE] [--debug]
                            url

    Print the current datetime of the datalogger.

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)


**Example**

.. code-block:: console

    $ pycr1000 gettime serial:COM1:38400
    2012-07-16 21:57:30


Settime
-------

Allows us to update the datalogger datetime and returns the new value.

.. code-block:: console

    $ pycr1000 settime -h
    usage: pycr1000 settime [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                          [--code CODE] [--debug]
                          url datetime

    positional arguments:
    url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                       serial:/dev/ttyUSB0:19200:8N1
    datetime           The chosen datetime value. (like : "2012-07-16 21:58")

    optional arguments:
    -h, --help         Show this help message and exit
    --timeout TIMEOUT  Connection link timeout (default: 10.0)
    --src SRC          Source node ID (default: 2050)
    --dest DEST        Destination node ID (default: 1)
    --code CODE        Datalogger security code (default: 0)
    --debug            Display log (default: False)

**Example**

.. code-block:: console

    $ pycr1000 settime serial:/dev/ttyUSB0:19200:8N1 "2012-07-16 23:00"
    Old Time : 2012-07-16 22:00
    Current Time : 2012-07-16 23:00


Getprogstat
-----------

Retrieve available programming statistics from the datalogger.

.. code-block:: console

    $ pycr1000 getprogstat -h
    usage: pycr1000 getprogstat [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                                [--code CODE] [--debug]
                                url

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)


**Example**

.. code-block:: console

    $ pycr1000 getprogstat tcp:localhost:1112
    CompResult : CPU:CR1000_LABO.CR1 -- Compiled in PipelineMode.
    PowUpProg : CPU:CR1000_LABO.CR1
    OSSig : 12288
    ProgName : CPU:CR1000_LABO.CR1
    CompState : 1
    ProgSig : 2993
    OSVer : CR1000.Std.24
    CompTime : 2012-07-13 11:49:02
    SerialNbr : E4668


Getsettings
-----------

Retrieve the datalogger settings as CSV.

.. code-block:: console

    $ pycr1000 getsettings -h
    usage: pycr1000 getsettings [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                                [--code CODE] [--debug] [--output OUTPUT]
                                [--delim DELIM]
                                url

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)
      --output OUTPUT    Filename where output is written (default: <stdout>)
      --delim DELIM      CSV char delimiter (default: ',')

**Example**

.. code-block:: console

    $ pycr1000 getsettings tcp:127.0.0.1:1112
    SettingId,SettingValue,ReadOnly,LargeValue
    0,'CR1000.Std.24\x00',1,0
    1,'E\x00\x12<',1,0
    ...

Listfiles
---------

Lists all files stored in the datalogger.

.. code-block:: console

    $ pycr1000 listfiles -h
    usage: pycr1000 listfiles [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                              [--code CODE] [--debug]
                              url

    Lists all files stored in the datalogger.

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)


**Example**

.. code-block:: console

    $ pycr1000 listfiles tcp:localhost:1112
    CPU:
    CPU:templateexample.cr1
    CPU:CR1000_LABO.CR1


Getfile
-------

Get the file content from the datalogger.

.. code-block:: console

    $ pycr1000 getfile -h
    usage: pycr1000 getfile [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                            [--code CODE] [--debug]
                            url filename output

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1
      filename           Filename to be downloaded.
      output             Filename where output is written

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)


**Example**

.. code-block:: console

    $ pycr1000 getfile tcp:localhost:1112 "CPU:templateexample.cr1" ./templateexample.cr1
    $ head templateexample.cr1
    'CR1000/800/850 Series Datalogger
    'This Program is the Same as the default template in the
    'CRBasic Editor.

    'Declare Public Variables
    'Example:
    Public PTemp, batt_volt

    'Declare Other Variables
    'Example:


Listtables
----------

Lists all table names stored in the datalogger.

.. code-block:: console

    $ pycr1000 listtables -h
    usage: pycr1000 listtables [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                               [--code CODE] [--debug]
                               url


    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)


**Example**

.. code-block:: console

    $ pycr1000 listtables tcp:localhost:1112
    Status
    Table1
    Public


Getdata
-------

Extract data from the datalogger between start datetime and stop datetime. By
default the entire contents will be downloaded.

.. code-block:: console

    $ pycr1000 getdata -h
    usage: pycr1000 getdata [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                            [--code CODE] [--debug] [--start START] [--stop STOP]
                            [--delim DELIM]
                            url table output

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1
      table              The table name used for data collection
      output             Filename where output is written

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)
      --start START      The beginning datetime record (like : "2012-07-17 11:25")
                         (default: None)
      --stop STOP        The stopping datetime record (like : "2012-07-17 11:25")
                         (default: None)
      --delim DELIM      CSV char delimiter (default: ,)

**Example**

.. code-block:: console

    $ pycr1000 getdata tcp:localhost:1112 'Table1' \
    --start "2012-07-17 10:25" --stop "2012-07-17 11:25" ./my_data.csv
    Your download is starting.
    Packet 0 with 47 records
    Packet 1 with 13 records
    ---------------------------
    60 new records were found

.. code-block:: console

    $ head my_data.csv
    Datetime,RecNbr,CurSensor1_mVolt_Avg,CurSensor3_mVolt_Avg, CurSensor3_mAmp_Avg
    2012-07-17 10:25:00,75717,2509.0,2508.0,15.97
    2012-07-17 10:26:00,75718,2509.0,2508.0,15.69
    2012-07-17 10:27:00,75719,2509.0,2508.0,17.76
    2012-07-17 10:28:00,75720,2509.0,2508.0,16.75
    2012-07-17 10:29:00,75721,2509.0,2508.0,16.58
    2012-07-17 10:30:00,75722,2509.0,2508.0,16.64


Update
------

Update CSV database records by getting automatically new records.

.. code-block:: console

    $ pycr1000 update -h
    usage: pycr1000 update [-h] [--timeout TIMEOUT] [--src SRC] [--dest DEST]
                           [--code CODE] [--debug] [--delim DELIM]
                           url table db

    positional arguments:
      url                Specifiy URL for connection link. E.g. tcp:iphost:port or
                         serial:/dev/ttyUSB0:19200:8N1
      table              The table name used for data collection
      db                 The CSV file database

    optional arguments:
      -h, --help         Show this help message and exit
      --timeout TIMEOUT  Connection link timeout (default: 10.0)
      --src SRC          Source node ID (default: 2050)
      --dest DEST        Destination node ID (default: 1)
      --code CODE        Datalogger security code (default: 0)
      --debug            Display log (default: False)
      --delim DELIM      CSV char delimiter (default: ,)

**Examples**

If the file does not exist, it will be created automatically.

.. code-block:: console

    $ pycr1000 update tcp:localhost:1112 'Table1' ./db.csv
    Your download is starting.
    Packet 0 with 48 records
    Packet 1 with 47 records
    Packet 2 with 47 records
    Packet 3 with 47 records
    Packet 4 with 47 records
    Packet 5 with 47 records
    ...
    Packet 1574 with 47 records
    Packet 1575 with 47 records
    Packet 1576 with 47 records
    Packet 1577 with 47 records
    Packet 1578 with 47 records
    Packet 1579 with 7 records
    ---------------------------
    74261 new records were found

1 minute later...

.. code-block:: console

    $ pycr1000 update tcp:localhost:1112 'Table1' ./db.csv
    Your download is starting.
    Packet 0 with 1 records
    ---------------------------
    1 new record was found

5 seconds later...

.. code-block:: console

    $ pycr1000 update tcp:localhost:1112 'Table1' ./db.csv
    Your download is starting.
    Packet 0 with 0 records
    ---------------------------
    No new records were found﻿


Debug mode
----------

You can use debug option if you want to print log and see the flowing data.

.. code-block:: console

    $ pycr1000 gettime tcp:localhost:1112 --debug
    2012-07-17 11:58:11,866 INFO: init client
    2012-07-17 11:58:11,866 INFO: Get the node attention
    2012-07-17 11:58:11,866 INFO: Create header
    2012-07-17 11:58:11,866 INFO: Packet data: 90 01 58 02 00 01 08 02 09 01 00 02 07 08
    2012-07-17 11:58:11,866 INFO: Calculate signature for packet
    2012-07-17 11:58:11,866 INFO: Calculate signature nullifier to create packet
    2012-07-17 11:58:11,866 INFO: Quote packet
    2012-07-17 11:58:11,866 INFO: Write: BD 90 01 58 02 00 01 08 02 09 01 00 02 07 08 F6 86 BD
    2012-07-17 11:58:11,866 INFO: Wait packet with transaction 1
    2012-07-17 11:58:11,931 INFO: Read packet: A8 02 10 01 08 02 00 01 89 01 00 01 FF FF 6C 75
    2012-07-17 11:58:11,931 INFO: Unquote packet
    2012-07-17 11:58:11,931 INFO: Check signature : OK
    2012-07-17 11:58:11,931 INFO: Decode packet
    2012-07-17 11:58:11,931 INFO: HiProtoCode, MsgType = <0, 89>


.. _api:

-------------
API reference
-------------

High level API
--------------

.. autoclass:: pycampbellcr1000.device.CR1000
    :members: from_url, send_wait, ping_node, gettime, settime, settings, getfile, table_def, list_tables, get_data, get_data_generator, getprogstat, bye

.. autoclass:: pycampbellcr1000.utils.Dict
    :members: to_csv, filter

.. autoclass:: pycampbellcr1000.utils.ListDict
    :members: to_csv, filter, sorted_by

.. autoexception:: pycampbellcr1000.exceptions.NoDeviceException

.. autoexception:: pycampbellcr1000.exceptions.BadSignatureException

.. autoexception:: pycampbellcr1000.exceptions.BadDataException

.. autoexception:: pycampbellcr1000.exceptions.DeliveryFailureException


Low level API
-------------

.. autoclass:: pycampbellcr1000.pakbus.PakBus
    :members: write, read, wait_packet, pack_header, compute_signature, compute_signature_nullifier, quote, unquote, encode_bin, decode_bin, decode_packet, get_hello_cmd, get_hello_response, unpack_hello_response, unpack_failure_response, get_getsettings_cmd, unpack_getsettings_response, get_collectdata_cmd, unpack_collectdata_response, get_clock_cmd, unpack_clock_response, get_getprogstat_cmd, unpack_getprogstat_response, get_fileupload_cmd, unpack_fileupload_response, unpack_pleasewait_response, get_bye_cmd, parse_filedir, parse_tabledef, parse_collectdata

---------------------
Feedback & Contribute
---------------------

Your feedback is more than welcome. Write email to the
`PyCampbellCR1000 mailing list`_.

.. _`PyCampbellCR1000 mailing list`: pycampbellcr1000@librelist.com

There are several ways to contribute to the project:

#. Post bugs and feature `requests on github`_.
#. Fork `the repository`_ on Github to start making your changes.
#. Test with new CR1000 Type dataloggers.
#. Write a test which shows that the bug was fixed or that the feature works as expected.
#. Send a pull request and bug the maintainer until it gets merged and published. :) Make sure to add yourself to AUTHORS_.

.. _`requests on github`: https://github.com/SalemHarrache/PyCampbellCR1000/issues
.. _`the repository`: https://github.com/SalemHarrache/PyCampbellCR1000
.. _AUTHORS: https://github.com/SalemHarrache/PyCampbellCR1000/blob/master/AUTHORS.rst

.. include:: ../CHANGES.rst
