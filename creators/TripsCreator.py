# coding=utf-8

import sys

class TripsCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_trips_to_schedule(self, schedule, data):
        raise NotImplementedError( "Should have implemented this" )
