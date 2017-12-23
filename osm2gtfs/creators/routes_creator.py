# coding=utf-8

from osm2gtfs.core.helper import Helper


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
        routes = data.get_routes()

        # Loop through all routes
        for route_ref, route in sorted(routes.iteritems()):

            # Add route information
            gtfs_route = feed.AddRoute(
                route_id=self._define_route_id(route),
                route_type=self._define_route_type(route),
                short_name=self._define_short_name(route),
                long_name=self._define_long_name(route)
            )
            gtfs_route.agency_id = feed.GetDefaultAgency().agency_id
            gtfs_route.route_desc = self._define_route_description(route)
            gtfs_route.route_url = self._define_route_url(route)
            gtfs_route.route_color = self._define_route_color(route)
            gtfs_route.route_text_color = self._define_route_text_color(route)
        return

    def _define_route_id(self, route):
        """
        Returns the route_id for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.route_id

    def _define_short_name(self, route):
        """
        Returns the short name for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.route_id.encode('utf-8')

    def _define_long_name(self, route):
        """
        Returns the long name for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.name

    def _define_route_type(self, route):
        """
        Returns the route_id for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.route_type

    def _define_route_description(self, route):
        """
        Returns the route_desc for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.route_desc

    def _define_route_url(self, route):
        """
        Returns the route_url for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.osm_url

    def _define_route_color(self, route):
        """
        Returns the route_color for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return route.route_color[1:]

    def _define_route_text_color(self, route):
        """
        Returns the route_text_color for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        if route.route_text_color is None:
            # Auto calculate text color with high contrast
            route.route_text_color = Helper.calculate_color_of_contrast(
                route.route_color)

        return route.route_text_color[1:]
