# coding=utf-8

import os
import shutil
# import csv
# from osm2gtfs.core.cache import Cache
# import osmium
import pytest
import argparse
import transitfeed
from osm2gtfs.core.configuration import Configuration
from osm2gtfs.core.osm_connector import OsmConnector
from osm2gtfs.core.creator_factory import CreatorFactory

#To run : from osm2gtfs/osm2gtfs, run py.test ./tests/accra_tests.py

def init_accra_data():
    #initialization of cache file, either with osm-transit-extractor or pyosmium
    # selector = 'accra'
    # routes = {}
    # #Acra only use route_masters
    # with open('./fixtures/accra/osm-transit-extractor_lines.csv') as lines_file:
    #     lines_reader = csv.DictReader(lines_file)
    #     for l in lines_reader:
    #         frequency = 60
    #         members = []
    #         route_id = l["line_id"].split(":")[2]
    #         rm = RouteMaster(route_id, l["code"], l["name"], members, frequency)
    #         routes[route_id] = rm
    # Cache.write_data('routes-' + selector, routes)
    current_dir = os.path.dirname(__file__)
    for f in ['routes-accra.pkl', 'stops-accra.pkl']:
        fixture_file = os.path.join(current_dir, 'fixtures/accra/', f) + ".bak"
        cache_file = os.path.join(current_dir, '../../data/', f)
        shutil.copy(fixture_file, cache_file)

class Args():
    def __init__(self, config_file):
        self.config = open(config_file)
        self.output = "../data/accra_tests.zip"

def test_accra():
    #the following is an adaptation of the osm2gtfs main function
    args = Args(os.path.realpath("./creators/accra/accra.json"))
    config = Configuration(args)
    data = OsmConnector(config.config)
    # Define (transitfeed) schedule object for GTFS creation
    schedule = transitfeed.Schedule()

    # Initiate creators for GTFS components through an object factory
    factory = CreatorFactory(config.config)
    agency_creator = factory.get_agency_creator()
    feed_info_creator = factory.get_feed_info_creator()
    routes_creator = factory.get_routes_creator()
    stops_creator = factory.get_stops_creator()
    trips_creator = factory.get_trips_creator()

    # Add data to schedule object
    agency_creator.add_agency_to_schedule(schedule)
    feed_info_creator.add_feed_info_to_schedule(schedule)
    routes_creator.add_routes_to_schedule(schedule, data)
    stops_creator.add_stops_to_schedule(schedule, data)
    trips_creator.add_trips_to_schedule(schedule, data)

    # Validate GTFS
    schedule.Validate(transitfeed.ProblemReporter())

    # Write GTFS
    schedule.WriteGoogleTransitFeed(config.output)
