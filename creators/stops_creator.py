# coding=utf-8


class StopsCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_stops_to_schedule(self, schedule, data):

        # Get stops information
        stops = data.get_stops()

        # Loop through all stops
        for stop in stops.values():

            # Add stop to GTFS object
            schedule.AddStop(
                lat=float(stop.lat),
                lng=float(stop.lon),
                name=stop.name,
                stop_id=str(stop.id)
            )
