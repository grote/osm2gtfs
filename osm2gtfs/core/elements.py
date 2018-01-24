# coding=utf-8

import sys
import attr


@attr.s
class Element(object):
    """The basic data element.
    Contains the common attributes all other data classes share.

    """
    osm_id = attr.ib()
    osm_type = attr.ib()
    osm_url = attr.ib()

    tags = attr.ib()
    name = attr.ib()


@attr.s
class Line(Element):
    """A general public transport service Line.

    It's a container of meta information and different Itinerary objects for
    variants of the same service line.

    In OpenStreetMap this is usually represented as "route_master" relation.
    In GTFS this is usually represented as "route".

    """
    route_id = attr.ib()

    route_type = attr.ib(default=None)
    route_desc = attr.ib(default=None)
    route_color = attr.ib(default="#FFFFFF")
    route_text_color = attr.ib(default="#000000")

    # Related route variants
    _itineraries = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''
        Populates the object with information obtained from the tags
        '''
        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'colour' in self.tags:
            self.route_color = self.tags['colour']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'route_master' in self.tags:
            self.route_type = self.tags['route_master'].capitalize()
        else:
            sys.stderr.write(
                "Warning: Route master relation without a route_master tag:\n")
            sys.stderr.write(" " + self.osm_url + "\n")

            # Try to guess the type differently
            if 'route' in self.tags:
                self.route_type = self.tags['route'].capitalize()
            else:
                self.route_type = "Bus"

    def add_itinerary(self, itinerary):

        if self.route_id != itinerary.route_id:
            raise ValueError('Itinerary route ID (' +
                             itinerary.route_id +
                             ') does not match Line route ID (' +
                             self.route_id + ')')
        # pylint: disable=no-member
        self._itineraries.append(itinerary)

    def get_itineraries(self):
        return self._itineraries


@attr.s
class Itinerary(Element):
    """A public transport service itinerary.

    It's a representation of a possible variant of a line, grouped together by
    a Line object.

    In OpenStreetMap this is usually represented as "route" relation.
    In GTFS this is not exlicitly presented but used as base to create "trips"

    """
    route_id = attr.ib()
    shape = attr.ib()

    line = attr.ib(default=None)
    fr = attr.ib(default=None)
    to = attr.ib(default=None)
    duration = attr.ib(default=None)

    # All stop objects of itinerary
    stops = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''
        Populates the object with information obtained from the tags
        '''
        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'from' in self.tags:
            self.fr = self.tags['from']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'to' in self.tags:
            self.to = self.tags['to']

    def get_stops(self):
        return self.stops


@attr.s
class Station(Element):
    """A public transport stop of the type station.

    It's a representation of a possible group of stops.

    In OpenStreetMap this is usually represented as "stop_area" relation.
    In GTFS it is handled as a stop with a location_type=1. Regular Stops with
    location_type=0 might specify a station as parent_station.

    """
    lat = attr.ib()
    lon = attr.ib()

    stop_id = attr.ib(default="")
    location_type = attr.ib(default=1)

    # Stops forming part of this Station
    _members = attr.ib(default=attr.Factory(list))

    def set_members(self, members):
        self._members = members

    def get_members(self):
        return self._members

    def get_stop_id(self):
        return self.stop_id

    def set_stop_id(self, stop_id):
        self.stop_id = stop_id


@attr.s
class Stop(Element):
    """A public transport stop.

    In OpenStreetMap this is usually represented as an object of the role
    "plattform" in the route.

    """
    lat = attr.ib()
    lon = attr.ib()

    stop_id = attr.ib("")
    location_type = attr.ib(default=0)

    # The id of the Station this Stop might be part of.
    _parent_station = attr.ib(default=None)

    def set_parent_station(self, identifier, override=False):
        """
        Set the parent_station_id on the first time;
        Second attempts throw a warning
        """
        if self._parent_station is None or override is True:
            self._parent_station = identifier
        else:
            sys.stderr.write("Warning: Stop is part of two stop areas:\n")
            sys.stderr.write(
                "https://osm.org/" + self.osm_type + "/" + str(
                    self.osm_id) + "\n")

    def get_parent_station(self):
        return self._parent_station

    def get_stop_id(self):
        return self.stop_id

    def set_stop_id(self, stop_id):
        self.stop_id = stop_id
