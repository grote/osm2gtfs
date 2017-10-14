# coding=utf-8

import importlib
from osm2gtfs.creators.agency_creator import AgencyCreator
from osm2gtfs.creators.feed_info_creator import FeedInfoCreator
from osm2gtfs.creators.routes_creator import RoutesCreator
from osm2gtfs.creators.stops_creator import StopsCreator
from osm2gtfs.creators.trips_creator import TripsCreator


class CreatorFactory(object):

    def __init__(self, config):
        self.config = config
        if 'selector' in config:
            self.selector = config['selector']
        else:
            self.selector = None

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        if self.selector is not None:
            rep += self.selector
        return rep

    def get_agency_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                ".creators." + selector + ".agency_creator_" + selector,
                package="osm2gtfs")
            agency_creator_override = getattr(
                module, "AgencyCreator" + selector.capitalize())
            print "Agency creator: " + selector.capitalize()
            return agency_creator_override(self.config)
        except ImportError:
            print "Agency creator: Default"
            return AgencyCreator(self.config)

    def get_feed_info_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                ".creators." + selector + ".feed_info_creator_" + selector,
                package="osm2gtfs")
            feed_info_creator_override = getattr(
                module, "FeedInfoCreator" + selector.capitalize())
            print "Feed info creator: " + selector.capitalize()
            return feed_info_creator_override(self.config)
        except ImportError:
            print "Feed info creator: Default"
            return FeedInfoCreator(self.config)

    def get_routes_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                ".creators." + selector + ".routes_creator_" + selector,
                package="osm2gtfs")
            routes_creator_override = getattr(
                module, "RoutesCreator" + selector.capitalize())
            print "Routes creator: " + selector.capitalize()
            return routes_creator_override(self.config)
        except ImportError:
            print "Routes creator: Default"
            return RoutesCreator(self.config)

    def get_stops_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                ".creators." + selector + ".stops_creator_" + selector,
                package="osm2gtfs")
            stops_creator_override = getattr(
                module, "StopsCreator" + selector.capitalize())
            print "Stops creator: " + selector.capitalize()
            return stops_creator_override(self.config)
        except ImportError:
            print "Stops creator: Default"
            return StopsCreator(self.config)

    def get_trips_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                ".creators." + selector + ".trips_creator_" + selector,
                package="osm2gtfs")
            trips_creator_override = getattr(
                module, "TripsCreator" + selector.capitalize())
            print "Trips creator: " + selector.capitalize()
            return trips_creator_override(self.config)
        except ImportError:
            print "Trips creator: Default"
            return TripsCreator(self.config)
