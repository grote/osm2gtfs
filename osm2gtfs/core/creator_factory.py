# coding=utf-8

import importlib
import logging
from osm2gtfs.creators.agency_creator import AgencyCreator
from osm2gtfs.creators.feed_info_creator import FeedInfoCreator
from osm2gtfs.creators.routes_creator import RoutesCreator
from osm2gtfs.creators.stops_creator import StopsCreator
from osm2gtfs.creators.schedule_creator import ScheduleCreator
from osm2gtfs.creators.trips_creator import TripsCreator


class CreatorFactory(object):

    def __init__(self, config):
        self.config = config
        if 'selector' in self.config.data:
            self.selector = self.config.data['selector']
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
                module, "AgencyCreator" + self._generate_class_name(selector))
            logging.info("Agency creator: %s", selector)
            return agency_creator_override(self.config)
        except ImportError:
            logging.info("Agency creator: Default")
            return AgencyCreator(self.config)

    def get_feed_info_creator(self):
        selector = self.selector

        try:
            module = importlib.import_module(
                ".creators." + selector + ".feed_info_creator_" + selector,
                package="osm2gtfs")
            feed_info_creator_override = getattr(
                module, "FeedInfoCreator" + self._generate_class_name(selector))
            logging.info("Feed info creator: %s", selector)
            return feed_info_creator_override(self.config)
        except ImportError:
            logging.info("Feed info creator: Default")
            return FeedInfoCreator(self.config)

    def get_routes_creator(self):
        selector = self.selector

        try:
            module = importlib.import_module(
                ".creators." + selector + ".routes_creator_" + selector,
                package="osm2gtfs")
            routes_creator_override = getattr(
                module, "RoutesCreator" + self._generate_class_name(selector))
            logging.info("Routes creator: %s", selector)
            return routes_creator_override(self.config)
        except ImportError:
            logging.info("Routes creator: Default")
            return RoutesCreator(self.config)

    def get_stops_creator(self):
        selector = self.selector

        try:
            module = importlib.import_module(
                ".creators." + selector + ".stops_creator_" + selector,
                package="osm2gtfs")
            stops_creator_override = getattr(
                module, "StopsCreator" + self._generate_class_name(selector))
            logging.info("Stops creator: %s", selector)
            return stops_creator_override(self.config)
        except ImportError:
            logging.info("Stops creator: Default")
            return StopsCreator(self.config)

    def get_schedule_creator(self):
        selector = self.selector

        try:
            module = importlib.import_module(
                ".creators." + selector + ".schedule_creator_" + selector,
                package="osm2gtfs")
            schedule_creator_override = getattr(
                module, "ScheduleCreator" + self._generate_class_name(selector))
            logging.info("Schedule creator: %s", selector)
            return schedule_creator_override(self.config)
        except ImportError:
            logging.info("Schedule creator: Default")
            return ScheduleCreator(self.config)

    def get_trips_creator(self):
        selector = self.selector

        try:
            module = importlib.import_module(
                ".creators." + selector + ".trips_creator_" + selector,
                package="osm2gtfs")
            trips_creator_override = getattr(
                module, "TripsCreator" + self._generate_class_name(selector))
            logging.info("Trips creator: %s", selector)
            return trips_creator_override(self.config)
        except ImportError:
            logging.info("Trips creator: Default")
            return TripsCreator(self.config)

    @staticmethod
    def _generate_class_name(selector):
        """
        Converts the underscore selector into class names sticking to Python's
        naming convention.
        """
        if "_" in selector:
            split_selector = selector.split("_")
            class_name = str()
            for part in split_selector:
                class_name += part.capitalize()
        else:
            class_name = selector.capitalize()
        return class_name
