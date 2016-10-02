# coding=utf-8

import os
import sys
import json
import transitfeed
from datetime import datetime
from creators_default.TripsCreator import TripsCreator
from osmhelper.osm_routes import Route, RouteMaster

DEBUG_ROUTE = "104"

WEEKDAY = "Dias Úteis"
SATURDAY = "Sábado"
SUNDAY = "Domingo"

class TripsCreatorFenix(TripsCreator):

    def add_trips_to_schedule(self, schedule, data):

        service_weekday = schedule.NewDefaultServicePeriod()
        service_weekday.SetStartDate(self.config['feed_info']['start_date'])
        service_weekday.SetEndDate(self.config['feed_info']['end_date'])
        service_weekday.SetWeekdayService(True)
        service_weekday.SetWeekendService(False)

        service_saturday = schedule.NewDefaultServicePeriod()
        service_saturday.SetStartDate(self.config['feed_info']['start_date'])
        service_saturday.SetEndDate(self.config['feed_info']['end_date'])
        service_saturday.SetWeekdayService(False)
        service_saturday.SetWeekendService(False)
        service_saturday.SetDayOfWeekHasService(5, True)

        service_sunday = schedule.NewDefaultServicePeriod()
        service_sunday.SetStartDate(self.config['feed_info']['start_date'])
        service_sunday.SetEndDate(self.config['feed_info']['end_date'])
        service_sunday.SetWeekdayService(False)
        service_sunday.SetWeekendService(False)
        service_sunday.SetDayOfWeekHasService(6, True)

        routes = data.routes

        # Get Fenix data from JSON file
        json_data = []
        with open('data/linhas.json') as f:
            for line in f:
                json_data.append(json.loads(line))
        linhas = json_data[0]['data']

        blacklist = ['10200', '12400', '328', '466', '665']
        # Try to find OSM routes in Fenix data
        for route_ref, route in sorted(routes.iteritems()):
            found = False
            for linha in linhas:
                if route_ref == linha:
                    route.add_linha(linhas[linha])
                    if isinstance(route, RouteMaster):
                        for sub_route in route.routes.values():
                            sub_route.add_linha(linhas[linha])
                    found = True
                    break

            if not found and route_ref not in blacklist:
                sys.stderr.write("Route not found in Fenix data: " + str(route) + "\n")
                blacklist.append(route_ref)

        # delete missing routes from OSM data
        for route_ref in blacklist:
            if route_ref in routes:
                del routes[route_ref]

        # add trips for all routes
        for route_ref, route in sorted(routes.iteritems()):
            line = schedule.AddRoute(
                short_name=route.ref,
                long_name=route.name,
                route_type="Bus")
            line.agency_id = schedule.GetDefaultAgency().agency_id
            line.route_desc = "TEST DESCRIPTION"
            line.route_url = "http://www.consorciofenix.com.br/horarios?q=" + str(route.ref)
            line.route_color = "1779c2"
            line.route_text_color = "ffffff"

            weekday = {}
            saturday = {}
            sunday = {}

            for day in route.horarios:
                sday = day.encode('utf-8')

                if sday.startswith(WEEKDAY):
                    weekday[sday.replace(WEEKDAY + ' - Saída ', '')] = route.horarios[day]
                elif sday.startswith(SATURDAY):
                    saturday[sday.replace(SATURDAY + ' - Saída ', '')] = route.horarios[day]
                elif sday.startswith(SUNDAY):
                    sunday[sday.replace(SUNDAY + ' - Saída ', '')] = route.horarios[day]
                else:
                    raise RuntimeError("Unknown day in Fenix data: " + day)

            self.add_trips_by_day(schedule, line, service_weekday, route, weekday, WEEKDAY)
            self.add_trips_by_day(schedule, line, service_saturday, route, saturday, SATURDAY)
            self.add_trips_by_day(schedule, line, service_sunday, route, sunday, SUNDAY)

    def add_trips_by_day(self, schedule, line, service, route, horarios, day):
        # check if we even have service
        if horarios is None or len(horarios) == 0:
            return

        if isinstance(route, RouteMaster):
            # recurse into "Ida" and "Volta" routes
            for sub_route in route.routes.values():
                self.add_trips_by_day(schedule, line, service, sub_route, horarios, day)
            return

        # have at least two stops
        if len(route.stops) < 2:
            sys.stderr.write("Skipping Route, has no stops: " + str(route) + "\n")
            return

        # check if we have a match for the first stop
        key = route.match_first_stops(horarios.keys())

        if key is None:
            # Do not print debug output here, because already done in route.match_first_stops()
            return

        if route.ref == DEBUG_ROUTE:
            print "\n\n\n" + str(route)
            print day + " - " + key

        # get shape id
        shape_id = str(route.id)
        try:
            schedule.GetShape(shape_id)
        except KeyError:
            shape = transitfeed.Shape(shape_id)
            for point in route.shape:
                shape.AddPoint(lat=float(point["lat"]), lon=float(point["lon"]))
            schedule.AddShapeObject(shape)

        if len(horarios) > 1 and not route.has_proper_master():
            sys.stderr.write("Route should have a master: " + str(route) + "\n")

        for time_group in horarios[key]:
            for time_point in time_group:
                # parse first departure time
                start_time = datetime.strptime(time_point[0], "%H:%M")
                start_time = str(start_time.time())

                # calculate last arrival time for GTFS
                start_sec = transitfeed.TimeToSecondsSinceMidnight(start_time)
                factor = 1
                if len(horarios) > 1 and not route.has_proper_master():
                    # since this route has only one instead of two trips, double the duration
                    factor = 2
                end_sec = start_sec + route.duration.seconds * factor
                end_time = transitfeed.FormatSecondsSinceMidnight(end_sec)

                # save options
                opts = time_point[1]

                trip = line.AddTrip(schedule, headsign=route.name, service_period=service)
                # add empty attributes to make navitia happy
                trip.block_id = ""
                trip.wheelchair_accessible = ""
                trip.bikes_allowed = ""
                trip.shape_id = shape_id
                trip.direction_id = ""
                if route.ref == DEBUG_ROUTE:
                    print "ADD TRIP " + str(trip.trip_id) + ":"
                self.add_trip_stops(schedule, trip, route, start_time, end_time, opts)

                # interpolate times, because Navitia can not handle this itself
                self.interpolate_stop_times(trip)


    def add_trip_stops(self, schedule, trip, route, start_time, end_time, opts):

        if isinstance(route, Route):
            i = 1
            for stop in route.stops:
                if i == 1:
                    # timepoint="1" (Times are considered exact)
                    trip.AddStopTime(schedule.GetStop(str(stop.id)), stop_time=start_time)
                    if route.ref == DEBUG_ROUTE:
                        print "START: " + start_time + " at " + str(stop)
                elif i == len(route.stops):
                    # timepoint="0" (Times are considered approximate)
                    trip.AddStopTime(schedule.GetStop(str(stop.id)), stop_time=end_time)
                    if route.ref == DEBUG_ROUTE:
                        print "END: " + end_time + " at " + str(stop)
                else:
                    # timepoint="0" (Times are considered approximate)
                    trip.AddStopTime(schedule.GetStop(str(stop.id)))
    #                print "INTER: " + str(stop)
                i += 1


    def interpolate_stop_times(self, trip):
        for secs, stop_time, is_timepoint in trip.GetTimeInterpolatedStops():
            if not is_timepoint:
                stop_time.arrival_secs = secs
                stop_time.departure_secs = secs
                trip.ReplaceStopTimeObject(stop_time)
