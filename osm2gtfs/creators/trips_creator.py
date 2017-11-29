# coding=utf-8

import json
from datetime import datetime
from transitfeed import ServicePeriod


class TripsCreator(object):

    def __init__(self, config):
        self.config = config
        self.timetable_file = 'data/timetable.json'
        if 'timetable' in self.config:
            # TODO: Check if URL -> download
            self.timetable_file = self.config['timetable']

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_trips_to_schedule(self, schedule, data):
        """
        route_id  # Required: From Line
        service_id  # Required: To be generated
        trip_id  # Required: To be generated

        trip_headsign # Itinerary "to"
        direction_id  # Order of tinieraries in Line object
        wheelchair_accessible  # Itinerary "wheelchair_accessible"
        bikes_allowed # Itinerary "bikes_allowed"
        trip_short_name  # To be avoided!
        block_id  # To be avoided!
        """
        # Get route information
        lines = data.routes

        # Loop though all lines
        for line_id, line in lines.iteritems():

            # Loop through all itineraries
            itineraries = line.get_itineraries()
            for itinerary_id, itinerary in itineraries:

                # Add itinerary shape to schedule
                shape_id = TripsCreator.add_shape(schedule, itinerary_id, itinerary)

                # Get operations for itinerary
                services = self._get_itinerary_services(itinerary)

                # Loop through all services
                for service in services:
                    service_period = self._create_service_period(schedule, service)
                    timetable = self._load_timetable(itinerary, service)
                    stops = self._load_stops(itinerary, service)
                    route = schedule.GetRoute(line_id)

                    self._add_trips_for_route(schedule, route, itinerary,
                                              service_period, shape_id, stops,
                                              timetable)
        return

    @staticmethod
    def interpolate_stop_times(trip):
        """
        interpolate stop_times, because Navitia does not handle this itself by now
        """
        for secs, stop_time, is_timepoint in trip.GetTimeInterpolatedStops():
            if not is_timepoint:
                stop_time.arrival_secs = secs
                stop_time.departure_secs = secs
                trip.ReplaceStopTimeObject(stop_time)

    @staticmethod
    def add_shape(schedule, itinerary_id, itinerary):
        """
        create GTFS shape and return shape_id to add on GTFS trip
        """
        import transitfeed
        shape_id = str(itinerary_id)
        try:
            schedule.GetShape(shape_id)
        except KeyError:
            shape = transitfeed.Shape(shape_id)
            for point in itinerary.shape:
                shape.AddPoint(
                    lat=float(point["lat"]), lon=float(point["lon"]))
            schedule.AddShapeObject(shape)
        return shape_id

    def _get_itinerary_services(self, itinerary):
        """
        Returns a list with services of given itinerary.
        """
        with open(self.timetable_file, 'r', encoding='utf8') as f:
            data = json.load(f)

            fr = itinerary.fr.encode('utf-8')
            to = itinerary.to.encode('utf-8')

            services = []

            for service in data["itineraries"][itinerary.route_id]:
                input_fr = service["from"].encode('utf-8')
                input_to = service["to"].encode('utf-8')
                if input_fr == fr and input_to == to:
                    services.append(service["service"].encode('utf-8'))
            return services

    def _create_service_period(self, schedule, service):
        try:
            gtfs_service = schedule.GetServicePeriod(service)
            if gtfs_service is not None:
                return gtfs_service
        except KeyError:
            pass

        if service == "Mo-Fr":
            gtfs_service = ServicePeriod("weekday")
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(False)
        elif service == "Sa":
            gtfs_service = ServicePeriod("saturday")
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(5, True)
        elif service == "So":
            gtfs_service = ServicePeriod("sunday")
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(6, True)
        elif service == "Sa-So":
            gtfs_service = ServicePeriod("weekend")
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(True)
        else:
            raise KeyError("Unknown service keyword: " + service)

        gtfs_service.SetStartDate(self.config['feed_info']['start_date'])
        gtfs_service.SetEndDate(self.config['feed_info']['end_date'])
        schedule.AddServicePeriodObject(gtfs_service)
        return schedule.GetServicePeriod(gtfs_service)

    def _load_timetable(self, itinerary, service):
        with open(self.timetable_file, 'r', encoding='utf8') as f:
            data = json.load(f)

            times = None
            for direction in data["lines"][itinerary.route_id]:

                fr = direction["from"].encode('utf-8')
                to = direction["to"].encode('utf-8')
                data_service = direction["service"].encode('utf-8')
                if (fr == itinerary.fr.encode('utf-8') and
                   to == itinerary.to.encode('utf-8') and data_service == service):
                    times = direction["times"]

            if times is None:
                print("Problems found with Itinerary from " +
                      itinerary.fr.encode('utf-8') + " to " +
                      itinerary.to.encode('utf-8')
                      )
                print("Couldn't load times from timetable.")
            return times

    def _load_stops(self, itinerary, service):
        with open(self.timetable_file, 'r', encoding='utf8') as f:
            data = json.load(f)

            stops = []
            for direction in data["itineraries"][itinerary.route_id]:
                fr = direction["from"].encode('utf-8')
                to = direction["to"].encode('utf-8')
                data_service = direction["service"].encode('utf-8')
                if (fr == itinerary.fr.encode('utf-8') and
                   to == itinerary.to.encode('utf-8') and data_service == service):
                    for stop in direction["stops"]:
                        stops.append(stop.encode('utf-8'))
        return stops

    def _add_trips_for_route(self, schedule, gtfs_route, itinerary, service_period,
                             shape_id, stops, timetable):

        for trip in timetable:
            gtfs_trip = gtfs_route.AddTrip(schedule, headsign=itinerary.name,
                                           service_period=service_period)
            for stop_id, stop in stops:
                time = trip[stop_id]
                if time != "-":
                    time_at_stop = datetime.strptime(time, "%H:%M").time()

                    for itinerary_stop in itinerary.stops:
                        if itinerary_stop.name == stop:
                            gtfs_stop = schedule.GetStop(str(stop.id))
                            gtfs_trip.AddStopTime(gtfs_stop, stop_time=str(time_at_stop))
                            continue

                # add empty attributes to make navitia happy
                trip.block_id = ""
                trip.wheelchair_accessible = ""
                trip.bikes_allowed = ""
                trip.shape_id = shape_id
                trip.direction_id = ""
        return
