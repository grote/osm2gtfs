# coding=utf-8

import overpy
import sys

from transitfeed import util
from creators.stops_creator import StopsCreator
from core.cache import Cache
from core.osm_routes import Route, RouteMaster
from core.osm_stops import Stop


class StopsCreatorFenix(StopsCreator):

    def add_stops_to_schedule(self, schedule, data):

        # Get stops information
        stops = data.get_stops()

        # add all stops to GTFS
        for stop in stops.values():

            # If there is no name, query one intelligently from OSM
            if stop.name == Stop.NO_NAME:
                self.find_best_name_for_unnamed_stop(stop)
                print stop

                # Cache stops with newly created stop names
                Cache.write_data('stops-' + data.selector, stops)

            # Add stop to GTFS object
            schedule.AddStop(
                lat=float(stop.lat),
                lng=float(stop.lon),
                name=stop.name,
                stop_id=str(stop.id)
            )

        # Add loose stop objects to route objects
        self.add_stops_to_routes(data)

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
                if stop in stops:
                    # Replace stop id with Stop objects
                    # TODO: Remove here and use references in TripsCreatorFenix
                    route.stops[i] = stops[stop]
                else:
                    raise RuntimeError("Unknown stop: " + str(stop))
                i += 1

        elif isinstance(route, RouteMaster):
            for route_variant_ref, route_variant in route.routes.iteritems():
                self._fill_stops(stops, route_variant)

        else:
            raise RuntimeError("Unknown Route: " + str(route))

    def find_best_name_for_unnamed_stop(self, stop):
        """Define name for stop without explicit name based on sourroundings

        """
        api = overpy.Overpass()

        result = api.query("""
        <osm-script>
          <query type="way">
            <around lat="%s" lon="%s" radius="50.0"/>
            <has-kv k="name" />
            <has-kv modv="not" k="highway" v="trunk"/>
            <has-kv modv="not" k="highway" v="primary"/>
            <has-kv modv="not" k="highway" v="secondary"/>
            <has-kv modv="not" k="amenity" v="bus_station"/>
          </query>
          <print order="quadtile"/>
          <query type="node">
            <around lat="%s" lon="%s" radius="50.0"/>
            <has-kv k="name"/>
            <has-kv modv="not" k="highway" v="bus_stop"/>
          </query>
          <print order="quadtile"/>
        </osm-script>
        """ % (stop.lat, stop.lon, stop.lat, stop.lon))

        candidates = []

        # get all node candidates
        for node in result.get_nodes():
            if 'name' in node.tags and node.tags["name"] is not None:
                candidates.append(node)

        # get way node candidates
        for way in result.get_ways():
            if 'name' in way.tags and way.tags["name"] is not None:
                candidates.append(way)

        # leave if no candidates
        if len(candidates) == 0:
            # give stop a different name, so we won't search again without
            # refreshing data
            stop.name = "Ponto sem nome"
            return

        # find closest candidate
        winner = None
        winner_distance = sys.maxint
        for candidate in candidates:
            if isinstance(candidate, overpy.Way):
                lat, lon = Stop.get_center_of_nodes(
                    candidate.get_nodes(resolve_missing=True))
                distance = util.ApproximateDistance(
                    lat,
                    lon,
                    stop.lat,
                    stop.lon
                )
            else:
                distance = util.ApproximateDistance(
                    candidate.lat,
                    candidate.lon,
                    stop.lat,
                    stop.lon
                )
            if distance < winner_distance:
                winner = candidate
                winner_distance = distance

        # take name from winner
        stop.name = winner.tags["name"].encode('utf-8')
