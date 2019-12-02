# coding=utf-8

import collections
from datetime import timedelta, datetime
import transporthours
from transitfeed import ServicePeriod

from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line


class TripsCreatorCiAbidjan(TripsCreator):

    _DAYS_OF_WEEK = [ 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday' ]
    _DEFAULT_START_TIME = "05:00:00"
    _DEFAULT_END_TIME = "22:00:00"
    _DAY_ABBREVIATIONS = {
            'monday': 'Mo',
            'tuesday': 'Tu',
            'wednesday': 'We',
            'thursday': 'Th',
            'friday': 'Fr',
            'saturday': 'Sa',
            'sunday': 'Su'
        }
    _DEFAULT_HEADWAY = 30 # in minutes

    def _date_range(self, start, end):
        return self._DAY_ABBREVIATIONS[start] + '-' + self._DAY_ABBREVIATIONS[end]

    def _days_abbreviation_from_transport_hour(self, a_transport_hour):
        service_days = [ day_name for day_name in self._DAYS_OF_WEEK if day_name in a_transport_hour and a_transport_hour[day_name]]

        if not service_days:
            print('Transport_hour missing service days. Assuming 7 days a week.')
            service_days = self._DAYS_OF_WEEK

        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK):
            return self._date_range('monday', 'sunday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[:5]):
            return self._date_range('monday', 'friday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[:6]):
            return self._date_range('monday', 'saturday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[-2:]):
            return self._date_range('saturday', 'sunday')

        return ','.join([self._DAY_ABBREVIATIONS[day_name] for day_name in service_days])

    def _set_default_times(self, transport_hour):
        transport_hour['start_time'] = self._DEFAULT_START_TIME
        transport_hour['end_time'] = self._DEFAULT_END_TIME

    def _init_service_period(self, feed, hour):
        service_id = self._days_abbreviation_from_transport_hour(hour)
        service_period = ServicePeriod(id=service_id)
        service_period.SetStartDate(self.config['feed_info']['start_date'])
        service_period.SetEndDate(self.config['feed_info']['end_date'])
        for i,day_of_week in enumerate(self._DAYS_OF_WEEK):
            if (day_of_week in hour and hour[day_of_week]):
                service_period.SetDayOfWeekHasService(i)
        feed.AddServicePeriodObject(service_period)
        print("Created new service period " + service_id)
        return service_period

    def _process_transport_hours(self, feed, transport_hours_list):
        transport_hours_dict = {}
        for hour in transport_hours_list:
            service_id = self._days_abbreviation_from_transport_hour(hour)
            try:
                feed.GetServicePeriod(service_id)
            except KeyError:
                self._init_service_period(feed, hour)

            if "00:00:00" ==  hour['start_time'] and hour['end_time'] in ["00:00:00", "24:00:00"]:
                self._set_default_times(hour)

            if service_id in transport_hours_dict.keys():
                transport_hours_dict[service_id].append(hour)
            else:
                transport_hours_dict[service_id] = [hour]
        return transport_hours_dict

    def _init_default_hour(self):
        hour = { key:True for key in self._DAYS_OF_WEEK }
        self._set_default_times(hour)
        hour['headway'] = self._DEFAULT_HEADWAY * 60
        return hour

    def _init_agency(self, feed, agency_name):
        return feed.AddAgency(agency_name, None, self.config['agency']['agency_timezone'], agency_id=agency_name)

    def add_trips_to_feed(self, feed, data):
        lines = data.routes
        default_hour = self._init_default_hour()
        default_service_period = self._init_service_period(feed, default_hour)
        default_hours_dict = {
            default_service_period.service_id: [default_hour]
        }

        feed.SetDefaultServicePeriod(default_service_period)
        # This sets the default agency to the agency in config.json
        # Not ever used, but needed to avoid an error in feed.AddRoute() below
        feed.GetDefaultAgency()

        for route_ref, line in sorted(lines.iteritems()):
            if not isinstance(line, Line):
                continue
            # print("Generating schedule for line: " + route_ref)

            if 'operator' in line.tags and line.tags['operator']:
                agency_id = line.tags['operator']
                if agency_id == self.config['agency']['agency_name']:
                    agency_id = self.config['agency']['agency_id']
            else:
                agency_id = 'Unknown Agency'

            try:
                agency = feed.GetAgency(agency_id)
            except KeyError:
                agency = self._init_agency(feed, agency_id)

            line_gtfs = feed.AddRoute(
                short_name=str(line.route_id),
                long_name=line.name,
                # we change the route_long_name with the 'from' and 'to' tags
                # of the route as the route_master name tag contains
                # the line code (route_short_name)
                route_type=line.route_type,
                route_id=line.osm_id)
            line_gtfs.agency_id = agency.agency_id
            line_gtfs.route_desc = ""
            line_gtfs.route_color = "1779c2"
            line_gtfs.route_text_color = "ffffff"

            route_index = 0
            itineraries = line.get_itineraries()
            transport_hours = transporthours.main.Main()

            line_hours_list = transport_hours.tagsToGtfs(line.tags)
            line_hours_dict = self._process_transport_hours(feed, line_hours_list)

            for a_route in itineraries:
                itinerary_hours_list = transport_hours.tagsToGtfs(a_route.tags)

                if itinerary_hours_list:
                    itinerary_hours_dict = self._process_transport_hours(feed, itinerary_hours_list)
                elif line_hours_dict:
                    itinerary_hours_dict = line_hours_dict
                else:
                    itinerary_hours_dict = default_hours_dict

                for service_id,itinerary_hours in itinerary_hours_dict.items():
                    service_period = feed.GetServicePeriod(service_id)
                    trip_gtfs = line_gtfs.AddTrip(feed, service_period=service_period)
                    trip_gtfs.shape_id = self._add_shape_to_feed(feed, a_route.osm_id, a_route)
                    trip_gtfs.direction_id = route_index % 2
                    route_index += 1

                    if a_route.fr and a_route.to:
                        trip_gtfs.trip_headsign = a_route.to
                        line_gtfs.route_long_name = a_route.fr + " ↔ ".decode('utf-8') +  a_route.to

                    DEFAULT_TRAVEL_TIME = 120 # minutes

                    for itinerary_hour in itinerary_hours:
                        trip_gtfs.AddFrequency(itinerary_hour['start_time'], itinerary_hour['end_time'], itinerary_hour['headway'])

                    if 'duration' in a_route.tags:
                        print('duration', a_route.tags['duration'])

                    if 'travel_time' in a_route.tags:
                        try:
                            travel_time = int(a_route.tags['travel_time'])
                            if not travel_time > 0:
                                print("travel_time is invalid for route " + str(
                                        a_route.osm_id))
                                travel_time = DEFAULT_TRAVEL_TIME
                        except (ValueError, TypeError) as e:
                            print("travel_time not a number for route " + str(
                                        a_route.osm_id))
                            travel_time = DEFAULT_TRAVEL_TIME
                    else:
                        travel_time = DEFAULT_TRAVEL_TIME


                    for index_stop, a_stop in enumerate(a_route.stops):
                        stop_id = a_stop
                        departure_time = datetime(2008, 11, 22, 6, 0, 0)

                        if index_stop == 0:
                            trip_gtfs.AddStopTime(feed.GetStop(
                                str(stop_id)), stop_time=departure_time.strftime(
                                    "%H:%M:%S"))
                        elif index_stop == len(a_route.stops) - 1:
                            departure_time += timedelta(minutes=travel_time)
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
