# coding=utf-8

import sys
import overpy
from collections import OrderedDict
from math import cos, sin, atan2, sqrt, radians, degrees
from transitfeed import util
from osm2gtfs.core.cache import Cache
from osm2gtfs.core.routes import Itinerary, Line
from osm2gtfs.core.stops import Stop, StopArea


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
        for key, value in self.config["query"].get("tags", {}).iteritems():
            self.tags += str('["' + key + '" = "' + value + '"]')
        if not self.tags:
            # fallback
            self.tags = '["public_transport:version" = "2"]'
            print("No tags found for querying from OpenStreetMap.")
            print("Using tag 'public_transport:version=2'")

        # Define name for stops without one
        self.stop_no_name = 'No name'
        if 'stops' in self.config and 'name_without' in self.config['stops']:
            self.stop_no_name = self.config['stops']['name_without'].encode()

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
            itineraries = OrderedDict()

            # Build route variant members
            for member in route_master.members:

                # Create Itinerary objects from member route variants
                if member.ref in route_variants:
                    rv = route_variants.pop(member.ref)
                    itineraries[rv.id] = self._build_itinerary(rv, result)

                # Route variant was already used or is not valid
                else:
                    rv = result.get_relations(member.ref)
                    if bool(rv):
                        rv = rv.pop()
                        sys.stderr.write("Itinerary was assigned again:\n")
                        sys.stderr.write(
                            "http://osm.org/relation/" + str(rv.id) + "\n")
                        itineraries[rv.id] = self._build_itinerary(rv, result)
                    else:
                        sys.stderr.write(
                            "Member relation is not a valid itinerary:\n")
                        sys.stderr.write("http://osm.org/relation/" + str(member.ref) + "\n")

            # Create Line object from route master
            line = self._build_line(route_master, itineraries)

            # Make sure route_id (ref) number is not already taken
            if line.route_id in self.routes:
                sys.stderr.write("'Ref' of route_master already taken\n")
                sys.stderr.write(
                    "http://osm.org/relation/" + str(route_master.id) + "\n")
                sys.stderr.write("Skipped. Please fix in OpenStreetMap\n")
            else:
                self.routes[line.route_id] = line

        # Build routes from variants (missing master relation)
        for rvid, route_variant in route_variants.iteritems():
            sys.stderr.write("Itinerary without master\n")
            sys.stderr.write(
                "http://osm.org/relation/" + str(route_variant.id) + "\n")
            sys.stderr.write("Please fix in OpenStreetMap\n")
            itinerary = self._build_itinerary(route_variant, result)

            # Make sure route_id (ref) number is not already taken
            if itinerary.route_id in self.routes:
                sys.stderr.write("Itinerary with existing route id (ref)\n")
                sys.stderr.write(
                    "http://osm.org/relation/" + str(route_variant.id) + "\n")
                sys.stderr.write("Skipped. Please fix in OpenStreetMap\n")
            else:
                # Create Line from route variant
                itineraries = OrderedDict()
                itineraries[itinerary.osm_id] = itinerary
                line = self._build_line(route_variant, itineraries)
                self.routes[line.route_id] = line

        # Cache data
        Cache.write_data(self.selector + '-routes', self.routes)

        return self.routes

    def get_stops(self, refresh=False):
        """The get_stops function returns the data of stops and stop areas from
        OpenStreetMap converted into usable objects.

        Data about stops and stop_areas is getting obtained from OpenStreetMap
        through the Overpass API, based on the configuration from the config
        file.

        Then this data gets prepared by building up objects of the class Stops
        and StopArea (when the Stops are members of a stop_area)

        It uses caching to leverage fast performance and spare the Overpass
        API. Special commands are used to refresh cached data.

        :param self: the own object including it's functions and variables
        :param refresh: A simple boolean indicating a data refresh or use of
            caching if possible.

        :return stops: A dictionary of Stops and StopAreas constituting the
            obtained data.

        """

        # Preferably return cached data about stops
        if refresh is False:
            # Check if stops data is already built in this object
            if not self.stops:
                # If not, try to get stops data from file cache
                self.stops = Cache.read_data(self.selector + '-stops')

            if bool(self.stops):
                # Maybe check for unnamed stop names
                if self.auto_stop_names:
                    self._get_names_for_unnamed_stops()

                # Return cached data if found
                return self.stops

        # No cached data was found or refresh was forced
        print("Query and build fresh data for stops")

        # Obtain raw data about routes from OpenStreetMap
        result = self._query_stops()

        # Build stops from ways (polygons)
        for stop in result.ways:
            if self._is_valid_stop_candidate(stop):
                self.stops["way/" + str(stop.id)
                           ] = self._build_stop(stop, "way")

        # Build stops from nodes
        for stop in result.nodes:
            if self._is_valid_stop_candidate(stop):
                self.stops["node/" + str(stop.id)
                           ] = self._build_stop(stop, "node")

        # Build stop_areas
        for relation in result.relations:
            # valid stop_area candidade?
            if 'public_transport' in relation.tags:
                if relation.tags["public_transport"] == "stop_area":
                    try:
                        self.stops["relation/" + str(relation.id)
                                   ] = self._build_stop_area(relation)
                    except (ValueError, TypeError) as e:
                        sys.stderr.write('Cannot add stop area: ' + str(relation.id))

        # Cache data
        Cache.write_data(self.selector + '-stops', self.stops)

        # Maybe check for unnamed stop names
        if self.auto_stop_names:
            self._get_names_for_unnamed_stops()

        # Warning about stops without stop_area
        for ref, elem in self.stops.iteritems():
            if type(elem) is Stop:
                sys.stderr.write("Stop is not member of a stop_area." +
                                 " Please fix in OpenStreetMap\n")
                sys.stderr.write("http://osm.org/" + ref + "\n")

        return self.stops

    def _build_line(self, route_master, itineraries):
        """Helper function to build a Line object

        Returns a initiated Line object from raw data

        """
        if 'ref' in route_master.tags:
            ref = route_master.tags['ref']
        else:
            sys.stderr.write(
                "Relation without 'ref'. Please fix in OpenStreetMap\n")
            sys.stderr.write(
                "http://osm.org/relation/" + str(route_master.id) + "\n")

            # Check if a ref can be taken from one of the itineraries
            ref = False
            for itinerary in list(itineraries.values()):
                if not ref and itinerary.route_id:
                    ref = itinerary.route_id
                    sys.stderr.write(
                        "Using 'ref' from member variant instead\n")
                    sys.stderr.write(itinerary.osm_url + "\n")

            # Ignore whole Line if no reference number could be obtained
            if not ref:
                sys.stderr.write(
                    "No 'ref' could be obtained. Skipping whole route.\n")
                return

        name = route_master.tags['name']
        frequency = None
        if "frequency" in route_master.tags:
            frequency = route_master.tags['frequency']

        color = "FFFFFF"
        if "colour" in route_master.tags:
            color = OsmConnector.get_hex_code_for_color(route_master.tags['colour'])

        text_color = OsmConnector.get_complementary_color(color)
        if "text_colour" in route_master.tags:
            text_color = OsmConnector.get_hex_code_for_color(route_master.tags['text_colour'])

        if 'route_master' in route_master.tags:
            route_type = route_master.tags['route_master'].capitalize()

        # If there was no route_master present we have a route relation here
        elif 'route' in route_master.tags:
            route_type = route_master.tags['route'].capitalize()

        # Create Line (route master) object
        line = Line(osm_id=route_master.id, route_id=ref,
                    name=name, route_type=route_type, frequency=frequency,
                    route_color=color, route_text_color=text_color)

        # Add Itinerary objects (route variants) to Line (route master)
        for itinerary in list(itineraries.values()):
            try:
                line.add_itinerary(itinerary)
            except ValueError:
                sys.stderr.write(
                    "Itinerary ID does not match line ID. Please fix in OSM.\n")
                sys.stderr.write(line.osm_url)
                itinerary.route_id = line.route_id
                line.add_itinerary(itinerary)

        return line

    def _build_itinerary(self, route_variant, query_result_set):
        """Helper function to build a Itinerary object

        Returns a initiated Itinerary object from raw data

        """
        if 'ref' in route_variant.tags:
            ref = route_variant.tags['ref']
        else:
            sys.stderr.write(
                "RouteVariant without 'ref': " + str(route_variant.id) + "\n")
            sys.stderr.write(
                "http://osm.org/relation/" + str(route_variant.id) + "\n")
            sys.stderr.write(
                "Whole Itinerary skipped. Please fix in OpenStreetMap\n")
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

        if 'travel_time' in route_variant.tags:
            travel_time = route_variant.tags['travel_time']
        else:
            travel_time = None

        stops = []

        # Add ids for stops of this route variant
        for stop_candidate in route_variant.members:
            if stop_candidate.role == "platform":

                if isinstance(stop_candidate, overpy.RelationNode):
                    otype = "node"

                elif isinstance(stop_candidate, overpy.RelationWay):
                    otype = "way"

                else:
                    sys.stderr.write("Unknown type of itinerary member: " +
                                     str(stop_candidate) + "\n")

                stops.append(otype + "/" + str(stop_candidate.ref))

        shape = self._generate_shape(route_variant, query_result_set)
        rv = Itinerary(osm_id=route_variant.id, fr=fr,
                       to=to, stops=stops, shape=shape, route_id=ref,
                       name=name, travel_time=travel_time)
        return rv

    def _build_stop(self, stop, stop_type):
        """Helper function to build a Stop object

        Returns a initiated Stop object from raw data

        """

        # Make sure name is not empty
        if 'name' not in stop.tags:
            stop.tags['name'] = "[" + self.stop_no_name + "]"

        # Ways don't have coordinates and they have to be calculated
        if stop_type == "way":
            (stop.lat, stop.lon) = self.get_center_of_nodes(stop.get_nodes())

        s = Stop(stop.id, "node", unicode(stop.tags['name']), stop.lat, stop.lon)
        return s

    def _build_stop_area(self, relation):
        """Helper function to build a StopArea object

        Returns a initiated StopArea object from raw data
        """
        stop_members = {}
        for member in relation.members:
            if (isinstance(member, overpy.RelationNode) and
               member.role == "platform"):
                if "node/" + str(member.ref) in self.stops:
                    stop = self.stops.pop("node/" + str(member.ref))
                    stop_members["node/" + str(member.ref)] = stop
                else:
                    sys.stderr.write("Stop not found in stops: ")
                    sys.stderr.write("http://osm.org/node/" +
                                     str(member.ref) + "\n")
        if len(stop_members) < 1:
            sys.stderr.write("Cannot build stop area with no members\n")

        if 'name' not in relation.tags:
            sys.stderr.write("Stop area without name." +
                             " Please fix in OpenStreetMap\n")
            sys.stderr.write("http://osm.org/relation/" +
                             str(relation.id) + "\n")
            stop_area = StopArea(relation.id, stop_members, self.stop_no_name)
        else:
            stop_area = StopArea(relation.id, stop_members,
                                 relation.tags["name"])
        # print(stop_area)
        return stop_area

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
            );out body;

            /* Select stop area relations */
            foreach.nodes(
            rel(bn:"platform")["public_transport"="stop_area"];
            out body;
            );""" % (self.tags, self.bbox)
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
                sys.stderr.write("Route has non-matching ways: " +
                                 "http://osm.org/relation/" +
                                 str(route_variant.id) + "\n")
                sys.stderr.write(
                    "  Problem at: http://osm.org/way/" + str(way) + "\n")
                break

        for sorted_node in shape_sorter:
            shape.append(node_geography[sorted_node])

        return shape

    def _is_valid_stop_candidate(self, stop):
        """Helper function to check if a stop candidate has a valid tagging

        Returns True or False

        """
        if 'public_transport' in stop.tags:
            if stop.tags['public_transport'] == 'platform':
                return True
            elif stop.tags['public_transport'] == 'station':
                return True
        elif 'highway' in stop.tags:
            if stop.tags['highway'] == 'bus_stop':
                return True
        elif 'amenity' in stop.tags:
            if stop.tags['amenity'] == 'bus_station':
                return True
        return False

    def _get_names_for_unnamed_stops(self):
        """Intelligently guess stop names for unnamed stops by sourrounding
        street names and amenities.

        Caches stops with newly guessed names.

        """
        # Loop through all stops
        for stop in self.stops.values():

            # If there is no name, query one intelligently from OSM
            if stop.name == "[" + self.stop_no_name + "]":
                self._find_best_name_for_unnamed_stop(stop)
                print(stop)

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
        winner_distance = sys.maxint
        for candidate in candidates:
            if isinstance(candidate, overpy.Way):
                lat, lon = self.get_center_of_nodes(
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

    @staticmethod
    def get_center_of_nodes(nodes):
        """Helper function to get center coordinates of a group of nodes

        """
        x = 0
        y = 0
        z = 0

        if len(nodes) < 1:
            sys.stderr.write("Cannot find the center of zero nodes\n")
        for node in nodes:
            lat = radians(float(node.lat))
            lon = radians(float(node.lon))

            x += cos(lat) * cos(lon)
            y += cos(lat) * sin(lon)
            z += sin(lat)

        x = float(x / len(nodes))
        y = float(y / len(nodes))
        z = float(z / len(nodes))

        center_lat = degrees(atan2(z, sqrt(x * x + y * y)))
        center_lon = degrees(atan2(y, x))

        return center_lat, center_lon

    @staticmethod
    def get_hex_code_for_color(color):
        color = color.lower()
        if color == u'black':
            return '000000'
        if color == u'blue':
            return '0000FF'
        if color == u'gray':
            return '808080'
        if color == u'green':
            return '008000'
        if color == u'purple':
            return '800080'
        if color == u'red':
            return 'FF0000'
        if color == u'silver':
            return 'C0C0C0'
        if color == u'white':
            return 'FFFFFF'
        if color == u'yellow':
            return 'FFFF00'
        print('Color not known: ' + color)
        return 'FA8072'

    @staticmethod
    def get_complementary_color(color):
        """
        Returns complementary RGB color
        Source: https://stackoverflow.com/a/38478744
        """
        if color[0] == '#':
            color = color[1:]
        rgb = (color[0:2], color[2:4], color[4:6])
        comp = ['%02X' % (255 - int(a, 16)) for a in rgb]
        return ''.join(comp)
