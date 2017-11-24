# coding=utf-8

import json
import re
from datetime import datetime
from transitfeed import ServicePeriod


class TripsCreator(object):

    def __init__(self, config):
        self.config = config.data

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_trips_to_feed(self, feed, data):
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
        # print('Getting line information')
        lines = data.routes

        # Loop though all lines
        for line_id, line in lines.iteritems():
            # print('Loop for line_id', line_id)
            if line_id in timetable.excluded_lines:
                print('Ignoring line ID: ' + line_id)
                continue
            # Loop through all itineraries
            # print('Getting itinerary information from line', line.route_id)
            itineraries = line.get_itineraries()
            for itinerary in itineraries:
                # print('Loop for itinerary.route_id', itinerary.route_id)
                if itinerary.route_id.encode('utf-8') != line_id.encode('utf-8'):
                    raise RuntimeError('Itinerary route ID (' + itinerary.route_id + ') does not match Line route ID (' + line_id + ')')

                if itinerary.route_id not in timetable.lines:
                    print('Route ID of itinerary not found in timetable, skipping it', itinerary.route_id)
                    continue
                # Add itinerary shape to schedule, using osm_id instead of route_id to differ itinerary shapes
                # print('Adding itinerary shape to schedule', itinerary.osm_id)
                shape_id = TripsCreator.add_shape(schedule, itinerary.osm_id, itinerary)

                # Get operations for itinerary
                # print('Getting operations for itinerary')
                services = self._get_itinerary_services(timetable, itinerary)

                # Loop through all services
                for service in services:
                    # print('Loop for service', service)
                    # print('Create service period')
                    service_period = self._create_service_period(schedule, service)
                    # print('Load timetable')
                    gtfs_timetable = self._load_timetable(timetable, itinerary, service)
                    # print('Load stops')
                    stops = self._load_stops(timetable, itinerary, service)
                    # print('Get route from line id', line_id)
                    route = schedule.GetRoute(line_id)

                    # print('Add trips for route')
                    self._add_trips_for_route(schedule, route, itinerary,
                                              service_period, shape_id, stops,
                                              gtfs_timetable)
        return

    def _get_itinerary_services(self, timetable, itinerary):
        """
        Returns a list with services of given itinerary.
        """
        fr = itinerary.fr.encode('utf-8')
        to = itinerary.to.encode('utf-8')

        services = []

        for trip in timetable.lines[itinerary.route_id]:
            input_fr = trip["from"].encode('utf-8')
            input_to = trip["to"].encode('utf-8')
            if input_fr == fr and input_to == to:
                trip_services = trip["services"]
                for service in trip_services:
                    services.append(service.encode('utf-8'))
        return services

    def _create_service_period(self, schedule, service):
        try:
            gtfs_service = schedule.GetServicePeriod(service)
            if gtfs_service is not None:
                return gtfs_service
        except KeyError:
            pass

        if service == "Mo-Fr":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(False)
        elif service == "Mo-Sa":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(5, True)
        elif service == "Mo-Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(True)
        elif service == "Sa":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(5, True)
        elif service == "Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(6, True)
        elif service == "Sa-Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(True)
        elif re.search(r'^([0-9]{4})-?(1[0-2]|0[1-9])-?(3[01]|0[1-9]|[12][0-9])$', service):
            service = service.replace('-', '')
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetDateHasService(service)
        else:
            raise KeyError("Unknown service keyword: " + service)

        gtfs_service.SetStartDate(self.config['feed_info']['start_date'])
        gtfs_service.SetEndDate(self.config['feed_info']['end_date'])
        schedule.AddServicePeriodObject(gtfs_service)
        return schedule.GetServicePeriod(service)

    def _load_timetable(self, timetable, itinerary, service):
        times = None
        for trip in timetable.lines[itinerary.route_id]:
            fr = trip["from"].encode('utf-8')
            to = trip["to"].encode('utf-8')
            trip_services = trip["services"]
            if (fr == itinerary.fr.encode('utf-8') and
               to == itinerary.to.encode('utf-8') and service in trip_services):
                times = trip["times"]

        if times is None:
            print("Problems found with Itinerary from " +
                  itinerary.fr.encode('utf-8') + " to " +
                  itinerary.to.encode('utf-8')
                  )
            print("Couldn't load times from timetable.")
        return times

    def _load_stops(self, timetable, itinerary, service):
        stops = []
        for trip in timetable.lines[itinerary.route_id]:
            fr = trip["from"].encode('utf-8')
            to = trip["to"].encode('utf-8')
            trip_services = trip["services"]
            if (fr == itinerary.fr.encode('utf-8') and
               to == itinerary.to.encode('utf-8') and service in trip_services):
                for stop in trip["stations"]:
                    stops.append(unicode(stop))
        return stops

    def _add_trips_for_route(self, schedule, gtfs_route, itinerary, service_period,
                             shape_id, stops, gtfs_timetable):
        for trip in gtfs_timetable:
            gtfs_trip = gtfs_route.AddTrip(schedule, headsign=itinerary.name,
                                           service_period=service_period)
            # print('Count of stops', len(stops))
            # print('Count of itinerary.get_stops()', len(itinerary.get_stops()))
            # print('Stops', stops)
            for itinerary_stop in itinerary.get_stops():
                if itinerary_stop is None:
                    print('Itinerary stop is None. Seems to be a problem with OSM data. We should really fix that.')
                    print('itinerary route ID', itinerary.route_id)
                    print('itinerary stop', itinerary_stop)
                    continue
                gtfs_stop = schedule.GetStop(str(itinerary_stop.osm_id))
                time = "-"
                try:
                    time = trip[stops.index(itinerary_stop.name)]
                except ValueError:
                    pass
                if time != "-":
                    try:
                        time_at_stop = str(datetime.strptime(time, "%H:%M").time())
                    except ValueError:
                        print('Time seems invalid, skipping time', time)
                        break
                    gtfs_trip.AddStopTime(gtfs_stop, stop_time=time_at_stop)
                else:
                    try:
                        gtfs_trip.AddStopTime(gtfs_stop)
                    except Exception:
                        print('Skipping trip because no time were found', itinerary.route_id, stops, itinerary_stop.name)
                        break
                # add empty attributes to make navitia happy
                gtfs_trip.block_id = ""
                gtfs_trip.wheelchair_accessible = ""
                gtfs_trip.bikes_allowed = ""
                gtfs_trip.shape_id = shape_id
                gtfs_trip.direction_id = ""
            TripsCreator.interpolate_stop_times(gtfs_trip)

    @staticmethod
    def interpolate_stop_times(trip):
        """
        Interpolate stop_times, because Navitia does not handle this itself
        """
        try:
            for secs, stop_time, is_timepoint in trip.GetTimeInterpolatedStops():
                if not is_timepoint:
                    stop_time.arrival_secs = secs
                    stop_time.departure_secs = secs
                    trip.ReplaceStopTimeObject(stop_time)
        except ValueError as e:
            print(e)

    @staticmethod
    def add_shape(feed, route_id, osm_r):
        """
        create GTFS shape and return shape_id to add on GTFS trip
        """
        import transitfeed
        shape_id = str(osm_id)
        try:
            feed.GetShape(shape_id)
        except KeyError:
            shape = transitfeed.Shape(shape_id)
            for point in itinerary.shape:
                shape.AddPoint(
                    lat=float(point["lat"]), lon=float(point["lon"]))
            feed.AddShapeObject(shape)
        return shape_id
