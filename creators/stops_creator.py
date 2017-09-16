# coding=utf-8

from core.osm_routes import Route, RouteMaster
from core.osm_stops import Stop, StopArea


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

    def add_stop(this, schedule, stop, parent_station=None, is_station=False):
            # Add stop to GTFS object
            stop_obj = schedule.AddStop(
                lat=float(stop.lat),
                lng=float(stop.lon),
                name=stop.name,
                stop_id=str(stop.id)
            )

            if is_station:
                stop_obj.location_type = "1"
            else:
                stop_obj.location_type = ""

            if parent_station is None:
                stop_obj.parent_station = ""
            else:
                stop_obj.parent_station = parent_station.stop_id

            return stop_obj

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
        if isinstance(route, Route):
            i = 0
            for stop in route.stops:
                # Replace stop id with Stop objects
                # TODO: Remove here and use references in TripsCreatorFenix
                route.stops[i] = self._get_stop(stop, stops)
                i += 1

        elif isinstance(route, RouteMaster):
            for route_variant_ref, route_variant in route.routes.iteritems():
                self._fill_stops(stops, route_variant)

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
            raise RuntimeError("Unknown stop: " + str(stop))
