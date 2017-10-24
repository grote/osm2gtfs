# coding=utf-8

from osm2gtfs.creators.stops_creator import StopsCreator


class StopsCreatorCrGam(StopsCreator):

    # Override construction of stop_id
    def _define_stop_id(self, stop):
        if stop.osm_type == "relation":
            return "SA" + str(stop.osm_id)
        else:
            return str(stop.osm_id)
