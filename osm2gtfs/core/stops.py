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

    stop_id = attr.ib(default="")
    osm_type = attr.ib(default="relation")
    location_type = attr.ib(default=1)
    osm_url = attr.ib(default=None)

    # Stops forming part of this Station
    _members = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        '''Populates the object with information obtained from the tags

        '''
        self.osm_url = "https://osm.org/" + str(
            self.osm_type) + "/" + str(self.osm_id)

    def set_members(self, members):
        self._members = members

    def get_members(self):
        return self._members

    def get_stop_id(self):
        return self.stop_id

    def set_stop_id(self, stop_id):
        self.stop_id = stop_id


@attr.s
class Stop(object):

    osm_id = attr.ib()
    osm_type = attr.ib()
    tags = attr.ib()
    lat = attr.ib()
    lon = attr.ib()
    name = attr.ib()

    stop_id = attr.ib("")
    location_type = attr.ib(default=0)
    osm_url = attr.ib(default=None)

    # The id of the Station this Stop might be part of.
    _parent_station = attr.ib(default=None)

    def __attrs_post_init__(self):
        '''Populates the object with information obtained from the tags

        '''
        self.osm_url = "https://osm.org/" + str(
            self.osm_type) + "/" + str(self.osm_id)

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
                "https://osm.org/" + self.osm_type + "/" + str(
                    self.osm_id) + "\n")

    def get_parent_station(self):
        return self._parent_station

    def get_stop_id(self):
        return self.stop_id

    def set_stop_id(self, stop_id):
        self.stop_id = stop_id
