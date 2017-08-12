# coding=utf-8

import sys
import json
import re
import transitfeed
from datetime import timedelta, datetime
from creators.trips_creator import TripsCreator
from core.osm_routes import Route, RouteMaster

class TripsCreatorAccra(TripsCreator):

    def __init__(self, config):
        super(TripsCreatorAccra, self).__init__(config)

        self.service_weekday = transitfeed.ServicePeriod("weekday")
        self.service_weekday.SetStartDate(self.config['feed_info']['start_date'])
        self.service_weekday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_weekday.SetWeekdayService(True)
        self.service_weekday.SetWeekendService(False)

        self.service_saturday = transitfeed.ServicePeriod("saturday")
        self.service_saturday.SetStartDate(self.config['feed_info']['start_date'])
        self.service_saturday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_saturday.SetWeekdayService(False)
        self.service_saturday.SetWeekendService(False)
        self.service_saturday.SetDayOfWeekHasService(5, True)

        self.service_sunday = transitfeed.ServicePeriod("sunday")
        self.service_sunday.SetStartDate(self.config['feed_info']['start_date'])
        self.service_sunday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_sunday.SetWeekdayService(False)
        self.service_sunday.SetWeekendService(False)
        self.service_sunday.SetDayOfWeekHasService(6, True)

        self.exceptions = None

    def add_trips_to_schedule(self, schedule, data):
        lines = data.routes
        schedule.AddServicePeriodObject(self.service_weekday)
        schedule.AddServicePeriodObject(self.service_saturday)
        schedule.AddServicePeriodObject(self.service_sunday)

        ## TODO
        # gtfs_trip.AddStopTime(gtfs_stop, stop_time = departure_time.strftime("%H:%M:%S"))

        for route_ref, line in sorted(lines.iteritems()):
            if type(line).__name__ != "RouteMaster":
                continue
            print (line.name)
            line_gtfs = schedule.AddRoute(
                short_name=line.ref,
                long_name=line.name.decode('utf8'),
                route_type="Bus")
            line_gtfs.agency_id = schedule.GetDefaultAgency().agency_id
            line_gtfs.route_desc = "TEST DESCRIPTION"
            line_gtfs.route_url = ""
            line_gtfs.route_color = "1779c2"
            line_gtfs.route_text_color = "ffffff"

            for a_route_ref, a_route in line.routes.iteritems():
                trip_gtfs = line_gtfs.AddTrip(schedule)
                ROUTE_FREQUENCY = 18 #TODO
                trip_gtfs.AddFrequency("06:00:00", "21:00:00", ROUTE_FREQUENCY * 60)

                for index_stop, a_stop in enumerate(a_route.stops) :
                    stop_id = a_stop.split('/')[-1]
                    print (a_stop)
                    departure_time = datetime(2008, 11, 22, 6, 0, 0)
                    #trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)), stop_time=departure_time.strftime("%H:%M:%S"))

                    if index_stop == 0 :
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)), stop_time=departure_time.strftime("%H:%M:%S"))
                    elif index_stop == len(a_route.stops) -1 :
                        departure_time += timedelta(hours = 1) #TODO
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)), stop_time=departure_time.strftime("%H:%M:%S"))
                    else :
                        trip_gtfs.AddStopTime(schedule.GetStop(str(stop_id)))

                for secs, stop_time, is_timepoint in trip_gtfs.GetTimeInterpolatedStops():
                    if not is_timepoint:
                        print('>>>> Interpolation au milieu')
                        stop_time.arrival_secs = secs
                        stop_time.departure_secs = secs
                        trip_gtfs.ReplaceStopTimeObject(stop_time)

                # interpolate times, because Navitia can not handle this itself
                self.interpolate_stop_times(trip_gtfs)


    @staticmethod
    def interpolate_stop_times(trip):
        for secs, stop_time, is_timepoint in trip.GetTimeInterpolatedStops():
            if not is_timepoint:
                stop_time.arrival_secs = secs
                stop_time.departure_secs = secs
                trip.ReplaceStopTimeObject(stop_time)
