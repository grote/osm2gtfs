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
    tags = attr.ib()

    name = attr.ib(default=None)
    route_type = attr.ib(default=None)  # Required (Tram, Subway, Bus, ...)
    route_desc = attr.ib(default=None)
    route_url = attr.ib(default=None)
    route_color = attr.ib(default="FFFFFF")
    route_text_color = attr.ib(default="000000")
    osm_url = attr.ib(default="http://osm.org/relation/" + str(osm_id))

    # Related route variants
    _itineraries = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''
        Populates the object with information obtained from the tags
        '''
        from osm2gtfs.core.osm_connector import OsmConnector
        self.name = self.tags['name']

        if "colour" in self.tags:
            self.route_color = OsmConnector.get_hex_code_for_color(
                self.tags['colour'])

        text_color = OsmConnector.get_complementary_color(self.route_color)
        if "text_colour" in self.tags:
            self.route_text_color = OsmConnector.get_hex_code_for_color(
                self.tags['text_colour'])

        if 'self' in self.tags:
            # TODO: Get the type from itineraries/routes or config file
            route_type = self.tags['self'].capitalize()

        # If there was no self present we have a route relation here
        elif 'route' in self.tags:
            route_type = self.tags['route'].capitalize()

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
    stops = attr.ib()
    shape = attr.ib()
    tags = attr.ib()

    name = attr.ib(default=None)
    fr = attr.ib(default=None)
    to = attr.ib(default=None)
    duration = attr.ib(default=None)
    osm_url = attr.ib(default="http://osm.org/relation/" + str(osm_id))

    # All stop objects of itinerary
    _stop_objects = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''
        Populates the object with information obtained from the tags
        '''
        if 'from' in self.tags:
            self.fr = self.tags['from']

        if 'to' in self.tags:
            self.to = self.tags['to']

        if 'name' in self.tags:
            self.name = self.tags['name']

        if 'duration' in self.tags:
            self.name = self.tags['duration']

    def add_stop(self, stop):
        self._stop_objects.append(stop)

    def get_stop_by_position(self, pos):
        raise NotImplementedError("Should have implemented this")

    def get_stops(self):
        return self._stop_objects
