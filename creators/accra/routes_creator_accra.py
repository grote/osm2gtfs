# coding=utf-8

from creators.routes_creator import RoutesCreator


class RoutesCreatorAccra(RoutesCreator):

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
                route_type="Bus",
                route_id=line_ref)

            # AddRoute method add defaut agency as default
            route.agency_id = schedule.GetDefaultAgency().agency_id

            #route.route_desc = "Esta línea está a prueba"

            route.route_color = "ff0000"
            route.route_text_color = "ffffff"

            # debug
            print("información de la linea:", line.name, "agregada.")
        return
