# coding=utf-8

from osm2gtfs.creators.schedule_creator import ScheduleCreator


class ScheduleCreatorGhAccra(ScheduleCreator):

    def add_schedule_to_data(self, data):
        # Don't use any schedule source
        data.schedule = None
