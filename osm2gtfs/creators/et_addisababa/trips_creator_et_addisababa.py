# coding=utf-8

from datetime import timedelta, datetime

from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line

from transitfeed.trip import Trip

 
def time_string_to_minutes(time_string):
    (hours, minutes, seconds) = time_string.split(':')
    return int(hours) * 60 + int(minutes)

class TripsCreatorEtAddisababa(TripsCreator):
    service_weekday = None

    def add_trips_to_feed(self, feed, data):
        self.service_weekday = feed.GetDefaultServicePeriod()
        self.service_weekday.SetStartDate(
            self.config['feed_info']['start_date'])
        self.service_weekday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_weekday.SetWeekdayService(True)
        self.service_weekday.SetWeekendService(True)

        lines = data.routes
        for route_ref, line in sorted(lines.items()):
            if not isinstance(line, Line):
                continue
            print("Generating schedule for line: " + route_ref)

            flex_flag = None
            if 'route_master' in line.tags and line.tags['route_master'] == "light_rail":
                route_type = "Tram"
                route_suffix = " (Light Rail)"
            elif 'route_master' in line.tags and line.tags['route_master'] == "share_taxi":
                route_type = "Bus"
                route_suffix = " (Minibus)"
                flex_flag = 0
            else:
                route_type = "Bus"
                route_suffix = ""

            line_gtfs = feed.AddRoute(
                short_name=str(line.route_id).replace('Minibus', 'Tx'),
                long_name=line.name + route_suffix,
                # we change the route_long_name with the 'from' and 'to' tags
                # of the last route as the route_master name tag contains
                # the line code (route_short_name)
                route_type=route_type,
                route_id=line.osm_id)
            line_gtfs.agency_id = feed.GetDefaultAgency().agency_id
            line_gtfs.route_desc = ""
            line_gtfs.route_color = "1779c2"
            line_gtfs.route_text_color = "ffffff"

            route_index = 0
            itineraries = line.get_itineraries()
            for a_route in itineraries:
                trip_gtfs = line_gtfs.AddTrip(feed)
                trip_gtfs.shape_id = self._add_shape_to_feed(
                    feed, a_route.osm_id, a_route)
                trip_gtfs.direction_id = route_index % 2
                route_index += 1

                if a_route.fr and a_route.to:
                    trip_gtfs.trip_headsign = a_route.to
                    line_gtfs.route_long_name = a_route.fr + " ↔ " + a_route.to + route_suffix

                DEFAULT_ROUTE_FREQUENCY = 30
                DEFAULT_TRAVEL_TIME = 120

                frequency = None

                ROUTE_FREQUENCY = DEFAULT_ROUTE_FREQUENCY

                if "interval" in a_route.tags:
                    frequency = a_route.tags['interval']
                    try:
                        ROUTE_FREQUENCY = time_string_to_minutes(frequency)
                        if not ROUTE_FREQUENCY > 0:
                            print("frequency is invalid for route_master " + str(
                                line.osm_id))
                    except (ValueError, TypeError) as e:
                        print("frequency not a number for route_master " + str(
                                line.osm_id))

                trip_gtfs.AddFrequency(
                    "05:00:00", "22:00:00", ROUTE_FREQUENCY * 60)

                if 'duration' in a_route.tags:
                    try:
                        TRAVEL_TIME = time_string_to_minutes(a_route.tags['duration']);
                        if not TRAVEL_TIME > 0:
                            print("travel_time is invalid for route " + str(
                                    a_route.osm_id))
                            TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                    except (ValueError, TypeError) as e:
                        print("travel_time not a number / exception thrown for route with OSM ID " + str(
                                    a_route.osm_id))
                        TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                else:
                    TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                    print("WARNING: No duration set --- Using default travel time for route with OSM ID " +str(a_route.osm_id));

                for index_stop, a_stop in enumerate(a_route.stops):
                    stop_id = a_stop
                    departure_time = datetime(2008, 11, 22, 6, 0, 0)

                    if index_stop == 0:
                        trip_gtfs.AddStopTime(feed.GetStop(
                            str(stop_id)), stop_time=departure_time.strftime(
                                "%H:%M:%S"), continuous_pickup = flex_flag, continuous_drop_off = flex_flag, timepoint = 1)
                    elif index_stop == len(a_route.stops) - 1:
                        departure_time += timedelta(minutes=TRAVEL_TIME)
                        trip_gtfs.AddStopTime(feed.GetStop(
                            str(stop_id)), stop_time=departure_time.strftime(
                                "%H:%M:%S"), continuous_pickup = flex_flag, continuous_drop_off = flex_flag, timepoint = 1)
                    else:
                        trip_gtfs.AddStopTime(feed.GetStop(str(stop_id)), continuous_pickup = flex_flag, continuous_drop_off = flex_flag, timepoint = 0)

                for secs, stop_time, is_timepoint in trip_gtfs.GetTimeInterpolatedStops():
                    stop_time.continuous_pickup_flag = flex_flag
                    stop_time.continuous_drop_off_flag = flex_flag
                    if not is_timepoint:
                        stop_time.arrival_secs = secs
                        stop_time.departure_secs = secs
                        trip_gtfs.ReplaceStopTimeObject(stop_time)

                Helper.interpolate_stop_times(trip_gtfs)
