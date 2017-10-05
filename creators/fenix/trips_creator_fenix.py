# coding=utf-8

import sys
import json
import re
import transitfeed
from datetime import timedelta, datetime
from creators.trips_creator import TripsCreator
from core.osm_routes import Route, RouteMaster

DEBUG_ROUTE = ""
BLACKLIST = [
    '10200', '12400',
    '328', '466',  # Don't exist in Fenix data, should be removed from OSM
    '665',  # needs ponto final fixing and master in OSM
    '464'  # TODO handle special route variants (B)
]

STOP_REGEX = re.compile('(TICAN|TISAN|TICEN|TITRI|TILAG|TIRIO|TISAC).*')

WEEKDAY = "Dias Úteis"
SATURDAY = "Sábado"
SUNDAY = "Domingo"

NO_DURATION = "não encontrado"


class TripsCreatorFenix(TripsCreator):

    def __init__(self, config):
        super(TripsCreatorFenix, self).__init__(config)

        self.start_date = datetime.strptime(self.config['feed_info']['start_date'], "%Y%m%d")

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
        routes = data.routes
        schedule.AddServicePeriodObject(self.service_weekday)
        schedule.AddServicePeriodObject(self.service_saturday)
        schedule.AddServicePeriodObject(self.service_sunday)

        # Get Fenix data from JSON file
        json_data = []
        with open('data/linhas.json') as f:
            for line in f:
                json_data.append(json.loads(line))
        linhas = json_data[0]['data']

        # Try to find OSM routes in Fenix data
        for route_ref, route in sorted(routes.iteritems()):
            if route_ref not in BLACKLIST and route_ref in linhas:
                linha = linhas[route_ref]
                route.name = linha['nome'].encode('utf-8')
                route.last_update = datetime.strptime(linha['alterado_em'], "%d/%m/%Y")
                # save duration
                if linha['tempo_de_percurso'].encode('utf-8') == NO_DURATION:
                    sys.stderr.write(
                        "ERROR: Route has no duration in Fenix data: " + str(route) + "\n")
                    continue
                duration_str = linha['tempo_de_percurso'].replace('aproximado', '')
                (hours, tmp, minutes) = duration_str.partition(':')
                route.set_duration(timedelta(hours=int(hours), minutes=int(minutes)))
                self.add_route(schedule, route, linha['horarios'], linha['operacoes'])
            elif route_ref not in BLACKLIST:
                sys.stderr.write("Route not found in Fenix data: " + str(route) + "\n")

    def add_route(self, schedule, route, horarios, operacoes):
        line = schedule.AddRoute(
            short_name=route.ref,
            long_name=route.name.decode('utf8'),
            route_type="Bus")
        line.agency_id = schedule.GetDefaultAgency().agency_id
        line.route_desc = "TEST DESCRIPTION"
        line.route_url = "http://www.consorciofenix.com.br/horarios?q=" + str(route.ref)
        line.route_color = "1779c2"
        line.route_text_color = "ffffff"

        weekday = {}
        saturday = {}
        sunday = {}

        for day in horarios:
            sday = day.encode('utf-8')
            if sday.startswith(WEEKDAY):
                weekday[sday.replace(WEEKDAY + ' - Saída ', '')] = horarios[day]
            elif sday.startswith(SATURDAY):
                saturday[sday.replace(SATURDAY + ' - Saída ', '')] = horarios[day]
            elif sday.startswith(SUNDAY):
                sunday[sday.replace(SUNDAY + ' - Saída ', '')] = horarios[day]
            else:
                raise RuntimeError("Unknown day in Fenix data: " + day)

        # check that each route has the same exceptions, so they are in fact global
        if self.exceptions is None:
            self.exceptions = operacoes
        elif self.exceptions != operacoes:
            raise RuntimeError("Route has different service exceptions: " + str(route))

        # schedule exceptions
        for o in operacoes:
            date = datetime.strptime(o["data"], "%Y-%m-%d")
            day = o["tipo"].encode('utf-8')

            # only include exceptions within service period
            if date < self.start_date:
                continue

            service = self.get_exception_service_period(schedule, date, day)
            if day == SATURDAY:
                self.add_trips_by_day(schedule, line, service, route, saturday, SATURDAY)
            elif day == SUNDAY:
                self.add_trips_by_day(schedule, line, service, route, sunday, SUNDAY)
            else:
                sys.stderr.write("ERROR: Unknown day %s\n" % day)

        # regular schedule
        self.add_trips_by_day(schedule, line, self.service_weekday, route, weekday, WEEKDAY)
        self.add_trips_by_day(schedule, line, self.service_saturday, route, saturday, SATURDAY)
        self.add_trips_by_day(schedule, line, self.service_sunday, route, sunday, SUNDAY)

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
        key = self.match_first_stops(route, horarios.keys())

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

                # TODO handle options
                # opts = time_point[1]

                trip = line.AddTrip(schedule, headsign=route.name, service_period=service)
                # add empty attributes to make navitia happy
                trip.block_id = ""
                trip.wheelchair_accessible = ""
                trip.bikes_allowed = ""
                trip.shape_id = shape_id
                trip.direction_id = ""
                if route.ref == DEBUG_ROUTE:
                    print "ADD TRIP " + str(trip.trip_id) + ":"
                self.add_trip_stops(schedule, trip, route, start_time, end_time)

                # interpolate times, because Navitia can not handle this itself
                TripsCreator.interpolate_stop_times(trip)

    def get_exception_service_period(self, schedule, date, day):
        date_string = date.strftime("%Y%m%d")
        if date.weekday() <= 4:
            self.service_weekday.SetDateHasService(date_string, False)
        elif date.weekday() == 5:
            self.service_saturday.SetDateHasService(date_string, False)
        elif date.weekday() == 6:
            self.service_sunday.SetDateHasService(date_string, False)

        service_id = date_string + "_" + day
        if service_id in schedule.service_periods:
            service = schedule.GetServicePeriod(service_id)
        else:
            print("Created new schedule exception for %s with ID %s" % (str(date), service_id))
            service = transitfeed.ServicePeriod(service_id)
            service.SetStartDate(date_string)
            service.SetEndDate(date_string)
            service.SetDayOfWeekHasService(date.weekday())
            schedule.AddServicePeriodObject(service)
        return service

    @staticmethod
    def match_first_stops(route, sim_stops):
        # get the first stop of the route
        stop = route.get_first_stop()

        # normalize its name
        stop.name = TripsCreatorFenix.normalize_stop_name(stop.name)

        # get first stop from relation 'from' tag
        alt_stop_name = route.get_first_alt_stop()
        alt_stop_name = TripsCreatorFenix.normalize_stop_name(alt_stop_name.encode('utf-8'))

        # trying to match first stop from OSM with SIM
        for o_sim_stop in sim_stops:
            sim_stop = TripsCreatorFenix.normalize_stop_name(o_sim_stop)
            if sim_stop == stop.name:
                return o_sim_stop
            elif sim_stop == alt_stop_name:
                return o_sim_stop

        # print some debug information when no stop match found
        sys.stderr.write(str(route) + "\n")
        sys.stderr.write(str(sim_stops) + "\n")
        sys.stderr.write("-----\n")
        sys.stderr.write("OSM Stop: '" + stop.name + "'\n")
        sys.stderr.write("OSM ALT Stop: '" + alt_stop_name + "'\n")
        for sim_stop in sim_stops:
            sim_stop = TripsCreatorFenix.normalize_stop_name(sim_stop)
            sys.stderr.write("SIM Stop: '" + sim_stop + "'\n")
        print
        return None

    @staticmethod
    def normalize_stop_name(old_name):
        name = STOP_REGEX.sub(r'\1', old_name)
        name = name.replace('Terminal de Integração da Lagoa da Conceição', 'TILAG')
        name = name.replace('Terminal Centro', 'TICEN')
        name = name.replace('Terminal Rio Tavares', 'TIRIO')
        name = name.replace('Itacurubi', 'Itacorubi')
        return name

    @staticmethod
    def add_trip_stops(schedule, trip, route, start_time, end_time):
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
