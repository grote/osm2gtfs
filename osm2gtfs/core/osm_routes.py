# coding=utf-8


class BaseRoute(object):

    def __init__(self, osm, ref, name):
        """Base route initializer
        :param osm: ?
        :param ref: ?
        :param name: Name of the base route.
        """
        self.id = osm
        self.ref = ref
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.last_update = None

    def __repr__(self):
        rep = ""
        if self.ref is not None:
            rep += str(self.ref) + " | "
        if self.name is not None:
            rep += self.name
        return rep


class Route(BaseRoute):

    def __init__(self, osm, fr, to, stops, master, ref, name, shape, travel_time=None):
        BaseRoute.__init__(self, osm, ref, name)
        self.fr = fr
        self.to = to
        self.stops = stops
        self.master = master
        self.shape = shape
        self.travel_time = travel_time
        self.duration = None

    # TODO This has fenix specific information.
    # It might not be part of osm2gtfs core
    def __repr__(self):
        rep = BaseRoute.__repr__(self)
        if self.stops is not None:
            rep += " | Stops: " + str(len(self.stops)) + " | "
        rep += "https://www.openstreetmap.org/relation/" + str(self.id) + " "
        rep += "http://www.consorciofenix.com.br/horarios?q=" + str(self.ref)
        return rep

    def set_duration(self, duration):
        """Sets the duration of the route
        :param duration: timedelta
        """
        self.duration = duration

    def get_first_stop(self):
        """Returns the first stop from the stops dataset
        Return None when there are no stops defined
        :return object
        """
        if len(self.stops) > 0:
            return self.stops[0]
        else:
            return None

    # TODO This is fenix specific, so ideally should not be at the core.
    # This method will not be covered by tests.
    def get_first_alt_stop(self):
        """Returns the first alt stop from the stops dataset
        Return ??? when there are no alt defined
        :return list
        """
        if self.fr is not None:
            return self.fr
        else:
            return "???"

    def has_proper_master(self):
        """Returns True if master is defined and it has at leas one route
        :return bool
        """
        return self.master is not None and len(self.master.routes) > 1

    # TODO move to debug class?
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


class RouteMaster(BaseRoute):

    def __init__(self, osm, ref, name, routes, frequency=None):
        BaseRoute.__init__(self, osm, ref, name)
        self.routes = routes
        self.frequency = frequency
        for route in self.routes.values():
            route.master = self

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

    def set_duration(self, duration):
        for route in self.routes.values():
            route.set_duration(duration)

    def get_first_stop(self):
        return self.routes.itervalues().next().get_first_stop()

    def get_first_alt_stop(self):
        return self.routes.itervalues().next().get_first_alt_stop()
