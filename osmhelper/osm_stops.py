# coding=utf-8

import overpy
import re
import sys
from math import cos, sin, atan2, sqrt, radians, degrees
from transitfeed import util


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

    def get_all_data(self):
        if self.name is not None and self.lat is not None and self.lon is not None:
            # this stop is already full/complete
            return

        api = overpy.Overpass()
        result = api.query(
            """
            <id-query ref="%s" type="%s"/>
            <print/>
            """ % (str(self.id), self.type)
        )

        if self.type == "node":
            member = result.get_node(self.id, resolve_missing=True)
        elif self.type == "way":
            member = result.get_way(self.id, resolve_missing=True)
        else:
            raise RuntimeError("Unknown stop type: " + str(self.type))

        # more tags: 'alt_name', 'shelter', 'wheelchair', 'bench'

        if 'name' in member.tags:
            self.name = member.tags['name'].encode('utf-8')
        else:
            self.name = self.NO_NAME

        if self.type == "node":
            self.lat = member.lat
            self.lon = member.lon
        elif self.type == "way":
            (self.lat, self.lon) = self.get_center_of_nodes(member.get_nodes(resolve_missing=True))
        else:
            raise RuntimeError("Unknown type of stop: " + str(self))

        print self

    def get_interim_stop_name(self):
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
        """ % (self.lat, self.lon, self.lat, self.lon))

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
            # give stop a different name, so we won't search again without refreshing data
            self.name = "Ponto sem nome"
            return

        # find closest candidate
        winner = None
        winner_distance = sys.maxint
        for candidate in candidates:
            if isinstance(candidate, overpy.Way):
                lat, lon = Stop.get_center_of_nodes(candidate.get_nodes(resolve_missing=True))
                distance = util.ApproximateDistance(
                    lat,
                    lon,
                    self.lat,
                    self.lon
                )
            else:
                distance = util.ApproximateDistance(
                    candidate.lat,
                    candidate.lon,
                    self.lat,
                    self.lon
                )
            if distance < winner_distance:
                winner = candidate
                winner_distance = distance

        # take name from winner
        self.name = winner.tags["name"].encode('utf-8')

    @staticmethod
    def from_relation_member(member):
        stop_id = member.ref

        if isinstance(member, overpy.RelationNode):
            stop_type = "node"
        elif isinstance(member, overpy.RelationWay):
            stop_type = "way"
        else:
            raise RuntimeError("Unknown type: " + str(member))

        return Stop(stop_id, stop_type)

    @staticmethod
    def normalize_name(old_name):
        name = STOP_REGEX.sub(r'\1', old_name)
        name = name.replace('Terminal de Integração da Lagoa da Conceição', 'TILAG')
        return name

    @staticmethod
    def get_center_of_nodes(nodes):
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
