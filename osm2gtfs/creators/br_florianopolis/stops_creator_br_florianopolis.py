# coding=utf-8

from osm2gtfs.creators.stops_creator import StopsCreator


class StopsCreatorBrFlorianopolis(StopsCreator):

    # Override construction of stop_id
    def _define_stop_id(self, stop):

        # Simply returns osm_id regardless of the osm_type as only map
        # objects of type nodes are assumed.
        return str(stop.osm_id)
