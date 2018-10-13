# coding=utf-8

import sys
import re
import logging
from datetime import timedelta, datetime
import transitfeed
from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line, Itinerary, Stop

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


class TripsCreatorBrFlorianopolis(TripsCreator):

    def __init__(self, config):
        super(TripsCreatorBrFlorianopolis, self).__init__(config)

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

    def add_trips_to_feed(self, feed, data):
        routes = data.get_routes()
        feed.AddServicePeriodObject(self.service_weekday)
        feed.AddServicePeriodObject(self.service_saturday)
        feed.AddServicePeriodObject(self.service_sunday)

        # Get Fenix schedule data from source file
        linhas = data.schedule['data']

        # Try to find OSM routes in Fenix data
        for route_ref, route in sorted(routes.iteritems()):

            print("Generating schedule for line: " + route_ref)

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
                route.duration = timedelta(hours=int(hours), minutes=int(minutes))
                self.add_route(feed, route, linha['horarios'], linha['operacoes'])
            elif route_ref not in BLACKLIST:
                sys.stderr.write(
                    "Route not found in Fenix data: [" + route.route_id + "] " + str(
                        route.osm_url) + "\n")

    def add_route(self, feed, route, horarios, operacoes):
        line = feed.AddRoute(
            short_name=route.route_id,
            long_name=route.name.decode('utf8'),
            route_type="Bus")
        line.agency_id = feed.GetDefaultAgency().agency_id
        line.route_desc = "TEST DESCRIPTION"
        line.route_url = "http://www.consorciofenix.com.br/horarios?q=" + str(route.route_id)
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
            previous_exceptions = set()
            for ex in self.exceptions:
                previous_exceptions.add(ex['data'])
            this_exceptions = set()
            for ex in operacoes:
                this_exceptions.add(ex['data'])
            logging.error("Route has different service exceptions.")
            logging.error(
                "Missing service exceptions: %s", str(previous_exceptions - this_exceptions))
            logging.error(
                "Additional service exceptions: %s", str(this_exceptions - previous_exceptions))

        # schedule exceptions
        for o in operacoes:
            date = datetime.strptime(o["data"], "%Y-%m-%d")
            day = o["tipo"].encode('utf-8')

            # only include exceptions within service period
            if date < self.start_date:
                continue

            service = self.get_exception_service_period(feed, date, day)
            if day == SATURDAY:
                self.add_trips_by_day(feed, line, service, route, saturday, SATURDAY)
            elif day == SUNDAY:
                self.add_trips_by_day(feed, line, service, route, sunday, SUNDAY)
            else:
                sys.stderr.write("ERROR: Unknown day %s\n" % day)

        # regular schedule
        self.add_trips_by_day(feed, line, self.service_weekday, route, weekday, WEEKDAY)
        self.add_trips_by_day(feed, line, self.service_saturday, route, saturday, SATURDAY)
        self.add_trips_by_day(feed, line, self.service_sunday, route, sunday, SUNDAY)

    def add_trips_by_day(self, feed, line, service, route, horarios, day):

        # check if we even have service
        if horarios is None or len(horarios) == 0:
            return

        if isinstance(route, Line):
            # recurse into "Ida" and "Volta" routes
            for sub_route in route.get_itineraries():
                sub_route.duration = route.duration
                self.add_trips_by_day(feed, line, service, sub_route, horarios, day)
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

        if route.route_id == DEBUG_ROUTE:
            print "\n\n\n" + str(route)
            print day + " - " + key

        # get shape id
        shape_id = str(route.route_id)
        try:
            feed.GetShape(shape_id)
        except KeyError:
            shape = transitfeed.Shape(shape_id)
            for point in route.shape:
                shape.AddPoint(lat=float(point["lat"]), lon=float(point["lon"]))
            feed.AddShapeObject(shape)

        if len(horarios) > 1 and route.line is None:
            sys.stderr.write(
                "Route should have a master: [" + route.route_id + "] " + str(
                    route.osm_url) + "\n")

        for time_group in horarios[key]:
            for time_point in time_group:
                # parse first departure time
                start_time = datetime.strptime(time_point[0], "%H:%M")
                start_time = str(start_time.time())

                # calculate last arrival time for GTFS
                start_sec = transitfeed.TimeToSecondsSinceMidnight(start_time)
                factor = 1
                if len(horarios) > 1 and route.line is None:
                    # since this route has only one instead of two trips, double the duration
                    factor = 2
                end_sec = start_sec + route.duration.seconds * factor
                end_time = transitfeed.FormatSecondsSinceMidnight(end_sec)

                # TODO handle options
                # opts = time_point[1]

                trip = line.AddTrip(feed, headsign=route.name, service_period=service)
                # add empty attributes to make navitia happy
                trip.block_id = ""
                trip.wheelchair_accessible = ""
                trip.bikes_allowed = ""
                trip.shape_id = shape_id
                trip.direction_id = ""
                if route.route_id == DEBUG_ROUTE:
                    print "ADD TRIP " + str(trip.trip_id) + ":"
                self.add_trip_stops(feed, trip, route, start_time, end_time)

                # interpolate times, because Navitia can not handle this itself
                Helper.interpolate_stop_times(trip)

    def get_exception_service_period(self, feed, date, day):
        date_string = date.strftime("%Y%m%d")
        if date.weekday() <= 4:
            self.service_weekday.SetDateHasService(date_string, False)
        elif date.weekday() == 5:
            self.service_saturday.SetDateHasService(date_string, False)
        elif date.weekday() == 6:
            self.service_sunday.SetDateHasService(date_string, False)

        service_id = date_string + "_" + day
        if service_id in feed.service_periods:
            service = feed.GetServicePeriod(service_id)
        else:
            print("Created new schedule exception for %s with ID %s" % (str(date), service_id))
            service = transitfeed.ServicePeriod(service_id)
            service.SetStartDate(date_string)
            service.SetEndDate(date_string)
            service.SetDayOfWeekHasService(date.weekday())
            feed.AddServicePeriodObject(service)
        return service

    def match_first_stops(self, route, sim_stops, ):
        # get the first stop of the route
        stop = route.stops[0]

        # normalize its name
        stop.name = self.normalize_stop_name(stop.name)

        # get first stop from relation 'from' tag
        if 'from' in route.tags:
            alt_stop_name = route.tags['from']
        else:
            alt_stop_name = ""
        alt_stop_name = self.normalize_stop_name(alt_stop_name)

        # trying to match first stop from OSM with SIM
        for o_sim_stop in sim_stops:
            sim_stop = self.normalize_stop_name(o_sim_stop)
            if sim_stop == stop.name:
                return o_sim_stop
            elif sim_stop == alt_stop_name:
                return o_sim_stop

        # print some debug information when no stop match found
        sys.stderr.write(str(route.osm_url) + "\n")
        sys.stderr.write(str(sim_stops) + "\n")
        sys.stderr.write("-----\n")
        sys.stderr.write("OSM Stop: '" + stop.name + "'\n")
        sys.stderr.write("OSM ALT Stop: '" + alt_stop_name + "'\n")
        for sim_stop in sim_stops:
            sim_stop = self.normalize_stop_name(sim_stop)
            sys.stderr.write("SIM Stop: '" + sim_stop + "'\n")
        print
        return None

    @staticmethod
    def normalize_stop_name(old_name):
        name = STOP_REGEX.sub(r'\1', old_name)
        if type(name).__name__ == 'str':
            name = name.decode('utf-8')
        name = name.replace('Terminal de Integração da Lagoa da Conceição'.decode('utf-8'), 'TILAG')
        name = name.replace('Terminal Centro', 'TICEN')
        name = name.replace('Terminal Rio Tavares', 'TIRIO')
        name = name.replace('Itacurubi', 'Itacorubi')
        return name

    @staticmethod
    def add_trip_stops(feed, trip, route, start_time, end_time):
        if isinstance(route, Itinerary):
            i = 1
            for stop in route.stops:
                # TODO this check shouldn't be necessary if only valid stops were included
                if isinstance(stop, Stop):
                    if i == 1:
                        # timepoint="1" (Times are considered exact)
                        if route.route_id == DEBUG_ROUTE:
                            logging.info("START: %s at %s", start_time, str(stop))
                        trip.AddStopTime(feed.GetStop(str(stop.stop_id)), stop_time=start_time)
                    elif i == len(route.stops):
                        # timepoint="0" (Times are considered approximate)
                        if route.route_id == DEBUG_ROUTE:
                            logging.info("END: %s at %s", end_time, str(stop))
                        trip.AddStopTime(feed.GetStop(str(stop.stop_id)), stop_time=end_time)
                    else:
                        # timepoint="0" (Times are considered approximate)
                        if route.route_id == DEBUG_ROUTE:
                            logging.info("INTER: %s", str(stop))
                        trip.AddStopTime(feed.GetStop(str(stop.stop_id)))
                i += 1
