osm2gtfs
========

[![Build Status](https://travis-ci.org/grote/osm2gtfs.svg?branch=master)](https://travis-ci.org/grote/osm2gtfs)

Use public transport data from [OpenStreetMap](http://www.openstreetmap.org/)
and external schedule information
to create a General Transit Feed ([GTFS](https://developers.google.com/transit/gtfs/)).

The official source code repository is at [github.com/grote/osm2gtfs](https://github.com/grote/osm2gtfs).

How does it work?
-----------------

The script retrieves current data about public transport networks directly from
OpenStreetMap via the Overpass API. It stores the data in python objects and
caches on disk for efficient re-use. Then the data is combined with another
source of schedule (time) information in order to create a GTFS file using the
transitfeed library.

For every new city a new [configuration file](https://github.com/grote/osm2gtfs/wiki/Configuration)
needs to be created and the input of schedule information is preferred
in a certain [format](https://github.com/grote/osm2gtfs/wiki/Schedule).
For any city the script can be easily extended, see the
[developer documentation](https://github.com/grote/osm2gtfs/wiki/Development)
for more information.

Included cities
-----------------

* [Florianópolis, Brazil](https://github.com/grote/osm2gtfs/blob/master/osm2gtfs/creators/fenix/fenix.json)
* [Suburban trains in Costa Rica](https://github.com/grote/osm2gtfs/blob/master/osm2gtfs/creators/incofer/incofer.json)
* [Accra, Ghana](https://github.com/grote/osm2gtfs/blob/master/osm2gtfs/creators/accra/accra.json)
* [Managua, Ciudad Sandino](https://github.com/grote/osm2gtfs/blob/master/osm2gtfs/creators/managua/managua.json) and [Estelí](https://github.com/grote/osm2gtfs/blob/master/osm2gtfs/creators/esteli/esteli.json) in Nicaragua

*Soon, also in your city*

Install
------------

Install by running

    pip install -e .

Requirements
------------
Automatically installed by the previous step:
* https://github.com/DinoTools/python-overpy
* https://github.com/google/transitfeed

Use
------------

    osm2gtfs -c <config-file>

Example:

    $ osm2gtfs -c osm2gtfs/creators/fenix/fenix.json

License
-------

![GNU GPLv3 Image](https://www.gnu.org/graphics/gplv3-127x51.png)

This program is Free Software: You can use, study share and improve it at your
will. Specifically you can redistribute and/or modify it under the terms of the
[GNU General Public License](https://www.gnu.org/licenses/gpl.html) as
published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
