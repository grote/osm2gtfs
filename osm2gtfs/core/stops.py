# coding=utf-8

import attr


@attr.s
class Stop(object):

    osm_id = attr.ib()
    osm_type = attr.ib()
    name = attr.ib()
    lat = attr.ib()
    lon = attr.ib()
    gtfs_id = attr.ib(default=osm_id)
    osm_url = attr.ib(default="http://osm.org/" +
                      str(osm_type) + "/" + str(osm_id))


class StopArea(object):

    osm_id = attr.ib()
    name = attr.ib()
    lat = attr.ib()
    lon = attr.ib()
    
    _stop_members = []

    def __init__(self, osm_id, stop_members, name=None):
        self.osm_id = osm_id
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.stop_members = stop_members
        self.lat, self.lon = Stop.get_center_of_nodes(stop_members.values())
