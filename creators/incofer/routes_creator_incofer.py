# coding=utf-8

from creators.routes_creator import RoutesCreator


class RoutesCreatorIncofer(RoutesCreator):

    def add_routes_to_schedule(self, schedule, data):

        # Get routes information
        lines = data.get_routes()
        # debug
        # print("DEBUG: creando itinerarios a partir de", str(len(lines)),
        #      "lineas")

        # Loop through all lines (master_routes)
        for line_ref, line in sorted(lines.iteritems()):
            route = schedule.AddRoute(
                short_name=line.ref.encode('utf-8'),
                long_name=line.name,
                # TODO: infer transitfeed "route type" from OSM data
                route_type="Tram",
                route_id=line_ref)

            # AddRoute method add defaut agency as default
            route.agency_id = schedule.GetDefaultAgency().agency_id

            route.route_desc = "Esta línea está a prueba"

            # TODO: get route_url from OSM or other source.
            # url = "http://www.incofer.go.cr/tren-urbano-alajuela-rio-segundo"

            # line.route_url = url
            route.route_color = "ff0000"
            route.route_text_color = "ffffff"

            # debug
            # print("información de la linea:", line.name, "agregada.")
        return
