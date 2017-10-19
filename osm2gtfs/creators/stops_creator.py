# coding=utf-8

import transitfeed

from osm2gtfs.core.routes import Itinerary, Line
from osm2gtfs.core.stops import Stop, StopArea


class StopsCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_stops_to_schedule(self, schedule, data):

        # Get stops information
        stops = data.get_stops()

        # add all stops to GTFS
        for elem in stops.values():
            if type(elem) is StopArea:
                if len(elem.stop_members) > 1:
                    parent_station = self.add_stop(schedule, elem, None, True)
                    for stop in elem.stop_members.values():
                        self.add_stop(schedule, stop, parent_station)
                else:
                    stop = elem.stop_members.values()[0]
                    self.add_stop(schedule, stop)
            else:
                self.add_stop(schedule, elem)

        # Add loose stop objects to route objects
        self.add_stops_to_routes(data)

    def add_stop(self, schedule, stop, parent_station=None, is_station=False):

        stop_dict = {"stop_lat": float(stop.lat),
                     "stop_lon": float(stop.lon),
                     "stop_name": stop.name}

        if is_station:
            stop_dict["stop_id"] = "SA" + str(stop.osm_id)
            stop_dict["location_type"] = "1"
        else:
            stop_dict["stop_id"] = str(stop.osm_id)
            stop_dict["location_type"] = ""

        if parent_station is None:
            stop_dict["parent_station"] = ""
        else:
            stop_dict["parent_station"] = parent_station.stop_id

        # Add stop to GTFS object
        stop = transitfeed.Stop(field_dict=stop_dict)
        schedule.AddStopObject(stop)
        return stop

    def add_stops_to_routes(self, data):

        routes = data.routes
        stops = data.stops

        # Loop through routes
        for ref, route in routes.iteritems():
            # Replace stop ids with Stop objects
            self._fill_stops(stops, route)

        data.routes = routes
        return

    def _fill_stops(self, stops, route):
        """Fill a route object with stop objects for of linked stop ids

        """
        if isinstance(route, Itinerary):
            i = 0
            for stop in route.stops:
                # Replace stop id with Stop objects
                # TODO: Remove here and use references in TripsCreatorFenix
                route.stops[i] = self._get_stop(stop, stops)
                i += 1

        elif isinstance(route, Line):
            itineraries = route.get_itineraries()
            for itinerary_ref, itinerary in itineraries:
                self._fill_stops(stops, itinerary)

        else:
            raise RuntimeError("Unknown Route: " + str(route))

    def _get_stop(self, stop_id, stops):
        for ref, elem in stops.iteritems():
            if type(elem) is Stop:
                if ref == stop_id:
                    return elem
            elif type(elem) is StopArea:
                if stop_id in elem.stop_members:
                    return elem.stop_members[stop_id]
            else:
                raise RuntimeError("Unknown stop: " + str(stop_id))
