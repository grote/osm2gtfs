# coding=utf-8

import logging

from osm2gtfs.core.elements import Line, Itinerary, Station, Stop
from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorBrFlorianopolis(RoutesCreator):

    def add_routes_to_feed(self, feed, data):
        '''
        Override routes to feed method, to prepare routes with stops
        for the handling in the custom trips creators.
        '''
        routes = data.get_routes()
        stops = data.get_stops()

        # Loop through routes
        for ref, route in routes.iteritems():
            # Replace stop ids with Stop objects
            self._fill_stops(stops['regular'], route)
        return

    def _fill_stops(self, stops, route):
        """
        Fill a route object with stop objects for of linked stop ids
        """
        if isinstance(route, Itinerary):
            i = 0
            for stop in route.stops:
                # Replace stop id with Stop objects
                looked_up_stop = self._look_up_stop(stop, stops)
                if looked_up_stop is None:
                    logging.error("Missing stop for route %s: https://osm.org/%s",
                                  route.tags['ref'], route.stops[i])
                else:
                    route.stops[i] = looked_up_stop
                i += 1

        elif isinstance(route, Line):
            itineraries = route.get_itineraries()
            for itinerary in itineraries:
                self._fill_stops(stops, itinerary)
        else:
            logging.error("Unknown route: %s", str(route))

    def _look_up_stop(self, stop_id, stops):
        for ref, elem in stops.iteritems():
            if type(elem) is Stop:
                if ref == stop_id:
                    return elem
            elif type(elem) is Station:
                if stop_id in elem.stop_members:
                    return elem.stop_members[stop_id]
            else:
                logging.error("Unknown stop: %s", str(stop_id))
                return None
        return None
