# coding=utf-8

import sys
import json
import re
from datetime import timedelta, datetime
from creators.trips_creator import TripsCreator
from core.osm_routes import Route, RouteMaster



class TripsCreatorAccra(TripsCreator):

    def add_trips_to_schedule(self, schedule, data):
        self.service_weekday = schedule.GetDefaultServicePeriod()
        self.service_weekday.SetStartDate(self.config['feed_info']['start_date'])
        self.service_weekday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_weekday.SetWeekdayService(True)
        self.service_weekday.SetWeekendService(True)

        lines = data.routes
        for route_ref, line in sorted(lines.iteritems()):
            if type(line).__name__ != "RouteMaster":
                continue
            line_gtfs = schedule.AddRoute(
                short_name=line.ref,
                long_name=line.name.decode('utf8'),
                route_type="Bus",
                route_id=line.id)
            line_gtfs.agency_id = schedule.GetDefaultAgency().agency_id
            line_gtfs.route_desc = ""
            line_gtfs.route_color = "1779c2"
            line_gtfs.route_text_color = "ffffff"

            route_index = 0
            for a_route_ref, a_route in line.routes.iteritems():
                trip_gtfs = line_gtfs.AddTrip(schedule)
                trip_gtfs.shape_id = TripsCreator.add_shape(schedule, a_route_ref, a_route)
                trip_gtfs.trip_headsign = a_route.to
                trip_gtfs.direction_id = route_index % 2
                route_index += 1
                DEFAULT_ROUTE_FREQUENCY = 30
                DEFAULT_TRAVEL_TIME = 120

                try:
                    ROUTE_FREQUENCY = int(line.frequency)
                    if not ROUTE_FREQUENCY > 0 :
                        print("frequency is invalid for route_master " + str(line.id))
                        ROUTE_FREQUENCY = DEFAULT_ROUTE_FREQUENCY
                except Exception as e:
                    print("frequency not a number for route_master " + str(line.id))
                    ROUTE_FREQUENCY = DEFAULT_ROUTE_FREQUENCY
                trip_gtfs.AddFrequency("05:00:00", "22:00:00", ROUTE_FREQUENCY * 60)

                try:
                    TRAVEL_TIME = int(a_route.travel_time)
                    if not TRAVEL_TIME > 0 :
                        print("travel_time is invalid for route " + str(lia_routene.id))
                        TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                except Exception as e:
                    print("travel_time not a number for route " + str(a_route.id))
                    TRAVEL_TIME = DEFAULT_TRAVEL_TIME

                for index_stop, a_stop in enumerate(a_route.stops) :
                    stop_id = a_stop.split('/')[-1]
                    departure_time = datetime(2008, 11, 22, 6, 0, 0)

                    if index_stop == 0 :
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)), stop_time=departure_time.strftime("%H:%M:%S"))
                    elif index_stop == len(a_route.stops) -1 :
                        departure_time += timedelta(minutes = TRAVEL_TIME)
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)), stop_time=departure_time.strftime("%H:%M:%S"))
                    else :
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)))

                for secs, stop_time, is_timepoint in trip_gtfs.GetTimeInterpolatedStops():
                    if not is_timepoint:
                        stop_time.arrival_secs = secs
                        stop_time.departure_secs = secs
                        trip_gtfs.ReplaceStopTimeObject(stop_time)

                TripsCreator.interpolate_stop_times(trip_gtfs)
