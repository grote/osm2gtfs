# coding=utf-8

import logging
import sys
from collections import OrderedDict
import overpy
import webcolors
from transitfeed import util
from osm2gtfs.core.cache import Cache
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line, Itinerary, Station, Stop


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

        :param config: configuration object including data from config file

        """
        self.config = config.data

        # bbox from config file for querying
        self.bbox = (str(self.config['query']['bbox']["s"]) + "," +
                     str(self.config['query']['bbox']["w"]) + "," +
                     str(self.config['query']['bbox']["n"]) + "," +
                     str(self.config['query']['bbox']["e"]))

        # tags from config file for querying
        self.tags = ''
        for key, value in sorted(self.config["query"].get("tags", {}).items()):
            if isinstance(value, list):
                value = '^' + '$|^'.join(value) + '$'
                self.tags += "['{}' ~ '{}']".format(key, value)
            else:
                self.tags += "['{}' = '{}']".format(key, value)
        if not self.tags:
            # fallback
            self.tags = '["public_transport:version" = "2"]'
            logging.info("No tags found for querying from OpenStreetMap.")
            logging.info("Using tag 'public_transport:version=2'")

        # Define name for stops without one
        self.stop_no_name = "No name"
        if "stops" in self.config and "name_without" in self.config["stops"]:
            self.stop_no_name = self.config["stops"]["name_without"]

        # Check if auto stop name logic should be used
        self.auto_stop_names = False
        if 'stops' in self.config and 'name_auto' in self.config['stops']:
            if self.config['stops']['name_auto'] == "yes":
                self.auto_stop_names = True

        # Selector
        if 'selector' in self.config:
            self.selector = self.config['selector']
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

        Then this data gets prepared by building up objects of Line and
        Itinerary objects that are related to each other.

        It uses caching to leverage fast performance and spare the Overpass
        API. Special commands are used to refresh cached data.

        :param self: the own object including it's functions and variables
        :param refresh: A simple boolean indicating a data refresh or use of
            caching if possible.

        :return routes: A dictionary of Line objects with related
            Itinerary objects constituting the tree of data.

        """
        # Preferably return cached data about routes
        if refresh is False:
            # Check if routes data is already built in this object
            if not self.routes:
                # If not, try to get routes data from file cache
                self.routes = Cache.read_data(self.selector + '-routes')
            # Return cached data if found
            if bool(self.routes):
                return self.routes

        # No cached data was found or refresh was forced
        logging.info("Query and build fresh data for routes")

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
        for rmid, route_master in sorted(route_masters.items()):
            itineraries = OrderedDict()

            # Build route variant members
            for member in route_master.members:

                # Create Itinerary objects from member route variants
                if member.ref in route_variants:
                    rv = route_variants.pop(member.ref)
                    itinerary = self._build_itinerary(rv, result, route_master)
                    if itinerary is not None:
                        itineraries[rv.id] = itinerary

                # Route variant was already used or is not valid
                else:
                    rv = result.get_relations(member.ref)
                    if bool(rv):
                        rv = rv.pop()
                        logging.warning("Itinerary was assigned again:")
                        logging.warning(
                            "https://osm.org/relation/%s", rv.id)
                        itinerary = self._build_itinerary(rv, result, route_master)
                        if itinerary is not None:
                            itineraries[rv.id] = itinerary
                    else:
                        logging.warning(
                            "Warning: This relation route master:")
                        logging.warning(
                            " https://osm.org/relation/%s", route_master.id)
                        logging.warning(
                            " has a member which is not a valid itinerary:")
                        logging.warning(
                            " https://osm.org/relation/%s", member.ref)

            # Create Line object from route master
            line = self._build_line(route_master, itineraries)

            if line is None:
                continue

            # Make sure route_id (ref) number is not already taken
            if line.route_id and line.route_id in [elem.route_id for elem in self.routes.values()]:
                logging.warning("'Ref' of route_master already taken")
                logging.warning(
                    " https://osm.org/relation/%s", route_master.id)
                logging.warning(" Skipped. Please fix in OpenStreetMap")
                continue

            self.routes[str(line.osm_id)] = line

        # Build routes from variants (missing master relation)
        for rvid, route_variant in sorted(route_variants.items()):
            logging.warning("Route (variant) without route_master")
            logging.warning(
                " https://osm.org/relation/%s", route_variant.id)
            logging.warning(" Please fix in OpenStreetMap")
            itinerary = self._build_itinerary(route_variant, result, False)

            # Make sure route_id (ref) number is not already taken
            if itinerary is not None:
                if itinerary.route_id in self.routes:
                    logging.warning("Route with existing route_id (ref)")
                    logging.warning(
                        " https://osm.org/relation/%s", route_variant.id)
                    logging.warning(" Skipped. Please fix in OpenStreetMap")
                else:
                    # Create Line from route variant
                    itineraries = OrderedDict()
                    itineraries[itinerary.osm_id] = itinerary
                    line = self._build_line(route_variant, itineraries)
                    if line is not None:
                        self.routes[line.route_id] = line

        # Cache data
        Cache.write_data(self.selector + '-routes', self.routes)

        return self.routes

    def set_stops(self, stops):
        self.stops = stops

    def get_stops(self, refresh=False):
        """The get_stops function returns the data of stops and stop areas from
        OpenStreetMap converted into usable objects.

        Data about stops and stop_areas is getting obtained from OpenStreetMap
        through the Overpass API, based on the configuration from the config
        file.

        Then this data gets prepared by building up objects of the class Stops
        and Station (when the Stops are members of a stop_area)

        It uses caching to leverage fast performance and spare the Overpass
        API. Special commands are used to refresh cached data.

        :param self: the own object including it's functions and variables
        :param refresh: A simple boolean indicating a data refresh or use of
            caching if possible.

        :return stops: A dictionary of Stops and Stations constituting the
            obtained data.

        """

        # Preferably return cached data about stops
        if refresh is False:
            # Check if stops data is already built in this object
            if not self.stops:
                # If not, try to get stops data from file cache
                self.stops = Cache.read_data(
                    self.selector + '-stops')

            if bool(self.stops):
                # Maybe check for unnamed stop names
                if self.auto_stop_names:
                    self._get_names_for_unnamed_stops()

                # Return cached data if found
                return self.stops

        # No cached data was found or refresh was forced
        logging.info("Query and build fresh data for stops")

        # Obtain raw data about routes from OpenStreetMap
        result = self._query_stops()
        self.stops['regular'] = {}
        self.stops['stations'] = {}

        # Build stops from ways (polygons)
        for stop in result.ways:
            osm_type = "way"
            stop_object = self._build_stop(stop, osm_type)
            if stop_object:
                self.stops['regular'][osm_type + "/" + str(
                    stop_object.osm_id)] = stop_object

        # Build stops from nodes
        for stop in result.nodes:
            osm_type = "node"
            stop_object = self._build_stop(stop, osm_type)
            if stop_object:
                self.stops['regular'][osm_type + "/" + str(
                    stop_object.osm_id)] = stop_object

        # Build stations from stop_area relations
        for stop in result.relations:
            osm_type = "relation"
            stop_object = self._build_station(stop, osm_type)
            if stop_object:
                self.stops['stations'][osm_type + "/" + str(
                    stop.id)] = stop_object

        # Cache data
        Cache.write_data(self.selector + '-stops', self.stops)

        # Maybe check for unnamed stop names
        if self.auto_stop_names:
            self._get_names_for_unnamed_stops()

        return self.stops

    def _build_line(self, route_master, itineraries):
        """Helper function to build a Line object

        Returns a initiated Line object from raw data

        """
        osm_type = "relation"

        if len(itineraries) == 0:
            logging.warning(
                "Relation without valid members. Please fix in OpenStreetMap")
            logging.warning(
                " https://osm.org/relation/%s", route_master.id)
            logging.warning(
                " Skipping whole route without valid members.")
            return None

        if 'ref' in route_master.tags:
            ref = route_master.tags['ref']
        else:
            logging.warning(
                "Relation without 'ref'. Please fix in OpenStreetMap")
            logging.warning(
                " https://osm.org/relation/%s", route_master.id)

            # Check if a ref can be taken from one of the itineraries
            ref = False
            for itinerary in list(itineraries.values()):
                if not ref and itinerary.route_id:
                    ref = itinerary.route_id
                    logging.warning(
                        "Using 'ref' from member variant instead")
                    logging.warning("%s", itinerary.osm_url)

            if not ref:
                ref = ""

        # Move to Elements class, once attributes with defaults play well
        # with inheritance https://github.com/python-attrs/attrs/issues/38
        osm_url = "https://osm.org/" + str(
            osm_type) + "/" + str(route_master.id)
        if 'name' in route_master.tags:
            name = route_master.tags['name']
        elif 'ref' in route_master.tags:
            name = route_master.tags['ref']
        else:
            name = None

        # Normalize route color information
        if 'colour' in route_master.tags:
            try:
                # Check if colour is a valid hex format
                route_master.tags['colour'] = webcolors.normalize_hex(
                    route_master.tags['colour'])
            except ValueError:
                try:
                    # Convert web color names into rgb hex values
                    route_master.tags['colour'] = webcolors.name_to_hex(
                        route_master.tags['colour'])
                except ValueError:
                    logging.warning("Invalid colour: %s found in OSM data",
                                    route_master.tags['colour'])

        # Create Line (route master) object
        line = Line(osm_id=route_master.id, osm_type=osm_type, osm_url=osm_url,
                    tags=route_master.tags, name=name, route_id=ref)

        # Add Itinerary objects (route variants) to Line (route master)
        for itinerary in list(itineraries.values()):
            try:
                line.add_itinerary(itinerary)
            except ValueError:
                logging.warning(
                    "Itinerary ID doesn't match line ID. Please fix in OSM.")
                logging.warning("%s", line.osm_url)
                itinerary.route_id = line.route_id
                line.add_itinerary(itinerary)

        return line

    def _build_itinerary(self, route_variant, query_result_set, route_master):
        """Helper function to build a Itinerary object

        Returns a initiated Itinerary object from raw data

        """
        osm_type = "relation"
        if 'ref' in route_variant.tags:
            ref = route_variant.tags['ref']
        else:
            logging.warning(
                "RouteVariant without 'ref': %s", route_variant.id)
            ref = ""

        stops = []

        # Add ids for stops of this route variant
        for stop_candidate in route_variant.members:
            if stop_candidate.role == "platform":

                if isinstance(stop_candidate, overpy.RelationNode):
                    otype = "node"

                elif isinstance(stop_candidate, overpy.RelationWay):
                    otype = "way"

                else:
                    logging.warning("Unknown type of itinerary member: %s", stop_candidate)
                    continue

                stops.append(otype + "/" + str(stop_candidate.ref))

        if route_master:
            parent_identifier = osm_type + "/" + str(route_master.id)
        else:
            parent_identifier = None

        # Move to Elements class, once attributes with defaults play well with
        # inheritance https://github.com/python-attrs/attrs/issues/38
        osm_url = "https://osm.org/" + str(
            osm_type) + "/" + str(route_variant.id)
        if 'name' in route_variant.tags:
            name = route_variant.tags['name']
        elif 'ref' in route_variant.tags:
            name = route_variant.tags['ref']
        else:
            name = None

        shape = self._generate_shape(route_variant, query_result_set)

        rv = Itinerary(osm_id=route_variant.id, osm_type=osm_type,
                       osm_url=osm_url, name=name, tags=route_variant.tags,
                       route_id=ref, shape=shape, line=parent_identifier,
                       stops=stops)
        return rv

    def _build_stop(self, stop, osm_type):
        """Helper function to build a Stop object

        Returns a initiated Stop object from raw data

        """

        if self._is_valid_stop_candidate(stop):

            # Make sure name is not empty
            if "name" not in stop.tags:
                stop.tags["name"] = "[{}]".format(self.stop_no_name)

            # Ways don't have a pair of coordinates and need to be calculated
            if osm_type == "way":
                (stop.lat, stop.lon) = Helper.get_center_of_nodes(
                    stop.get_nodes())

            # Move to Elements class, once attributes with defaults play well
            # with inheritance https://github.com/python-attrs/attrs/issues/38
            osm_url = "https://osm.org/" + str(
                osm_type) + "/" + str(stop.id)

            # Create and return Stop object
            stop = Stop(osm_id=stop.id, osm_type=osm_type, osm_url=osm_url,
                        tags=stop.tags, name=stop.tags['name'], lat=stop.lat,
                        lon=stop.lon)
            return stop

        else:
            logging.warning(
                "Warning: Potential stop is invalid and has been ignored.")
            logging.warning(
                " Check tagging: https://osm.org/%s/%s", osm_type, stop.id)
            return None

    def _build_station(self, stop_area, osm_type):
        """Helper function to build Station objects from stop_areas

        The function creates a Station object for the stop_area
        flagged as location_type = 1. This means station, that can
        group stops.

        The members of this relation add this station their parent.

        Returns a initiated Station object from raw data

        """
        # Check relation to be a station or used differently
        if 'route' in stop_area.tags:
            return None
        else:
            # Check tagging whether this is a stop area.
            if 'public_transport' not in stop_area.tags:
                logging.warning(
                    "Potential station has no public_transport tag.")
                logging.warning(
                    " Please fix on OSM: https://osm.org/%s/%s", osm_type, stop_area.id)
                return None
            elif stop_area.tags['public_transport'] != 'stop_area':
                logging.warning(
                    "Warning: Potential station is not tagged as stop_area.")
                logging.warning(
                    " Please fix on OSM: https://osm.org/%s/%s", osm_type, stop_area.id)
                return None

        # Analzyse member objects (stops) of this stop area
        members = {}
        for member in stop_area.members:

            if member.role == "platform":

                if isinstance(member, overpy.RelationNode):
                    member_osm_type = "node"
                elif isinstance(member, overpy.RelationWay):
                    member_osm_type = "way"

                identifier = member_osm_type + "/" + str(member.ref)

                if identifier in self.stops['regular']:

                    # Collect the Stop objects that are members
                    # of this Station
                    members[identifier] = self.stops['regular'][identifier]
                else:
                    logging.error("Station member was not found in data")
                    logging.error(" https://osm.org/relation/%s", stop_area.id)
                    logging.error(" https://osm.org/node/%s", member.ref)

        if len(members) < 1:
            # Stop areas with only one stop, are not stations they just
            # group different elements of one stop together.
            logging.error("Station with no members has been discarted:")
            logging.error(" https://osm.org/relation/%s", stop_area.id)
            return None

        elif len(members) == 1:
            logging.warning(
                "OSM stop area has only one platform and can't be used as a GTFS station:")
            logging.warning(" https://osm.org/relation/%s", stop_area.id)
            return None

        # Check name of stop area
        if 'name' not in stop_area.tags:
            logging.warning("Stop area without name. Please fix in OpenStreetMap:")
            logging.warning(" https://osm.org/relation/%s", stop_area.id)
            stop_area.name = self.stop_no_name
        else:
            stop_area.name = stop_area.tags["name"]

        # Calculate coordinates for stop area based on the center of it's
        # members
        stop_area.lat, stop_area.lon = Helper.get_center_of_nodes(
            members.values())

        # Move to Elements class, once attributes with defaults play well
        # with inheritance https://github.com/python-attrs/attrs/issues/38
        osm_url = "https://osm.org/" + str(
            osm_type) + "/" + str(stop_area.id)

        # Create and return Station object
        station = Station(osm_id=stop_area.id, osm_type=osm_type,
                          osm_url=osm_url, tags=stop_area.tags,
                          name=stop_area.name, lat=stop_area.lat,
                          lon=stop_area.lon)
        station.set_members(members)

        logging.info("Stop area (OSM) has been used to create a station (GTFS):\n")
        logging.info(" https://osm.org/relation/%s\n", str(stop_area.id))

        return station

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
        logging.info(query_str)
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
            );out body;

            /* Select stop area relations */
            foreach.nodes(
            rel(bn:"platform")["public_transport"="stop_area"];
            out body;
            );""" % (self.tags, self.bbox)
        logging.info(query_str)
        return api.query(query_str)

    def _generate_shape(self, route_variant, query_result_set):
        """Helper function to generate a valid GTFS shape from OSM query result
        data

        Returns list of coordinates representing a shape

        """
        shape = []

        ways = []
        for member in route_variant.members:
            if isinstance(member, overpy.RelationWay):
                if not str(member.role).startswith("platform"):
                    ways.append(member.ref)

        shape_sorter = []
        node_geography = {}

        for way in ways:
            # Obtain geography (nodes) from original query result set
            nodes = query_result_set.get_ways(way).pop().get_nodes()

            # Prepare data for sorting and geographic information of nodes
            way_nodes = []
            for node in nodes:
                way_nodes.append(node.id)
                node_geography[node.id] = {'lat': float(
                    node.lat), 'lon': float(node.lon)}

            if len(shape_sorter) == 0:
                shape_sorter.extend(way_nodes)
            elif shape_sorter[-1] == way_nodes[0]:
                del shape_sorter[-1]
                shape_sorter.extend(way_nodes)
            elif shape_sorter[-1] == way_nodes[-1]:
                del shape_sorter[-1]
                shape_sorter.extend(reversed(way_nodes))
            elif shape_sorter[0] == way_nodes[0]:
                del shape_sorter[0]
                shape_sorter.reverse()
                shape_sorter.extend(way_nodes)
            elif shape_sorter[0] == way_nodes[-1]:
                del shape_sorter[0]
                shape_sorter.reverse()
                shape_sorter.extend(reversed(way_nodes))
            else:
                logging.warning("Route has non-matching ways: https://osm.org/relation/%s",
                                route_variant.id)
                logging.warning(
                    "  Problem at: https://osm.org/way/%s", way)
                break

        for sorted_node in shape_sorter:
            shape.append(node_geography[sorted_node])

        return shape

    def _is_valid_stop_candidate(self, stop):
        """Helper function to check if a stop candidate has a valid tagging

        :return bool: Returns True or False

        """
        if 'public_transport' in stop.tags:
            if stop.tags['public_transport'] == 'platform':
                return True
            elif stop.tags['public_transport'] == 'station':
                return True
        if 'highway' in stop.tags:
            if stop.tags['highway'] == 'bus_stop':
                return True
        if 'amenity' in stop.tags:
            if stop.tags['amenity'] == 'bus_station':
                return True
        return False

    def _get_names_for_unnamed_stops(self):
        """Intelligently guess stop names for unnamed stops by sourrounding
        street names and amenities.

        Caches stops with newly guessed names.

        """
        # Loop through all stops
        for stop in self.stops['regular'].values():

            # If there is no name, query one intelligently from OSM
            if stop.name == "[{}]".format(self.stop_no_name):
                self._find_best_name_for_unnamed_stop(stop)
                logging.info("* Found alternative stop name: " +
                             stop.name + " - " + stop.osm_url)

                # Cache stops with newly created stop names
                Cache.write_data(self.selector + '-stops', self.stops)

    def _find_best_name_for_unnamed_stop(self, stop):
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
            stop.name = self.stop_no_name
            return

        # find closest candidate
        winner = None
        winner_distance = sys.maxsize
        for candidate in candidates:
            if isinstance(candidate, overpy.Way):
                lat, lon = Helper.get_center_of_nodes(
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
        stop.name = winner.tags["name"]
