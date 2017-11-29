# coding=utf-8

import attr


@attr.s
class Line(object):
    """A general public transport service Line.

    It's a container of meta information and different Itinerary objects for
    variants of the same service line.

    In OpenStreetMap this is usually represented as "route_master" relation.
    In GTFS this is usually represented as "route"

    """
    osm_id = attr.ib()
    route_id = attr.ib()
    name = attr.ib()
    route_type = attr.ib()  # Required (Tram, Subway, Rail, Bus, ...)

    route_desc = attr.ib(default=None)
    route_url = attr.ib(default=None)
    route_color = attr.ib(default="FFFFFF")
    route_text_color = attr.ib(default="000000")
    osm_url = attr.ib(default="http://osm.org/relation/" + str(osm_id))
    frequency = attr.ib(default=None)

    # Related route variants
    _itineraries = attr.ib(default=attr.Factory(list))

    def add_itinerary(self, itinerary):

        if self.route_id.encode('utf-8') != itinerary.route_id.encode('utf-8'):
            raise ValueError('Itinerary route ID (' +
                             itinerary.route_id +
                             ') does not match Line route ID (' +
                             self.route_id + ')')
        self._itineraries.append(itinerary)

    def get_itineraries(self):
        return self._itineraries


@attr.s
class Itinerary(object):
    """A public transport service itinerary.

    It's a representation of a possible variant of a line, grouped together by
    a Line object.

    In OpenStreetMap this is usually represented as "route" relation.
    In GTFS this is not exlicitly presented but used as based to create "trips"

    """
    osm_id = attr.ib()
    route_id = attr.ib()
    name = attr.ib()
    fr = attr.ib()
    to = attr.ib()
    shape = attr.ib()
    stops = attr.ib()
    travel_time = attr.ib()

    route_url = attr.ib(default=None)
    wheelchair_accessible = attr.ib(default=0)
    bikes_allowed = attr.ib(default=0)
    osm_url = attr.ib(default="http://osm.org/relation/" + str(osm_id))

    # Useful information for further calculation
    duration = attr.ib(default=None)

    # All stop objects of itinerary
    _stop_objects = attr.ib(default=attr.Factory(list))

    def add_stop(self, stop):
        self._stop_objects.append(stop)

    def get_stop_by_position(self, pos):
        raise NotImplementedError("Should have implemented this")

    def get_stops(self):
        return self._stop_objects
