# coding=utf-8
import logging
import collections
from datetime import timedelta, datetime
import transporthours
from transitfeed import ServicePeriod

from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line


class TripsCreatorCiAbidjan(TripsCreator):

    _DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday',
                     'thursday', 'friday', 'saturday', 'sunday']
    _DEFAULT_SCHEDULE = {
        'opening_hours': 'Mo-Su,PH 05:00-22:00',
        'interval': '01:00'
    }
    _DAY_ABBREVIATIONS = {
        'monday': 'Mo',
        'tuesday': 'Tu',
        'wednesday': 'We',
        'thursday': 'Th',
        'friday': 'Fr',
        'saturday': 'Sa',
        'sunday': 'Su'
    }
    _DEFAULT_TRIP_DURATION = 120  # minutes

    def _service_id_from_transport_hour(self, a_transport_hour):
        service_days = [day_name for day_name in self._DAYS_OF_WEEK
                        if day_name in a_transport_hour and a_transport_hour[day_name]]

        if not service_days:
            logging.warning(
                'Transport_hour missing service days. Assuming 7 days a week.')
            service_days = self._DAYS_OF_WEEK

        def date_range(start, end):
            return self._DAY_ABBREVIATIONS[start] + '-' + self._DAY_ABBREVIATIONS[end]

        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK):
            return date_range('monday', 'sunday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[:5]):
            return date_range('monday', 'friday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[:6]):
            return date_range('monday', 'saturday')
        if collections.Counter(service_days) == collections.Counter(self._DAYS_OF_WEEK[-2:]):
            return date_range('saturday', 'sunday')

        return ','.join([self._DAY_ABBREVIATIONS[day_name] for day_name in service_days])

    def _init_service_period(self, feed, hour):
        service_id = self._service_id_from_transport_hour(hour)
        service_period = ServicePeriod(id=service_id)
        service_period.SetStartDate(self.config['feed_info']['start_date'])
        service_period.SetEndDate(self.config['feed_info']['end_date'])
        for i, day_of_week in enumerate(self._DAYS_OF_WEEK):
            if (day_of_week in hour and hour[day_of_week]):
                service_period.SetDayOfWeekHasService(i)
        feed.AddServicePeriodObject(service_period)
        return service_period

    def _group_hours_by_service_period(self, feed, transport_hours_list):
        transport_hours_dict = {}
        for hour in transport_hours_list:
            service_id = self._service_id_from_transport_hour(hour)
            try:
                feed.GetServicePeriod(service_id)
            except KeyError:
                self._init_service_period(feed, hour)

            if service_id in transport_hours_dict.keys():
                transport_hours_dict[service_id].append(hour)
            else:
                transport_hours_dict[service_id] = [hour]
        return transport_hours_dict

    def add_trips_to_feed(self, feed, data):
        transport_hours = transporthours.main.Main()
        default_hours = transport_hours.tagsToGtfs(self._DEFAULT_SCHEDULE)

        default_service_period = self._init_service_period(
            feed, default_hours[0])
        feed.SetDefaultServicePeriod(default_service_period)
        default_hours_dict = self._group_hours_by_service_period(
            feed, default_hours)

        lines = data.routes

        default_agency = feed.GetDefaultAgency()

        for route_id, line in sorted(lines.items()):
            if not isinstance(line, Line):
                continue
            logging.info("Generating schedule for line: %s",  route_id)
            if 'network' in line.tags and line.tags['network']:
                try:
                    agency = feed.GetAgency(line.tags['network'])
                except KeyError:
                    agency = feed.AddAgency(line.tags['network'],
                                            default_agency.agency_url,
                                            default_agency.agency_timezone,
                                            agency_id=line.tags['network'])
                    logging.info("Added agency: %s", agency.agency_name)
                    if not agency.Validate():
                        logging.error("Agency data not valid for %s in line",
                                      line.tags['network'])
                if 'operator:website' in line.tags and line.tags['operator:website']:
                    agency.agency_url = line.tags['operator:website']
                    if not agency.Validate():
                        logging.error(
                            'Url is not valid for agency: %s',  agency.agency_url)
            else:
                agency = default_agency

            line_gtfs = feed.AddRoute(
                short_name=str(line.route_id),
                long_name=line.name,
                route_type=line.route_type,
                route_id=line.osm_id)
            line_gtfs.agency_id = agency.agency_id
            line_gtfs.route_desc = ""
            line_gtfs.route_color = "1779c2"
            line_gtfs.route_text_color = "ffffff"

            route_index = 0
            itineraries = line.get_itineraries()

            line_hours_list = transport_hours.tagsToGtfs(line.tags)
            line_hours_dict = self._group_hours_by_service_period(
                feed, line_hours_list)

            for a_route in itineraries:
                itinerary_hours_list = transport_hours.tagsToGtfs(a_route.tags)

                if itinerary_hours_list:
                    itinerary_hours_dict = self._group_hours_by_service_period(
                        feed, itinerary_hours_list)
                elif line_hours_dict:
                    itinerary_hours_dict = line_hours_dict
                else:
                    itinerary_hours_dict = default_hours_dict
                    logging.warning("schedule is missing, using default")
                    logging.warning(
                        " Add opening_hours & interval tags in OSM - %s", line.osm_url)

                for service_id, itinerary_hours in itinerary_hours_dict.items():
                    service_period = feed.GetServicePeriod(service_id)
                    trip_gtfs = line_gtfs.AddTrip(
                        feed, service_period=service_period)
                    trip_gtfs.shape_id = self._add_shape_to_feed(
                        feed, a_route.osm_id, a_route)
                    trip_gtfs.direction_id = route_index % 2
                    route_index += 1

                    if a_route.fr and a_route.to:
                        trip_gtfs.trip_headsign = a_route.to
                        if line_gtfs.route_short_name:
                            # The line.name in the OSM data (route_long_name in the GTFS)
                            # is in the following format:
                            # '{transport mode} {route_short_name if any} :
                            # {A terminus} ↔ {The other terminus}'
                            # But it is good practice to not repeat the route_short_name
                            # in the route_long_name,
                            # so we abridge the route_long_name here if needed
                            line_gtfs.route_long_name =  "{} ↔ {}".format(a_route.fr, a_route.to)

                    for itinerary_hour in itinerary_hours:
                        trip_gtfs.AddFrequency(
                            itinerary_hour['start_time'], itinerary_hour['end_time'],
                            itinerary_hour['headway'])

                    if 'duration' in a_route.tags:
                        try:
                            travel_time = int(a_route.tags['duration'])
                            if not travel_time > 0:
                                logging.warning(
                                    "trip duration %s is invalid - %s",
                                    travel_time,
                                    a_route.osm_url)
                                travel_time = self._DEFAULT_TRIP_DURATION
                        except (ValueError, TypeError) as e:
                            logging.warning(
                                "trip duration %s is not a number - %s",
                                a_route.tags['duration'],
                                a_route.osm_url)
                            travel_time = self._DEFAULT_TRIP_DURATION
                    else:
                        travel_time = self._DEFAULT_TRIP_DURATION
                        logging.warning(
                            "trip duration is missing, using default (%s min)", travel_time)
                        logging.warning(
                            " Add a duration tag in OSM - %s", a_route.osm_url)

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
