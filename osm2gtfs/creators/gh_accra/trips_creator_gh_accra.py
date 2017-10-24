# coding=utf-8

from datetime import timedelta, datetime

from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line


class TripsCreatorGhAccra(TripsCreator):
    service_weekday = None

    def add_trips_to_feed(self, feed, data):
        self.service_weekday = feed.GetDefaultServicePeriod()
        self.service_weekday.SetStartDate(
            self.config['feed_info']['start_date'])
        self.service_weekday.SetEndDate(self.config['feed_info']['end_date'])
        self.service_weekday.SetWeekdayService(True)
        self.service_weekday.SetWeekendService(True)

        lines = data.routes
        for route_ref, line in sorted(lines.iteritems()):
            if not isinstance(line, Line):
                continue
            print("Generating schedule for line: " + route_ref)

            line_gtfs = feed.AddRoute(
                short_name=str(line.route_id),
                long_name=line.name,
                # we change the route_long_name with the 'from' and 'to' tags
                # of the last route as the route_master name tag contains
                # the line code (route_short_name)
                route_type="Bus",
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
                    line_gtfs.route_long_name = a_route.fr.decode(
                        'utf8') + " ↔ ".decode(
                        'utf8') + a_route.to.decode('utf8')

                DEFAULT_ROUTE_FREQUENCY = 30
                DEFAULT_TRAVEL_TIME = 120

                frequency = None
                if "frequency" in line.tags:
                    frequency = line.tags['frequency']
                try:
                    ROUTE_FREQUENCY = int(frequency)
                    if not ROUTE_FREQUENCY > 0:
                        print("frequency is invalid for route_master " + str(
                            line.osm_id))
                        ROUTE_FREQUENCY = DEFAULT_ROUTE_FREQUENCY
                except (ValueError, TypeError) as e:
                    print("frequency not a number for route_master " + str(
                            line.osm_id))
                    ROUTE_FREQUENCY = DEFAULT_ROUTE_FREQUENCY
                trip_gtfs.AddFrequency(
                    "05:00:00", "22:00:00", ROUTE_FREQUENCY * 60)
                if 'travel_time' in a_route.tags:
                    try:
                        TRAVEL_TIME = int(a_route.tags['travel_time'])
                        if not TRAVEL_TIME > 0:
                            print("travel_time is invalid for route " + str(
                                    a_route.osm_id))
                            TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                    except (ValueError, TypeError) as e:
                        print("travel_time not a number for route " + str(
                                    a_route.osm_id))
                        TRAVEL_TIME = DEFAULT_TRAVEL_TIME
                else:
                    TRAVEL_TIME = DEFAULT_TRAVEL_TIME

                for index_stop, a_stop in enumerate(a_route.stops):
                    stop_id = a_stop.split('/')[-1]
                    departure_time = datetime(2008, 11, 22, 6, 0, 0)

                    if index_stop == 0:
                        trip_gtfs.AddStopTime(feed.GetStop(
                            str(stop_id)), stop_time=departure_time.strftime(
                                "%H:%M:%S"))
                    elif index_stop == len(a_route.stops) - 1:
                        departure_time += timedelta(minutes=TRAVEL_TIME)
                        trip_gtfs.AddStopTime(feed.GetStop(
                            str(stop_id)), stop_time=departure_time.strftime(
                                "%H:%M:%S"))
                    else:
                        trip_gtfs.AddStopTime(feed.GetStop(str(stop_id)))

                for secs, stop_time, is_timepoint in trip_gtfs.GetTimeInterpolatedStops():
                    if not is_timepoint:
                        stop_time.arrival_secs = secs
                        stop_time.departure_secs = secs
                        trip_gtfs.ReplaceStopTimeObject(stop_time)

                Helper.interpolate_stop_times(trip_gtfs)
