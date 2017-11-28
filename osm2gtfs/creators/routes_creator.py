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
        route_id  # Required: From Line
        route_type  # Required: From Line

        route_short_name  # Required: To be generated from Line or Itinerary
        route_long_name  # Required: To be generated from Line or Itinerary

        route_desc # From Line
        route_url  # From Line
        route_color # From Line
        route_text_color  # From Line
        """
        # Get route information
        lines = data.get_routes()

        # Loop through all lines
        for line_ref, line in sorted(lines.iteritems()):

            # Add route information
            route = schedule.AddRoute(
                route_id=line_ref,
                route_type=self._get_route_type(line),
                short_name=line.route_id.encode('utf-8'),
                long_name=line.name
            )

            route.agency_id = schedule.GetDefaultAgency().agency_id

            route.route_desc = self._get_route_description(line)
            route.route_url = self._get_route_url(line)
            route.route_color = self._get_route_color(line)
            route.route_text_color = self._get_route_text_color(line)
        return

    def _get_route_type(self, line):
        return line.route_type

    def _get_route_description(self, line):
        return line.route_desc

    def _get_route_url(self, line):
        return line.route_url

    def _get_route_color(self, line):
        return line.route_color

    def _get_route_text_color(self, line):
        return line.route_text_color
