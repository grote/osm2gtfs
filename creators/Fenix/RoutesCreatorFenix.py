# coding=utf-8

from creators.RoutesCreator import RoutesCreator


class RoutesCreatorFenix(RoutesCreator):

    def add_routes_to_schedule(self, schedule, data):

        # Get routes information
        data.get_routes()

        # Fenix logic is doing route aggregation in TripsCreator
        return
