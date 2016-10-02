# coding=utf-8

import importlib
from creators.AgencyCreator import AgencyCreator
from creators.FeedInfoCreator import FeedInfoCreator
from creators.RoutesCreator import RoutesCreator
from creators.StopsCreator import StopsCreator
from creators.TripsCreator import TripsCreator


class CreatorFactory(object):

    def __init__(self, config):
        self.config = config
        if 'selector' in config:
            self.selector = config['selector'].capitalize()
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
        try:
            agency_creator_override = getattr(importlib.import_module("creators." + self.selector + ".AgencyCreator" + self.selector), "AgencyCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of the agency (AgencyCreator" + self.selector + ")"
            return agency_creator_override(self.config)
        except ImportError:
            print "Using default implementation for creation of the agency"
            return AgencyCreator(self.config)

    def get_feed_info_creator(self):
        try:
            feed_info_creator_override = getattr(importlib.import_module("creators." + self.selector + ".FeedInfoCreator" + self.selector), "FeedInfoCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of the feed info (FeedInfoCreator" + self.selector + ")"
            return feed_info_creator_override(self.config)
        except ImportError:
            print "Using default implementation for creation of the feed info"
            return FeedInfoCreator(self.config)

    def get_routes_creator(self):
        try:
            routes_creator_override = getattr(importlib.import_module("creators." + self.selector + ".RoutesCreator" + self.selector), "RoutesCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of routes (RoutesCreator" + self.selector + ")"
            return routes_creator_override(self.config)
        except ImportError:
            print "Using default implementation for creation of routes"
            return RoutesCreator(self.config)

    def get_stops_creator(self):
        try:
            stops_creator_override = getattr(importlib.import_module("creators." + self.selector + ".StopsCreator" + self.selector), "StopsCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of stops (StopsCreator" + self.selector + ")"
            return stops_creator_override(self.config)
        except ImportError:
            print "Using default implementation for creation of stops"
            return StopsCreator(self.config)

    def get_trips_creator(self):
        try:
            trips_creator_override = getattr(importlib.import_module("creators." + self.selector + ".TripsCreator" + self.selector), "TripsCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of trips (TripsCreator" + self.selector + ")"
            return trips_creator_override(self.config)
        except ImportError:
            print "Using default implementation for creation of trips"
            return TripsCreator(self.config)
