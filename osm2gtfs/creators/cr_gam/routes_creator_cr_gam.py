# coding=utf-8

import sys
from osm2gtfs.core.elements import Line, Itinerary, Station, Stop
from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorCrGam(RoutesCreator):

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

        # debug
        # print("DEBUG: creando itinerarios a partir de", str(len(lines)),
        #      "lineas")

        # Loop through all lines (master_routes)
        for line_ref, line in sorted(routes.iteritems()):
            route = feed.AddRoute(
                short_name=line.route_id.encode('utf-8'),
                long_name=line.name,
                # TODO: infer transitfeed "route type" from OSM data
                route_type="Tram",
                route_id=line_ref)

            # AddRoute method add defaut agency as default
            route.agency_id = feed.GetDefaultAgency().agency_id

            route.route_desc = "Test line"

            # TODO: get route_url from OSM or other source.
            # url = "http://www.incofer.go.cr/tren-urbano-alajuela-rio-segundo"

            # line.route_url = url
            route.route_color = "ff0000"
            route.route_text_color = "ffffff"

            # debug
            # print("información de la linea:", line.name, "agregada.")
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
