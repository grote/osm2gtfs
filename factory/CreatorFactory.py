# coding=utf-8

import sys
import importlib
import transitfeed
from creators_default.AgencyCreator import AgencyCreator
from creators_default.FeedInfoCreator import FeedInfoCreator
from creators_default.RoutesCreator import RoutesCreator
from creators_default.StopsCreator import StopsCreator
from creators_default.TripsCreator import TripsCreator

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
            AgencyCreatorOverride = getattr(importlib.import_module("creators_custom.AgencyCreator" + self.selector), "AgencyCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of the agency (AgencyCreator" + self.selector + ")"
            return AgencyCreatorOverride(self.config)
        except ImportError:
            print "Using default implementation for creation of the agency"
            return AgencyCreator(self.config)

    def get_feed_info_creator(self):
        try:
            FeedInfoCreatorOverride = getattr(importlib.import_module("creators_custom.FeedInfoCreator" + self.selector), "FeedInfoCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of the feed info (FeedInfoCreator" + self.selector + ")"
            return FeedInfoCreatorOverride(self.config)
        except ImportError:
            print "Using default implementation for creation of the the feed info"
            return FeedInfoCreator(self.config)

    def get_routes_creator(self):
        try:
            RoutesCreatorOverride = getattr(importlib.import_module("creators_custom.RoutesCreator" + self.selector), "RoutesCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of routes (RoutesCreator" + self.selector + ")"
            return RoutesCreatorOverride(self.config)
        except ImportError:
            print "Using default implementation for creation of routes"
            return RoutesCreator(self.config)

    def get_stops_creator(self):
        try:
            StopsCreatorrOverride = getattr(importlib.import_module("creators_custom.StopsCreator" + self.selector), "StopsCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of stops (StopsCreator" + self.selector + ")"
            return StopsCreatorrOverride(self.config)
        except ImportError:
            print "Using default implementation for creation of stops"
            return StopsCreator(self.config)

    def get_trips_creator(self):
        try:
            TripsCreatorOverride = getattr(importlib.import_module("creators_custom.TripsCreator" + self.selector), "TripsCreator" + self.selector)
            print "Using " + self.selector + " implementation for creation of trips (TripsCreator" + self.selector + ")"
            return TripsCreatorOverride(self.config)
        except ImportError:
            print "Using default implementation for creation of trips"
            return TripsCreator(self.config)
