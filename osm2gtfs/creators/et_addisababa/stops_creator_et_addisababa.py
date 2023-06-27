# coding=utf-8

from osm2gtfs.creators.stops_creator import StopsCreator

class StopsCreatorEtAddisababa(StopsCreator):
    def _define_stop_id(self, stop):
        """
        We always use the node ID in Addis Ababa because refs currently might contain duplicates
        """

        stop_id = stop.osm_type + "/" + str(stop.osm_id)

        return stop_id