#!/usr/bin/env python
# coding=utf-8

import os
import transitfeed
import json
import sys
import argparse
from osmhelper.osm_helper import OsmHelper
from osmhelper.osm_routes import Route, RouteMaster
from factory.CreatorFactory import CreatorFactory

# Handle arguments
parser = argparse.ArgumentParser(prog='osm2gtfs', description='Create GTFS from OpenStreetMap data.')

# Filename arguments for config and output file
parser.add_argument('--config', '-c', metavar='FILE', type=argparse.FileType('r'), help='Configuration json file')
parser.add_argument('--output', '-o', metavar='FILENAME', type=str, help='Specify GTFS output zip file')

# Refresh caching arguments
group = parser.add_mutually_exclusive_group()
group.add_argument('--refresh-route', metavar='ROUTE', type=int, help='Refresh OSM data for ROUTE')
group.add_argument('--refresh-all-routes', action="store_true", help='Refresh OSM data for all routes')
group.add_argument('--refresh-all-stops', action="store_true", help='Refresh OSM data for all stops')
group.add_argument('--refresh-all', action="store_true", help='Refresh all OSM data')
args = parser.parse_args()

def main():

    # Load config json file
    if args.config is not None:
        config = load_config(args.config)
    elif os.path.isfile('config.json'):
        with open("config.json") as json_file:
            config = load_config(json_file)
    else:
        print('Error: No config.json file found')
        sys.exit(0)

    # Get and check filename for gtfs output
    if args.output is not None:
        output_file = args.output
    elif 'output_file' in config:
        output_file = config['output_file']
    else:
        print('Error: No filename for gtfs file specified')
        sys.exit(0)

    # --refresh-route
    if args.refresh_route is not None:
        OsmHelper.refresh_route(args.refresh_route, "bus", config['query']['bbox'])
        sys.exit(0)
    elif args.refresh_all_routes:
        OsmHelper.get_routes("bus", config['query']['bbox'], refresh=True)
        sys.exit(0)
    elif args.refresh_all_stops:
        OsmHelper.get_stops(OsmHelper.get_routes("bus", config['query']['bbox']), refresh=True)
        sys.exit(0)
    elif args.refresh_all:
        OsmHelper.refresh_data("bus", config['query']['bbox'])
        sys.exit(0)

    # Define (transitfeed) schedule object for GTFS creation
    schedule = transitfeed.Schedule()

    # Initiate OpenStreetMap helper containing data
    data = OsmHelper(config)

    # Initiate creators for GTFS components through an object factory
    factory = CreatorFactory(config)
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
    schedule.WriteGoogleTransitFeed(output_file)

    sys.exit()

def load_config(configfile):
    """
    Loads json from config file
    Return a dictionary with configration data
    """
    try:
        config = json.load(configfile)
    except ValueError, e:
        print('Error: Config json file is invalid')
        print(e)
        sys.exit(0)

    return config

if __name__ == "__main__":
    main()
