# coding=utf-8

import sys
import overpy
from datetime import timedelta, datetime
from core.osm_stops import Stop


class BaseRoute(object):

    def __init__(self, osm, ref, name):
        self.id = osm
        self.ref = ref
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.last_update = None
        self.horarios = []
        self.operacoes = []

    def __repr__(self):
        rep = ""
        if self.ref is not None:
            rep += str(self.ref) + " | "
        if self.name is not None:
            rep += self.name
        return rep

    # TODO: Move over to Fenix implementation
    def add_linha(self, linha):
        self.name = linha['nome'].encode('utf-8')

        self.last_update = datetime.strptime(linha['alterado_em'], "%d/%m/%Y")

        # TODO format this data
        self.horarios = linha['horarios']
        self.operacoes = linha['operacoes']


class Route(BaseRoute):

    def __init__(self, osm, fr, to, stops, master, ref=None, name=None):
        BaseRoute.__init__(self, osm, ref, name)
        self.fr = fr
        self.to = to
        self.stops = stops
        self.master = master
        self.shape = None
        self.duration = None

    def __repr__(self):
        rep = BaseRoute.__repr__(self)
        if self.stops is not None:
            rep += " | Stops: " + str(len(self.stops)) + " | "
        rep += "https://www.openstreetmap.org/relation/" + str(self.id) + " "
        rep += "http://www.consorciofenix.com.br/horarios?q=" + str(self.ref)
        return rep

    # TODO: Move over to Fenix implementation
    def add_linha(self, linha):
        super(Route, self).add_linha(linha)

        # save duration
        duration_str = linha['tempo_de_percurso'].replace('aproximado', '')
        (hours, tmp, minutes) = duration_str.partition(':')
        self.duration = timedelta(hours=int(hours), minutes=int(minutes))

    def match_first_stops(self, sim_stops):
        # get the first stop of the route
        stop = self.get_first_stop()

        # normalize its name
        stop.name = Stop.normalize_name(stop.name)

        # get first stop from relation 'from' tag
        alt_stop_name = self.get_first_alt_stop()
        alt_stop_name = Stop.normalize_name(alt_stop_name.encode('utf-8'))

        # trying to match first stop from OSM with SIM
        for o_sim_stop in sim_stops:
            sim_stop = Stop.normalize_name(o_sim_stop)
            if sim_stop == stop.name:
                return o_sim_stop
            elif sim_stop == alt_stop_name:
                return o_sim_stop

        # print some debug information when no stop match found
        sys.stderr.write(str(self) + "\n")
        sys.stderr.write(str(sim_stops) + "\n")
        sys.stderr.write("-----\n")
        sys.stderr.write("OSM Stop: '" + stop.name + "'\n")
        sys.stderr.write("OSM ALT Stop: '" + alt_stop_name + "'\n")
        for sim_stop in sim_stops:
            sim_stop = Stop.normalize_name(sim_stop)
            sys.stderr.write("SIM Stop: '" + sim_stop + "'\n")
        print
        return None

    def get_first_stop(self):
        if len(self.stops) > 0:
            return self.stops[0]
        else:
            return None

    def get_first_alt_stop(self):
        if self.fr is not None:
            return self.fr
        else:
            return "???"

    def has_proper_master(self):
        return self.master is not None and len(self.master.routes) > 1

    def add_shape(self, route_variant, query_result_set, refresh=False):
        if self.shape is not None and not refresh:
            return

        self.shape = []

        ways = []
        for member in route_variant.members:
            if isinstance(member, overpy.RelationWay):
                if not member.role == "platform":
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
                sys.stderr.write(
                    "Route has non-matching ways: " + str(self) + "\n")
                sys.stderr.write(
                    "  Problem at: http://osm.org/way/" + str(way) + "\n")
                break

        for sorted_node in shape_sorter:
            self.shape.append(node_geography[sorted_node])

    def print_shape_for_leaflet(self):
        print "var shape = [",
        i = 0
        for node in self.shape:
            print "new L.LatLng(" + str(node["lat"]) + ", " + str(node["lon"]) + ")",
            if i != len(self.shape) - 1:
                print ",",
            i += 1
        print "];"
        i = 0
        for node in self.shape:
            print "L.marker([" + str(node["lat"]) + ", " + str(node["lon"]) + "]).addTo(map)"
            print "    .bindPopup(\"" + str(i) + "\").openPopup();"
            i += 1

    @staticmethod
    def normalize_route(name):
        return name.replace('B', '')


class RouteMaster(BaseRoute):

    def __init__(self, osm, ref, name, routes):
        BaseRoute.__init__(self, osm, ref, name)
        self.routes = routes

    def __repr__(self):
        rep = BaseRoute.__repr__(self)
        rep += " | https://www.openstreetmap.org/relation/" + \
            str(self.id) + "\n"

        i = 1
        for route in self.routes:
            rep += "  Route %d: " % i
            rep += str(self.routes[route]) + "\n"
            i += 1

        return rep

    def get_first_stop(self):
        return self.routes.itervalues().next().get_first_stop()

    def get_first_alt_stop(self):
        return self.routes.itervalues().next().get_first_alt_stop()
