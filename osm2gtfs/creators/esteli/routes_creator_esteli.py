# coding=utf-8

import math
import webcolors
from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorEsteli(RoutesCreator):

    def _define_route_color(self, route):
        """
        Overriden to support color names
        """
        if not route.route_color == '#FFFFFF':
            route.route_color = webcolors.name_to_hex(route.route_color)
        return route.route_color[1:]

    def _define_route_text_color(self, route):
        """
        Overriden to support automatic guessing
        """

        # Prepare the color information
        color = route.route_color
        if color[0] == '#':
            color = color[1:]

        # Slice RGB and convert to decimal numbers
        red, green, blue = (int(color[0:2], 16), int(color[2:4], 16),
                            int(color[4:6], 16))

        # Calculate the route_text_color; based on
        # http://www.nbdtech.com/Blog/archive/2008/04/27/Calculating-the-Perceived-Brightness-of-a-Color.aspx
        brightness = math.sqrt(
            red * red * .241 + green * green * .691 + blue * blue * .068)
        route_text_color = "ffffff" if brightness <= 130 else "000000"

        return route_text_color
