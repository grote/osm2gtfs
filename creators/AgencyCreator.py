# coding=utf-8

import sys
import transitfeed


class AgencyCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_agency_to_schedule(self, schedule):
        schedule.AddAgencyObject(self.prepare_agency())

    def prepare_agency(self):
        """
        Loads agency data from a json config file. The valid keys under the json
        "agency" object correspond to the transitfeed.Agency field names.

        Return a transitfeed.Agency object
        """
        fields = ['agency_name', 'agency_url', 'agency_timezone', 'agency_id', 'agency_lang',
                  'agency_phone', 'agency_fare_url']
        data_dict = {}
        for field_name in fields:
            if field_name in self.config["agency"]:
                field_value = self.config["agency"][field_name]
                if field_value is not None and field_value != "":
                    data_dict[field_name] = field_value
            else:
                sys.stderr.write("Warning: Key '" + field_name + "' was not found in the config file.")

        agency = transitfeed.Agency(field_dict=data_dict)

        if not agency.Validate():
            sys.stderr.write("Error: Agency data is invalid.")
            # TODO error handling based on a exception
            # raise AttributeError('Agency data in config file in not valid.')

        return agency
