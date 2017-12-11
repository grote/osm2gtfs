# coding=utf-8

import transitfeed
from osm2gtfs.creators.stops_creator import StopsCreator


class StopsCreatorFenix(StopsCreator):

    # Override construction of stop_id
    def get_gtfs_stop_id(self, stop):

        # Simply returns osm_id regardless of the osm_type as only map
        # objects of type nodes are assumed.
        return stop.osm_id
