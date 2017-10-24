# coding=utf-8

from datetime import datetime

import transitfeed

from osm2gtfs.creators.trips_creator import TripsCreator


class TripsCreatorCrGam(TripsCreator):

    def add_trips_to_feed(self, feed, data):

        lines = data.get_routes()

        # line (osm rounte master | gtfs route)
        for line_id, line in lines.iteritems():
            # debug
            # print("DEBUG. procesando la línea:", line.name)

            # itinerary (osm route | non existent gtfs element)
            itineraries = line.get_itineraries()
            for itinerary in itineraries:
                # debug
                # print("DEBUG. procesando el itinerario", itinerary.name)

                # shape for itinerary
                shape_id = self._add_shape_to_feed(feed, itinerary.osm_id, itinerary)

                # service periods | días de opearación (c/u con sus horarios)
                operations = self._get_itinerary_operation(itinerary, data)

                # operation (gtfs service period)
                for operation in operations:
                    service_period = self._create_service_period(
                        feed, operation)

                    horarios = load_times(itinerary, data, operation)
                    estaciones = load_stations(itinerary, data, operation)

                    route = feed.GetRoute(line_id)

                    add_trips_for_route(feed, route, itinerary,
                                        service_period, shape_id, estaciones,
                                        horarios)
        return

    def _get_itinerary_operation(self, itinerary, data):
        """
            Retorna un iterable (lista) de objetos str, cada uno un 'keyword'
            del día o días de servicio, cuyos viajes (estaciones y horarios) se
            incluyen en el archivo de entrada.
        """

        start_date = self.config['feed_info']['start_date']
        enda_date = self.config['feed_info']['end_date']

        operations = []

        for operation in data.schedule["itinerario"][itinerary.route_id]:
            input_fr = operation["from"]
            input_to = operation["to"]
            if input_fr == itinerary.fr and input_to == itinerary.to:

                if operation["operacion"] == "weekday":
                    operations.append("weekday")

                if operation["operacion"] == "saturday":
                    operations.append("saturday")

                if operation["operacion"] == "sunday":
                    operations.append("sunday")
        return operations

    def _create_service_period(self, feed, operation):
        try:
            service = feed.GetServicePeriod(operation)
            if service is not None:
                return service
        except KeyError:
            print("INFO. There is no service_period for this service:",
                  operation, " therefore it will be created.")

        if operation == "weekday":
            service = transitfeed.ServicePeriod("weekday")
            service.SetWeekdayService(True)
            service.SetWeekendService(False)
        elif operation == "saturday":
            service = transitfeed.ServicePeriod("saturday")
            service.SetWeekdayService(False)
            service.SetWeekendService(False)
            service.SetDayOfWeekHasService(5, True)
        elif operation == "sunday":
            service = transitfeed.ServicePeriod("sunday")
            service.SetWeekdayService(False)
            service.SetWeekendService(False)
            service.SetDayOfWeekHasService(6, True)
        else:
            raise KeyError("uknown operation keyword")

        service.SetStartDate(self.config['feed_info']['start_date'])
        service.SetEndDate(self.config['feed_info']['end_date'])
        feed.AddServicePeriodObject(service)
        return feed.GetServicePeriod(operation)


def add_trips_for_route(feed, gtfs_route, itinerary, service_period,
                        shape_id, estaciones, horarios):
    # debug
    # print("DEBUG Adding trips for itinerary", itinerary.name)

    for viaje in horarios:
        indice = 0
        trip = gtfs_route.AddTrip(feed, headsign=itinerary.name,
                                  service_period=service_period)
        while indice < len(estaciones):
            tiempo = viaje[indice]
            estacion = estaciones[indice]
            if tiempo != "-":
                tiempo_parada = datetime.strptime(tiempo, "%H:%M")
                tiempo_parada = str(tiempo_parada.time())

                for stop in itinerary.stops:
                    if stop.name == estacion:
                        parada = feed.GetStop(str(stop.stop_id))
                        trip.AddStopTime(parada, stop_time=str(tiempo_parada))
                        continue

            # add empty attributes to make navitia happy
            trip.block_id = ""
            trip.wheelchair_accessible = ""
            trip.bikes_allowed = ""
            trip.shape_id = shape_id
            trip.direction_id = ""

            indice = indice + 1
    return


def load_stations(route, data, operation):

    stations = []
    for direction in data.schedule["itinerario"][route.route_id]:
        data_operation = direction["operacion"]
        if (direction["from"] == route.fr and
                direction["to"] == route.to and data_operation == operation):
            for station in direction["estaciones"]:
                stations = stations + [station]

    # debug
    # print("(json) estaciones encontradas: " + str(len(stations)))
    # for estacion in stations:
    #    print(estacion)

    return stations


def load_times(route, data, operation):

    # route_directions = data.schedule["itinerario"][route.ref]["horarios"]
    times = None

    for direction in data.schedule["itinerario"][route.route_id]:
        data_operation = direction["operacion"]
        if (direction["from"] == route.fr and
                direction["to"] == route.to and data_operation == operation):
            times = direction["horarios"]

    if times is None:
        print("debug: ruta va de", route.fr,
              "hacia", route.to)
        print("error consiguiendo los tiempos de la ruta")

    return times
