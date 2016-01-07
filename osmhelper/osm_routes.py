# coding=utf-8

import sys
from datetime import timedelta, datetime
from osmapi import OsmApi
from osmhelper.osm_stops import Stop


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

    def add_shape(self, refresh=False):
        if self.shape is not None and not refresh:
            return

        self.shape = []

        ways = []
        osm_api = OsmApi()
        for member in osm_api.RelationGet(self.id)['member']:
            if member["type"] == "way" and not member["role"].startswith("platform"):
                ways.append(member["ref"])

        nodes = []
        ways_info = osm_api.WaysGet(ways)
        for way in ways:
            if len(nodes) == 0:
                nodes.extend(ways_info[way]["nd"])
            elif nodes[-1] == ways_info[way]["nd"][0]:
                del nodes[-1]
                nodes.extend(ways_info[way]["nd"])
            elif nodes[-1] == ways_info[way]["nd"][-1]:
                del nodes[-1]
                nodes.extend(reversed(ways_info[way]["nd"]))
            elif nodes[0] == ways_info[way]["nd"][0]:
                del nodes[0]
                nodes.reverse()
                nodes.extend(ways_info[way]["nd"])
            elif nodes[0] == ways_info[way]["nd"][-1]:
                del nodes[0]
                nodes.reverse()
                nodes.extend(reversed(ways_info[way]["nd"]))
            else:
                sys.stderr.write("Route has non matching ways: " + str(self) + "\n")
                sys.stderr.write("  Problem at: http://www.openstreetmap.org/way/" + str(ways_info[way]["id"]) + "\n")
                pass

        # limit the number of nodes per API request to prevent 414
        size = 100
        for nodes_sublist in [nodes[i:i + size] for i in range(0, len(nodes), size)]:
            nodes_info = osm_api.NodesGet(nodes_sublist)
            for node in nodes_sublist:
                self.shape.append({'lat': nodes_info[node]["lat"], 'lon': nodes_info[node]["lon"]})

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
        rep += " | https://www.openstreetmap.org/relation/" + str(self.id) + "\n"
        
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
