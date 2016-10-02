# coding=utf-8

import sys

class RoutesCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_routes_to_schedule(self, schedule):
        raise NotImplementedError( "Should have implemented this" )
