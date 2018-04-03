# coding=utf-8

import logging
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
            gtfs_stop_id = self._add_stop_to_feed(stop, feed)

    def remove_unused_stops_from_feed(self, feed):
        """
        This function removes every stop which is not used by any trip
        from the final GTFS.
        It is called after the whole GTFS creation inside the main program.
        """
        removed = 0
        for stop_id, stop in feed.stops.items():
            if stop.location_type == 0 and not stop.GetTrips(feed):
                removed += 1
                del feed.stops[stop_id]
        if removed == 0:
            pass
        elif removed == 1:
            logging.info("Removed 1 unused stop")
        else:
            logging.info("Removed %d unused stops", removed)

    def _add_stop_to_feed(self, stop, feed):
        """
        This function adds a single Stop or Station object as a stop to GTFS.
        It can be overridden by custom creators to change how stop_ids are made
        up.

        :return stop_id: A string with the stop_id in the GTFS
        """
        try:
            parent_station = stop.get_parent_station()
        except AttributeError:
            parent_station = None

        # Send stop_id creation through overridable function
        gtfs_stop_id = self._define_stop_id(stop)

        # Save defined stop_id to the object for further use in other creators
        stop.set_stop_id(gtfs_stop_id)

        # Set stop name
        stop_name = self._define_stop_name(stop)

        # Collect all data together for the stop creation
        field_dict = {'stop_id': self._define_stop_id(stop),
                      'stop_name': stop_name,
                      'stop_lat': float(stop.lat),
                      'stop_lon': float(stop.lon),
                      'location_type': stop.location_type,
                      'parent_station': parent_station
                      }

        # Add stop to GTFS object
        feed.AddStopObject(transitfeed.Stop(field_dict=field_dict))

        if type(stop_name).__name__ == "unicode":
            stop_name = stop_name.encode('utf-8')

        logging.info("Added stop: %s - %s", stop_name, stop.osm_url)

        # Return the stop_id of the stop added
        return field_dict['stop_id']

    def _define_stop_id(self, stop):
        """
        This function returns the GTFS stop id to be used for a stop.
        It can be overridden by custom creators to change how stop_ids are made
        up.

        :return stop_id: A string with the stop_id for use in the GTFS
        """

        #  Use a GTFS stop_id coming from OpenStreetMap data
        if "ref:gtfs" in stop.tags:
            stop_id = stop.tags['ref:gtfs']
        elif "ref" in stop.tags:
            stop_id = stop.tags['ref']

        # Use a GTFS stop_id matching to OpenStreetMap objects
        else:
            stop_id = stop.osm_type + "/" + str(stop.osm_id)

        return stop_id

    def _define_stop_name(self, stop):
        """
        Returns the stop name for the use in the GTFS feed.
        Can be easily overridden in any creator.
        """
        return stop.name
