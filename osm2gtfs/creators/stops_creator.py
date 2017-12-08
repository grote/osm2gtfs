# coding=utf-8

import transitfeed


class StopsCreator(object):

    def __init__(self, config):
        self.config = config

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_stops_to_feed(self, feed, data):
        """
        This function adds the Stops from the data to the GTFS feed.
        It also unites stops in stations based on stop_areas in OpenStreetMap.
        """
        all_stops = data.get_stops()
        regular_stops = all_stops['regular']
        parent_stations = all_stops['stations']

        # Loop through all stations and prepare stops
        for station in parent_stations.values():

            # Add station to feed as stop
            gtfs_stop_id = self._add_stop_to_feed(station, feed)

            # Loop through member stops of a station
            for member in station.get_members():

                # Set parent station of each member Stop
                regular_stops[member].set_parent_station(gtfs_stop_id)

        # Loop through regular stops
        for stop in regular_stops.values():
            # Add stop to feed
            self._add_stop_to_feed(stop, feed)

    def get_gtfs_stop_id(self, stop):
        """
        This function returns the GTFS stop id to be used for a stop.
        It can be overridden by custom cretors to change how stop_ids are made
        up.

        :return gtfs_stop_id: A string with the stop_id for use in the GTFS
        """

        if "gtfs_id" in stop.tags:
            #  Use a GTFS stop_id coming from OpenStreetMap data
            return stop.tags['gtfs_id']
        else:
            # Use a GTFS stop_id mathing to OpenStreetMap objects
            return stop.osm_type + "/" + str(stop.osm_id)

    def _add_stop_to_feed(self, stop, feed):
        """
        This function adds a Stop or Station object as a stop to GTFS.
        It can be overridden by custom cretors to change how stop_ids are made
        up.

        :return stop_id: A string with the stop_id in the GTFS
        """
        try:
            parent_station = stop.get_parent_station()
        except AttributeError as e:
            parent_station = ""

        field_dict = {'stop_id': self.get_gtfs_stop_id(stop),
                      'stop_name': stop.name,
                      'stop_lat': float(stop.lat),
                      'stop_lon': float(stop.lon),
                      'location_type': stop.location_type,
                      'parent_station': parent_station
                      }

        # Add stop to GTFS object
        feed.AddStopObject(transitfeed.Stop(field_dict=field_dict))

        # Return the stop_id of the stop added
        return field_dict['stop_id']
