# coding=utf-8

import json
from datetime import datetime

import transitfeed

from osm2gtfs.creators.trips_creator import TripsCreator


class TripsCreatorIncofer(TripsCreator):

    def add_trips_to_schedule(self, schedule, data):

        lines = data.routes

        # line (osm rounte master | gtfs route)
        for line_id, line in lines.iteritems():
            # debug
            # print("DEBUG. procesando la línea:", line.name)

            # itinerary (osm route | non existent gtfs element)
            for itinerary_id, itinerary in line.routes.iteritems():
                # debug
                # print("DEBUG. procesando el itinerario", itinerary.name)

                # shape for itinerary
                shape_id = TripsCreator.add_shape(schedule, itinerary_id, itinerary)

                # service periods | días de opearación (c/u con sus horarios)
                operations = self._get_itinerary_operation(itinerary)

                # operation (gtfs service period)
                for operation in operations:
                    service_period = self._create_service_period(
                        schedule, operation)

                    horarios = load_times(itinerary, operation)
                    estaciones = load_stations(itinerary, operation)

                    route = schedule.GetRoute(line_id)

                    add_trips_for_route(schedule, route, itinerary,
                                        service_period, shape_id, estaciones,
                                        horarios)
        return

    def _get_itinerary_operation(self, itinerary,
                                 filename='data/input_incofer.json'):
        """
            Retorna un iterable (lista) de objetos str, cada uno un 'keyword'
            del día o días de servicio, cuyos viajes (estaciones y horarios) se
            incluyen en el archivo de entrada.
        """

        input_file = open(filename)
        data = json.load(input_file)

        fr = itinerary.fr.encode('utf-8')
        to = itinerary.to.encode('utf-8')
        start_date = self.config['feed_info']['start_date']
        enda_date = self.config['feed_info']['end_date']

        operations = []

        for operation in data["itinerario"][itinerary.ref]:
            input_fr = operation["from"].encode('utf-8')
            input_to = operation["to"].encode('utf-8')
            if input_fr == fr and input_to == to:

                if operation["operacion"].encode('utf-8') == "weekday":
                    operations.append("weekday")

                if operation["operacion"].encode('utf-8') == "saturday":
                    operations.append("saturday")

                if operation["operacion"].encode('utf-8') == "sunday":
                    operations.append("sunday")
        return operations

    def _create_service_period(self, schedule, operation):
        try:
            service = schedule.GetServicePeriod(operation)
            if service is not None:
                return service
        except KeyError:
            print("INFO. No existe el service_period para la operación:",
                  operation, " por lo que será creado")

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
        schedule.AddServicePeriodObject(service)
        return schedule.GetServicePeriod(operation)


def add_trips_for_route(schedule, gtfs_route, itinerary, service_period,
                        shape_id, estaciones, horarios):
    # debug
    # print("DEBUG Adding trips for itinerary", itinerary.name)

    for viaje in horarios:
        indice = 0
        trip = gtfs_route.AddTrip(schedule, headsign=itinerary.name,
                                  service_period=service_period)
        while indice < len(estaciones):
            tiempo = viaje[indice]
            estacion = estaciones[indice]
            if tiempo != "-":
                tiempo_parada = datetime.strptime(tiempo, "%H:%M")
                tiempo_parada = str(tiempo_parada.time())

                for stop in itinerary.stops:
                    if stop.name == estacion:
                        parada = schedule.GetStop(str(stop.id))
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


def load_stations(route, operation, filename='data/input_incofer.json'):
    input_file = open(filename)
    input_data = json.load(input_file)

    stations = []
    for direction in input_data["itinerario"][route.ref]:
        fr = direction["from"].encode('utf-8')
        to = direction["to"].encode('utf-8')
        data_operation = direction["operacion"].encode('utf-8')
        if (fr == route.fr.encode('utf-8') and
           to == route.to.encode('utf-8') and data_operation == operation):
            for station in direction["estaciones"]:
                stations = stations + [station.encode('utf-8')]

    # debug
    # print("(json) estaciones encontradas: " + str(len(stations)))
    # for estacion in stations:
    #    print(estacion)

    return stations


def load_times(route, operation, filename='data/input_incofer.json'):
    input_file = open(filename)
    input_data = json.load(input_file)

    # route_directions = input_data["itinerario"][route.ref]["horarios"]
    times = None
    for direction in input_data["itinerario"][route.ref]:

        fr = direction["from"].encode('utf-8')
        to = direction["to"].encode('utf-8')
        data_operation = direction["operacion"].encode('utf-8')
        if (fr == route.fr.encode('utf-8') and
           to == route.to.encode('utf-8') and data_operation == operation):
            times = direction["horarios"]

    if times is None:
        print("debug: ruta va de", route.fr.encode('utf-8'),
              "hacia", route.to.encode('utf-8'))
        print("error consiguiendo los tiempos de la ruta")

    return times
