# coding=utf-8

import attr


@attr.s
class Line(object):
    """A general public transport service Line.

    It's a container of meta information and different Itinerary objects for
    variants of the same service line.

    In OpenStreetMap this is usually represented as "route_master" relation.
    In GTFS this is usually represented as "route".

    """
    osm_id = attr.ib()
    route_id = attr.ib()
    tags = attr.ib()

    name = attr.ib(default=None)
    route_type = attr.ib(default=None)
    route_desc = attr.ib(default=None)
    route_color = attr.ib(default="#FFFFFF")
    route_text_color = attr.ib(default="#000000")
    osm_url = attr.ib(default=None)

    # Related route variants
    _itineraries = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''Populates the object with information obtained from the tags

        '''
        from osm2gtfs.core.helper import Helper

        # Disabling some pylint errors as pylint currently doesn't support any
        # custom decorators or descriptors
        # https://github.com/PyCQA/pylint/issues/1694

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        self.name = self.tags['name']
        self.osm_url = "https://osm.org/relation/" + str(self.osm_id)

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'colour' in self.tags:
            self.route_color = self.tags['colour']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'ref:colour_tx' in self.tags:
            self.route_text_color = self.tags['ref:colour_tx']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'route_master' in self.tags:
            self.route_type = self.tags['route_master'].capitalize()
        elif 'route' in self.tags:
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
class Itinerary(object):
    """A public transport service itinerary.

    It's a representation of a possible variant of a line, grouped together by
    a Line object.

    In OpenStreetMap this is usually represented as "route" relation.
    In GTFS this is not exlicitly presented but used as based to create "trips"

    """
    osm_id = attr.ib()
    route_id = attr.ib()
    shape = attr.ib()
    tags = attr.ib()

    name = attr.ib(default=None)
    line = attr.ib(default=None)
    osm_url = attr.ib(default=None)
    fr = attr.ib(default=None)
    to = attr.ib(default=None)
    duration = attr.ib(default=None)

    # All stop objects of itinerary
    stops = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''
        Populates the object with information obtained from the tags
        '''

        self.osm_url = "https://osm.org/relation/" + str(self.osm_id)

        # Disabling some pylint errors as pylint currently doesn't support any
        # custom decorators or descriptors
        # https://github.com/PyCQA/pylint/issues/1694

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'from' in self.tags:
            self.fr = self.tags['from']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'to' in self.tags:
            self.to = self.tags['to']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'name' in self.tags:
            self.name = self.tags['name']

        # pylint: disable=unsupported-membership-test,unsubscriptable-object
        if 'duration' in self.tags:
            self.duration = self.tags['duration']

    def add_stop(self, stop):
        # pylint: disable=no-member
        self.stops.append(stop)

    def get_stops(self):
        return self.stops
