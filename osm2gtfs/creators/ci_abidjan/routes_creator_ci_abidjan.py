# coding=utf-8

from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorCiAbidjan(RoutesCreator):

    def add_routes_to_feed(self, feed, data):
        # Get routes information
        data.get_routes()

        # GTFS routes are created in TripsCreator
        return
