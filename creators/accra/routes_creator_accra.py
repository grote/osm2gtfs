# coding=utf-8

from creators.routes_creator import RoutesCreator


class RoutesCreatorAccra(RoutesCreator):

    def add_routes_to_schedule(self, schedule, data):
        # Get routes information
        data.get_routes()

        # GTFS routes are created in TripsCreator
        return
