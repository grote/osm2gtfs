# coding=utf-8


class RoutesCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_routes_to_schedule(self, schedule, data):
        return

        """
        route_id  # Required: From Line
        route_type  # Required: From Line

        route_short_name  # Required: To be generated from Line or Itinerary
        route_long_name	  # Required: To be generated from Line or Itinerary

        route_desc # From Line
        route_url  # From Line
        route_color: # From Line
        route_text_color  #From Line
        """
