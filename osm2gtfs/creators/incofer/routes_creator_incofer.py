# coding=utf-8

from osm2gtfs.creators.routes_creator import RoutesCreator


class RoutesCreatorIncofer(RoutesCreator):

    def _get_route_type(self, line):
        return "Tram"

    def _get_route_description(self, line):
        return "Esta línea está a prueba"

    def _get_route_color(self, line):
        return "ff0000"

    def _get_route_text_color(self, line):
        return "ffffff"
