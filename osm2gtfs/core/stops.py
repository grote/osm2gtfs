# coding=utf-8

import sys
import attr


@attr.s
class Station(object):

    osm_id = attr.ib()
    tags = attr.ib()
    lat = attr.ib()
    lon = attr.ib()
    name = attr.ib()

    osm_type = attr.ib(default="relation")
    location_type = attr.ib(default=1)
    osm_url = attr.ib(default="http://osm.org/" +
                      str(osm_type) + "/" + str(osm_id))

    # Stops forming part of this Station
    _members = attr.ib(default=attr.Factory(list))

    def set_members(self, members):
        self._members = members

    def get_members(self):
        return self._members


@attr.s
class Stop(object):

    osm_id = attr.ib()
    osm_type = attr.ib()
    tags = attr.ib()
    lat = attr.ib()
    lon = attr.ib()
    name = attr.ib()

    location_type = attr.ib(default=0)
    osm_url = attr.ib(default="http://osm.org/" +
                      str(osm_type) + "/" + str(osm_id))

    # The id of the Station this Stop might be part of.
    _parent_station = attr.ib(default=None)

    def set_parent_station(self, identifier, override=False):
        """
        Set the parent_station_id on the first time;
        Second attempts throw a warning
        """
        if self._parent_station is None or override is True:
            self._parent_station = identifier
        else:
            sys.stderr.write("Warning: Stop is part of two stop areas:\n")
            sys.stderr.write(
                "http://osm.org/" + self.osm_type + "/" + str(
                    self.osm_id) + "\n")
            sys.stderr.write("http://osm.org/" + identifier + "\n")
            sys.stderr.write("http://osm.org/" + self._parent_station + "\n")
            sys.stderr.write("Please fix in OpenStreetMap\n")

    def get_parent_station(self):
        return self._parent_station
