# coding=utf-8

import sys
import overpy
from collections import OrderedDict
from core.cache import Cache
from core.osm_routes import Route, RouteMaster
from core.osm_stops import Stop


class OsmConnector(object):
    """The OsmConnector class retrieves information about transit networks from
    OpenStreetMap, caches it and serves it when needed to the osm2gtfs script

    """

    def __init__(self, config):
        """Contructor function

        This function gets called when OsmConnector object are created.

        Based on the configuration from the config file it prepares the bbox
        and tags that are used for querying OpenStreetMap.

        Further it initializes main storage dictionary variables for routes and
        stops, that are going to be shared and used by the ther components
        of the program.

        :param config: configuration information from the config file

        """
        self.config = config

        # bbox from config file for querying
        self.bbox = (str(config['query']['bbox']["s"]) + "," +
                     str(config['query']['bbox']["w"]) + "," +
                     str(config['query']['bbox']["n"]) + "," +
                     str(config['query']['bbox']["e"]))

        # tags from config file for querying
        self.tags = ''
        for key, value in config["query"].get("tags", {}).iteritems():
            self.tags += str('["' + key + '" = "' + value + '"]')
        if not self.tags:
            # fallback
            self.tags = '["public_transport:version" = "2"]'
            print("No tags found for querying from OpenStreetMap.")
            print("Using tag 'public_transport:version=2")

        # Selector
        if 'selector' in config:
            self.selector = config['selector']
        else:
            self.selector = 'no-selector'

        # Initiate containers for data
        self.routes = {}
        self.stops = {}

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
            rep += str(self.routes) + " | "
            rep += str(self.stops) + " | "
        return rep

    def get_routes(self, refresh=False):
        """The get_routes function returns the data of routes from
        OpenStreetMap converted into usable objects.

        Data about routes is getting obtained from OpenStreetMap through the
        Overpass API, based on the configuration from the config file.

        Then this data gets prepared by building up objects of RouteMaster and
        RouteVariant objects that are related to each other.

        It uses caching to leverage fast performance and spare the Overpass
        API. Special commands are used to refresh cached data.

        :param self: the own object including it's functions and variables
        :param refresh: A simple boolean indicating a data refresh or use of
            caching if possible.

        :return routes: A dictionary of RouteMaster objects with related
            RouteVariant objects constituting the tree of data.

        """
        # Preferably return cached data about routes
        if refresh is False:
            # Check if routes data is already built in this object
            if not self.routes:
                # If not, try to get routes data from file cache
                self.routes = Cache.read_data('routes-' + self.selector)
            # Return cached data if found
            if bool(self.routes):
                return self.routes

        # No cached data was found or refresh was forced
        print("Query and build fresh data for routes")

        # Obtain raw data about routes from OpenStreetMap
        result = self._query_routes()

        # Pre-sort relations by type
        route_masters = {}
        route_variants = {}
        for relation in result.relations:
            if relation.tags["type"] == "route_master":
                route_masters[relation.id] = relation
            else:
                route_variants[relation.id] = relation

        # Build routes from master relations
        for rmid, route_master in route_masters.iteritems():
            members = OrderedDict()

            # Build route variant members
            for member in route_master.members:

                if member.ref in route_variants:
                    rv = route_variants.pop(member.ref)
                    members[rv.id] = self._build_route_variant(rv, result)

                # Route master member was already used before or is not valid
                else:
                    rv = result.get_relations(member.ref)
                    if bool(rv):
                        rv = rv.pop()
                        sys.stderr.write("Route variant was assigned again:\n")
                        sys.stderr.write(
                            "http://osm.org/relation/" + str(rv.id) + "\n")
                        members[rv.id] = self._build_route_variant(rv, result)
                    else:
                        sys.stderr.write(
                            "Member relation is not a valid route variant:\n")
                        sys.stderr.write("http://osm.org/relation/"
                                         + str(member.ref) + "\n")

            rm = self._build_route_master(route_master, members)

            # Make sure ref number is not already taken
            if rm.ref in self.routes:
                sys.stderr.write("'Ref' of route_master already taken\n")
                sys.stderr.write(
                    "http://osm.org/relation/" + str(route_master.id) + "\n")
                sys.stderr.write("Skipped. Please fix in OpenStreetMap\n")

            else:
                self.routes[rm.ref] = rm

        # Build routes from variants (missing master relation)
        for rvid, route_variant in route_variants.iteritems():
            sys.stderr.write("Route (variant) without masters\n")
            rv = self._build_route_variant(route_variant, result)
            # Make sure ref number is not already taken
            if rv.ref in self.routes:
                sys.stderr.write("Route (variant) with existing 'Ref'\n")
                sys.stderr.write(
                    "http://osm.org/relation/" + str(route_variant.id) + "\n")
                sys.stderr.write("Skipped. Please fix in OpenStreetMap\n")
            else:
                self.routes[rv.ref] = rv

        # Cache and return whole data set
        Cache.write_data('routes-' + self.selector, self.routes)
        return self.routes

    def get_stops(self, refresh=False):
        """The get_stops function returns the data of stops from
        OpenStreetMap converted into usable objects.

        Data about stops is getting obtained from OpenStreetMap through the
        Overpass API, based on the configuration from the config file.

        Then this data gets prepared by building up objects of the class Stops.

        It uses caching to leverage fast performance and spare the Overpass
        API. Special commands are used to refresh cached data.

        :param self: the own object including it's functions and variables
        :param refresh: A simple boolean indicating a data refresh or use of
            caching if possible.

        :return stops: A dictionary of Stops constituting the obtained data.

        """

        # Preferably return cached data about stops
        if refresh is False:
            # Check if stops data is already built in this object
            if not self.stops:
                # If not, try to get stops data from file cache
                self.stops = Cache.read_data('stops-' + self.selector)
            # Return cached data if found
            if bool(self.stops):
                return self.stops

        # No cached data was found or refresh was forced
        print("Query and build fresh data for stops")

        # Obtain raw data about routes from OpenStreetMap
        result = self._query_stops()

        # Build stops from ways (polygons)
        for stop in result.ways:
            if Stop.is_valid_stop_candidate(stop):
                self.stops["way/" + str(stop.id)
                           ] = self._build_stop(stop, "way")

        # Build stops from nodes
        for stop in result.nodes:
            if Stop.is_valid_stop_candidate(stop):
                self.stops["node/" + str(stop.id)
                           ] = self._build_stop(stop, "node")

        # Cache and return whole data set
        Cache.write_data('stops-' + self.selector, self.stops)
        return self.stops

    def _build_route_master(self, route_master, members):
        """Helper function to build a RouteMaster object

        Returns a initiated RouteMaster object from raw data

        """
        if 'ref' in route_master.tags:
            ref = route_master.tags['ref']
        else:
            sys.stderr.write(
                "RouteMaster without 'ref'. Please fix in OpenStreetMap\n")
            sys.stderr.write(
                "http://osm.org/relation/" + str(route_master.id) + "\n")

            # Check if a ref can be taken from one of the members
            ref = False
            for member in list(members.values()):
                if not ref and member.ref:
                    ref = member.ref
                    sys.stderr.write(
                        "Using 'ref' from member variant instead\n")
                    sys.stderr.write(
                        "http://osm.org/relation/" + str(member.id) + "\n")

            # Ignore whole Line if no reference number could be obtained
            if not ref:
                sys.stderr.write(
                    "No 'ref' could be obtained from members. Skipping.\n")
                return

        name = route_master.tags['name']
        rm = RouteMaster(route_master.id, ref, name, members)
        print(rm)
        return rm

    def _build_route_variant(self, route_variant, query_result_set, rm=None):
        """Helper function to build a RouteVariant object

        Returns a initiated RouteVariant object from raw data

        """
        if 'ref' in route_variant.tags:
            ref = route_variant.tags['ref']
        else:
            sys.stderr.write(
                "RouteVariant without 'ref': " + str(route_variant.id) + "\n")
            sys.stderr.write(
                "http://osm.org/relation/" + str(route_variant.id) + "\n")
            return

        if 'from' in route_variant.tags:
            fr = route_variant.tags['from']
        else:
            fr = None

        if 'to' in route_variant.tags:
            to = route_variant.tags['to']
        else:
            to = None

        if 'name' in route_variant.tags:
            name = route_variant.tags['name']
        else:
            name = None

        stops = []

        # Add ids for stops of this route variant
        for stop_candidate in route_variant.members:
            if stop_candidate.role == "platform":

                if isinstance(stop_candidate, overpy.RelationNode):
                    otype = "node"

                elif isinstance(stop_candidate, overpy.RelationWay):
                    otype = "way"

                else:
                    raise RuntimeError("Unknown type: " + str(stop_candidate))

                stops.append(otype + "/" + str(stop_candidate.ref))

        rv = Route(route_variant.id, fr, to, stops, rm, ref, name)
        rv.add_shape(route_variant, query_result_set)
        print(rv)
        return rv

    def _build_stop(self, stop, stop_type):
        """Helper function to build a Stop object

        Returns a initiated Stop object from raw data

        """

        # Make sure name is not empty
        if 'name' not in stop.tags:
            stop.tags['name'] = Stop.NO_NAME

        # Ways don't have coordinates and they have to be calculated
        if stop_type == "way":
            (stop.lat, stop.lon) = Stop.get_center_of_nodes(stop.get_nodes())

        s = Stop(stop.id, "node", stop.tags['name'], stop.lat, stop.lon)
        return s

    def _query_routes(self):
        """Helper function to query OpenStreetMap routes

        Returns raw data on routes from OpenStreetMap

        """
        # Query relations of route variants, their masters and geometry
        api = overpy.Overpass()
        query_str = """(
            /* Obtain route variants based on tags and bounding box */
            relation%s(%s)->.routes;

            /*  Query for related route masters */
            relation[type=route_master](br.routes)->.masters;

            /* Query for routes' geometry (ways and it's nodes) */
            way(r.routes);
            node(w);

            /* Select all result sets  */
            ( .routes;.masters;._; );

            /* Return tags for elements and roles for relation members. */
            );out body;""" % (self.tags, self.bbox)
        return api.query(query_str)

    def _query_stops(self):
        """Helper function to query OpenStreetMap stops

        Returns raw data on stops from OpenStreetMap

        """
        # Query stops with platform role from selected relations
        api = overpy.Overpass()
        query_str = """(
            /* Obtain route variants based on tags and bounding box */
            relation%s(%s);

            /*  Query for relation elements with role platform */
            node(r:"platform")->.nodes;
            way(r:"platform");
            node(w);

            /* Select all result sets  */
            ( .nodes;._; );

            /* Return tags for elements */
            );out body;""" % (self.tags, self.bbox)
        return api.query(query_str)
