# coding=utf-8

import sys
import overpy
import re
import pickle
import transitfeed
from creators_default.StopsCreator import StopsCreator

class StopsCreatorFenix(StopsCreator):

    def add_stops_to_schedule(self, schedule, data):

        stops = data.stops

        # add all stops to GTFS
        for stop in stops.values():
            schedule.AddStop(
                lat=float(stop.lat),
                lng=float(stop.lon),
                name=stop.name,
                stop_id=str(stop.id)
            )
