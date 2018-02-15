#!/usr/bin/env python
# coding=utf-8

import sys
import argparse
import transitfeed
from core.configuration import Configuration
from core.osm_connector import OsmConnector
from core.creator_factory import CreatorFactory

# Handle arguments
parser = argparse.ArgumentParser(
    prog='osm2gtfs', description='Create GTFS from OpenStreetMap data.')

# Filename arguments for config and output file
parser.add_argument('--config', '-c', metavar='FILE',
                    type=argparse.FileType('r'), help='Configuration file')
parser.add_argument('--output', '-o', metavar='FILENAME',
                    type=str, help='Specify GTFS output zip file')

# Refresh caching arguments
group = parser.add_mutually_exclusive_group()
group.add_argument('--refresh-routes', action="store_true",
                   help='Refresh OSM data for all routes')
group.add_argument('--refresh-stops', action="store_true",
                   help='Refresh OSM data for all stops')
group.add_argument('--refresh-osm', action="store_true",
                   help='Refresh all OSM data')
group.add_argument('--refresh-schedule-source', action="store_true",
                   help='Refresh data for time information')
group.add_argument('--refresh-all', action="store_true",
                   help='Refresh all OSM and time information data')
args = parser.parse_args()


def main():

    # Load, prepare and validate configuration
    config = Configuration(args)

    # Initiate OpenStreetMap helper containing data
    data = OsmConnector(config)

    # Refresh argument option calls
    if args.refresh_routes:
        data.get_routes(refresh=True)
    elif args.refresh_stops:
        data.get_stops(refresh=True)
    elif args.refresh_osm:
        data.get_routes(refresh=True)
        data.get_stops(refresh=True)
    elif args.refresh_schedule_source:
        config.get_schedule_source(refresh=True)
    elif args.refresh_all:
        data.get_routes(refresh=True)
        data.get_stops(refresh=True)
        config.get_schedule_source(refresh=True)

    # Define (transitfeed) object for GTFS creation
    feed = transitfeed.Schedule()

    # Initiate creators for GTFS components through an object factory
    factory = CreatorFactory(config)
    agency_creator = factory.get_agency_creator()
    feed_info_creator = factory.get_feed_info_creator()
    routes_creator = factory.get_routes_creator()
    stops_creator = factory.get_stops_creator()
    schedule_creator = factory.get_schedule_creator()
    trips_creator = factory.get_trips_creator()

    # Add data to feed
    agency_creator.add_agency_to_feed(feed)
    feed_info_creator.add_feed_info_to_feed(feed)
    stops_creator.add_stops_to_feed(feed, data)
    routes_creator.add_routes_to_feed(feed, data)
    schedule_creator.add_schedule_to_data(data)
    trips_creator.add_trips_to_feed(feed, data)

    # Validate GTFS
    feed.Validate(transitfeed.ProblemReporter())

    # Write GTFS
    feed.WriteGoogleTransitFeed(config.output)

    sys.exit()


if __name__ == "__main__":
    main()
