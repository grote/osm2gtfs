osm2gtfs
========

Use public transport data from OpenStreetMap and external schedule information to create a General Transit Feed (GTFS).

**Attention:** The source code is currently very specific to one city, but this can be developed into something more generic.
You can help with pull requests that introduce an abstraction layer for the external schedule information.

## How does it work?

The osmhelper is responsible for retrieving current data directly from OpenStreetMap
via the Overpass and OSM API.
This data is stored in python objects and cached on disk for efficient re-use.
The osm2gtfs script then uses the OpenStreetMap data and local schedule information
to create a GTFS file using Google's transitfeed library and validates it after creation.

## Depends

- https://github.com/DinoTools/python-overpy
- https://github.com/google/transitfeed
- https://github.com/metaodi/osmapi

## Install

    pip install -r requirements.txt

## Use

    python osm2gtfs.py -c fenix.json.example

## License

![GNU GPLv3 Image](https://www.gnu.org/graphics/gplv3-127x51.png)

This program is Free Software: You can use, study share and improve it at your
will. Specifically you can redistribute and/or modify it under the terms of the
[GNU General Public License](https://www.gnu.org/licenses/gpl.html) as
published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
