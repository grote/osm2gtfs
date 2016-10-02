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
            module = importlib.import_module(
                "creators." + self.selector + ".AgencyCreator" + self.selector)
            agency_creator_override = getattr(
                module, "AgencyCreator" + self.selector)
            print "Agency creator: " + self.selector
            return agency_creator_override(self.config)
        except ImportError:
            print "Agency creator: Default"
            return AgencyCreator(self.config)

    def get_feed_info_creator(self):
        selector = self.selector
        try:
            module = importlib.import_module(
                "creators." + selector + ".FeedInfoCreator" + selector)
            feed_info_creator_override = getattr(
                module, "FeedInfoCreator" + selector)
            print "Feed info creator: " + selector
            return feed_info_creator_override(self.config)
        except ImportError:
            print "Feed info creator: Default"
            return FeedInfoCreator(self.config)

    def get_routes_creator(self):
        try:
            module = importlib.import_module(
                "creators." + self.selector + ".RoutesCreator" + self.selector)
            routes_creator_override = getattr(
                module, "RoutesCreator" + self.selector)
            print "Routes creator: " + self.selector
            return routes_creator_override(self.config)
        except ImportError:
            print "Routes creator: Default"
            return RoutesCreator(self.config)

    def get_stops_creator(self):
        try:
            module = importlib.import_module(
                "creators." + self.selector + ".StopsCreator" + self.selector)
            stops_creator_override = getattr(
                module, "StopsCreator" + self.selector)
            print "Stops creator: " + self.selector
            return stops_creator_override(self.config)
        except ImportError:
            print "Stops creator: Default"
            return StopsCreator(self.config)

    def get_trips_creator(self):
        try:
            module = importlib.import_module(
                "creators." + self.selector + ".TripsCreator" + self.selector)
            trips_creator_override = getattr(
                module, "TripsCreator" + self.selector)
            print "Trips creator: " + self.selector
            return trips_creator_override(self.config)
        except ImportError:
            print "Trips creator: Default"
            return TripsCreator(self.config)
