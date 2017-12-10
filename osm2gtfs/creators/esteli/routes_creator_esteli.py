# coding=utf-8

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
        return self._get_complementary_color(route.route_color)

    def _get_complementary_color(self, color):
        """
        Returns complementary RGB color
        Source: https://stackoverflow.com/a/38478744
        """
        if color[0] == '#':
            color = color[1:]
        rgb = (color[0:2], color[2:4], color[4:6])
        comp = ['%02X' % (255 - int(a, 16)) for a in rgb]
        return ''.join(comp)
