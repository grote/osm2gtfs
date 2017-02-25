osm2gtfs
========

Use public transport data from OpenStreetMap and external schedule information
to create a General Transit Feed (GTFS).

How does it work?
-----------------

The script retrieves current data about public transport networks directly from
OpenStreetMap via the Overpass API. It stores the data in python objects and
caches on disk for efficient re-use. Then the data is combined with another
source of schedule (time) information in order to create a GTFS file using the
transitfeed library.

**Attention:** The source code is currently very specific to Florianópolis Buses
and Costa Rica Urban Train, but it can be extended to make it work for your use
case. In the config file any transit network can be specified for download from
OpenStreetMap. And by extending the creator classes in code, different
approaches for time information handling can be easily implemented. You can help
with pull requests to improve this script.

Use
------------

    python osm2gtfs.py -c <config-file>

Example:

    $ python osm2gtfs.py -c creators/fenix/fenix.json

Requirements
------------

Install dependencies by running

    pip install -r requirements.txt

* https://github.com/DinoTools/python-overpy
* https://github.com/google/transitfeed

License
-------

![GNU GPLv3 Image](https://www.gnu.org/graphics/gplv3-127x51.png)

This program is Free Software: You can use, study share and improve it at your
will. Specifically you can redistribute and/or modify it under the terms of the
[GNU General Public License](https://www.gnu.org/licenses/gpl.html) as
published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
