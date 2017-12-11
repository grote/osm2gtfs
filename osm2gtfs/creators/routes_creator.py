# coding=utf-8


class RoutesCreator(object):

    def __init__(self, config):
        self.config = config.data

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_routes_to_feed(self, feed, data):
        """
        This function adds the routes from the data to the GTFS feed.
        """
        # Get route information
        lines = data.get_routes()

        # Loop through all lines
        for line_ref, line in sorted(lines.iteritems()):

            # Add route information
            route = feed.AddRoute(
                route_id=line_ref,
                route_type=line.route_type,
                short_name=line.route_id.encode('utf-8'),
                long_name=line.name
            )
            route.agency_id = feed.GetDefaultAgency().agency_id
            route.route_desc = line.route_desc
            route.route_url = line.route_url
            route.route_color = line.route_color
            route.route_text_color = line.route_text_color
        return
