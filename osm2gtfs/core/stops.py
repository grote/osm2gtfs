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

    stop_members = attr.ib(default=attr.Factory(list))

    def __init__(self, osm_id, stop_members, name=None):
        self.osm_id = osm_id
        if name is not None:
            self.name = name.encode('utf-8')
        else:
            self.name = name
        self.stop_members = stop_members

        from osm2gtfs.core.osm_connector import OsmConnector
        self.lat, self.lon = OsmConnector.get_center_of_nodes(self.stop_members.values())
