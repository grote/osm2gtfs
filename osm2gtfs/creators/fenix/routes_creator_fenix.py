# coding=utf-8

import sys
from osm2gtfs.core.routes import Itinerary, Line
from osm2gtfs.core.stops import Stop, Station
from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorFenix(RoutesCreator):

    def add_routes_to_feed(self, feed, data):
        '''
        Override routes to feed method, to prepare routes with stops
        for the handling in the custom trips creators.
        '''
        routes = data.routes
        stops = data.stops

        # Loop through routes
        for ref, route in routes.iteritems():
            # Replace stop ids with Stop objects
            self._fill_stops(stops, route)

        data.routes = routes
        return

    def _fill_stops(self, stops, route):
        """
        Fill a route object with stop objects for of linked stop ids
        """
        if isinstance(route, Itinerary):
            i = 0
            for stop in route.stops:
                # Replace stop id with Stop objects
                route.stops[i] = self._look_up_stop(stop, stops)
                i += 1

        elif isinstance(route, Line):
            itineraries = route.get_itineraries()
            for itinerary in itineraries:
                self._fill_stops(stops, itinerary)
        else:
            sys.stderr.write("Unknown route: " + str(route) + "\n")

    def _look_up_stop(self, stop_id, stops):
        for ref, elem in stops.iteritems():
            if type(elem) is Stop:
                if ref == stop_id:
                    return elem
            elif type(elem) is Station:
                if stop_id in elem.stop_members:
                    return elem.stop_members[stop_id]
            else:
                sys.stderr.write("Unknown stop: " + str(stop_id) + "\n")
