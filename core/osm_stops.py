# coding=utf-8

import re
from math import cos, sin, atan2, sqrt, radians, degrees

STOP_REGEX = re.compile('(TICAN|TISAN|TICEN|TITRI|TILAG|TIRIO|TISAC).*')


class Stop(object):
    NO_NAME = "[Ponto sem nome]"

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

    # TODO: Move over to Fenix implementation
    @staticmethod
    def normalize_name(old_name):
        name = STOP_REGEX.sub(r'\1', old_name)
        name = name.replace('Terminal de Integração da Lagoa da Conceição', 'TILAG')
        name = name.replace('Terminal Centro', 'TICEN')
        return name

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

    @staticmethod
    def is_valid_stop_candidate(stop):
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
