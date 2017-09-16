# coding=utf-8

from math import cos, sin, atan2, sqrt, radians, degrees


class Stop(object):

    def __init__(self, osm, stop_type, name=None, lat=None, lon=None):
        self.id = osm
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.lat = lat
        self.lon = lon
        self.type = stop_type
        self.added = False

    def __repr__(self):
        rep = ""
        if self.name is not None:
            rep += self.name
        if self.lat is not None and self.lon is not None:
            rep += " http://www.openstreetmap.org/?mlat=" + str(self.lat) + "&mlon=" + str(self.lon)
        rep += " (https://www.openstreetmap.org/" + self.type + "/" + str(self.id) + ")"
        return rep

    @staticmethod
    def get_center_of_nodes(nodes):
        """Helper function to get center coordinates of a group of nodes

        """
        x = 0
        y = 0
        z = 0

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


class StopArea(object):

    def __init__(self, osm, stop_members, name=None):
        self.id = osm
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.stop_members = stop_members
        self.lat, self.lon = Stop.get_center_of_nodes(stop_members.values())

    def __repr__(self):
        rep = ""
        if self.name is not None:
            rep += self.name
        if self.lat is not None and self.lon is not None:
            rep += " lat: " + str(self.lat) + " lon: " + str(self.lon) + "\n\t"
        for ref, stop in self.stop_members.iteritems():
            rep += " | Stop member: " + ref + " - " + stop.name
        return rep
