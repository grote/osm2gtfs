osm2gtfs tests
==============

Accra
------
#### Description

There are 3 unittests for the Accra GTFS generation

1. Generation of the cache stops Data from an Overpass result Mock
1. Generation of the cache routes Data from an Overpass result Mock
1. Generation of the GTFS ZIP File using the previously generated cache data
and

#### Validation of the GTFS

The generated GTFS is checked against a reference GTFS file (accra_tests.zip.ref)
in the `tests/fixtures/accra/` folder. For the moment, only the size of each GTFS file is compared to the reference.

#### How to run
To run all the tests (from the root `osm2gtfs` folder) :

    $ python -m unittest discover

To run only the Accra tests :

    $ python osm2gtfs/tests/tests_accra.py
