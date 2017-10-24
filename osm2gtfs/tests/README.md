osm2gtfs tests
==============

To run all the tests (from the root `osm2gtfs` folder) :

    $ python -m unittest discover -v -t .

## Core

Tests for core components must be named and placed in the following schema:
  `core/test_<FILENAME>.py`

### Creators Factory

#### Description

The creator factory allows certain parts of the GTFS generation from OSM data
to be overridden by different regions and networks. The tests make sure that
newly added creators follow the established naming convention of:
 `<ISO 3166-2 two letter country code>_<city/state/region>[_<network/operator>]`

#### How to run

    $ python osm2gtfs/tests/core/tests_creator_factory.py

## Creators

Tests for core components must be named and placed in the following schema:
  `creators/test_<SELECTOR>.py`

### Accra, Ghana

#### Description

There are 3 acceptance tests for the Accra GTFS generation

1. Obtain mock-up data on stops from OpenStreetMap and cache it,
1. Obtain mock-up data on routes from OpenStreetMap and cache it,
1. Generate GTFS file from using the previously generated cache data.

#### Validation of the GTFS

The generated GTFS is checked against a reference GTFS file (gh_accra_tests.zip.ref)
in the `tests/creators/fixtures/gh_accra/` folder. For the moment, only the size of each GTFS file is compared to the reference.

#### How to run

    $ python osm2gtfs/tests/creators/tests_gh_accra.py
