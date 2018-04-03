# coding=utf-8

import sys
import logging
import json


class ScheduleCreator(object):
    """
    The ScheduleCreator loads, validates and prepares configuration data from
    the schedule source file for further use in the script.

    More information about the standard schedule format:
    https://github.com/grote/osm2gtfs/wiki/Schedule

    """
    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_schedule_to_data(self, data):
        """
        This function adds the loaded schedule to the global data object.
        """
        schedule = self._load_schedule_source()
        data.schedule = self._prepare_schedule(schedule)

    def _load_schedule_source(self):
        """
        This function loads and verifies the content of the file.
        In the standard schedule creator it assumes a json file. This function
        can be overridden to support any type of file format or structure.
        """

        schedule_source = self.config.get_schedule_source()

        if schedule_source is None:
            logging.error("No schedule source found.")
            sys.exit(0)

        else:
            try:
                schedule = json.loads(schedule_source)
            except ValueError, e:
                logging.error('Schedule file is invalid.')
                logging.error(e)
                sys.exit(0)

        return schedule

    def _prepare_schedule(self, schedule):
        """
        This function prepares (if needed) the schedule for further use.
        """
        return schedule
