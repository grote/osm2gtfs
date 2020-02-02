# coding=utf-8

from osm2gtfs.creators.agency_creator import AgencyCreator


class AgencyCreatorCiAbidjan(AgencyCreator):
    # In the case of Abidjan, the agency that is defined in the config.json
    # file is used as the default agency.
    # Any other agencies are input from the OSM data in trip_creator_ci_abidjan.py
    # based on the "operator" and "operator:website" tags

    def add_agency_to_feed(self, feed):
        feed.SetDefaultAgency(self.prepare_agency())
