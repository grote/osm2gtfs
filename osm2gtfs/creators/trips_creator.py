# coding=utf-8

import re
from datetime import datetime
import transitfeed
from transitfeed import ServicePeriod
from osm2gtfs.core.helper import Helper


class TripsCreator(object):

    def __init__(self, config):
        self.config = config.data

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_trips_to_feed(self, feed, data):
        """
        This function generates and adds trips to the GTFS feed.

        It is the place where geographic information and schedule is
        getting joined to produce a routable GTFS.
        """
        all_trips_count = 0

        # Go though all lines
        for line_id, line in data.routes.iteritems():

            print("\nGenerating schedule for line: [" + str(
                line_id) + "] - " + line.name)

            # Loop through it's itineraries
            itineraries = line.get_itineraries()
            for itinerary in itineraries:
                trips_count = 0

                # Verify data before proceeding
                if self._verify_data(data.schedule, line, itinerary):

                    # Prepare itinerary's trips and schedule
                    prepared_trips = self._prepare_trips(feed, data.schedule,
                                                         itinerary)

                    # Add itinerary shape to feed.
                    shape_id = self._add_shape_to_feed(
                        feed, "relation/" + str(itinerary.osm_id), itinerary)

                    # Add trips of each itinerary to the GTFS feed
                    for trip_builder in prepared_trips:

                        trip_builder['all_stops'] = data.get_stops()
                        trips_count += self._add_itinerary_trips(
                            feed, itinerary, line, trip_builder, shape_id)

                # Print out status messge about added trips
                print(" Itinerary: [" + str(itinerary.route_id) + "] " +
                      itinerary.to.encode("utf-8") + " (added " + str(
                          trips_count) + " trips, serving " + str(
                              len(itinerary.get_stops())) + " stops) - " +
                      itinerary.osm_url)
                all_trips_count += trips_count

        print("\nTotal of added trips to this GTFS: " +
              str(all_trips_count) + "\n\n")
        return

    def _prepare_trips(self, feed, schedule, itinerary):
        """
        Prepare information necessary to generate trips

        :return trips: List of different objects
        """

        # Define a list with service days of given itinerary.
        services = []
        for trip in schedule['lines'][itinerary.route_id]:
            input_fr = trip["from"]
            input_to = trip["to"]
            if input_fr == itinerary.fr and input_to == itinerary.to:
                trip_services = trip["services"]
                for service in trip_services:
                    services.append(service)

        if not services:
            print(" Warning: From and to values didn't match with schedule.")

        # Loop through all service days
        trips = []
        for service in services:

            # Define GTFS feed service period
            service_period = self._create_gtfs_service_period(feed, service)

            # Get schedule for this itinierary's trips
            trips_schedule = self._load_itinerary_schedule(schedule,
                                                           itinerary, service)

            # Get the stops, which are listed in the schedule
            scheduled_stops = self._load_scheduled_stops(
                schedule, itinerary, service)

            # Prepare a trips builder container with useful data for later
            trips.append({'service_period': service_period,
                          'stops': scheduled_stops, 'schedule': trips_schedule})
        return trips

    def _verify_data(self, schedule, line, itinerary):
        """
        Verifies line, itinerary and it's schedule data for trip creation
        """

        # Check if itinerary and line are having the same reference
        if itinerary.route_id != line.route_id:
            print("Warning: The route id of the itinerary (" +
                  str(itinerary.route_id) + ") doesn't match route id of line (" +
                  str(line.route_id) + ")")
            print(" " + itinerary.osm_url)
            print(" " + line.osm_url)
            return True

        # Check if time information in schedule can be found for
        # the itinerary
        if itinerary.route_id not in schedule['lines']:
            print(" Warning: Route not found in schedule.")
            return False

        return True

    def _add_shape_to_feed(self, feed, shape_id, itinerary):
        """
        Create GTFS shape and return shape_id to add on GTFS trip
        """
        shape_id = str(shape_id)

        # Only add a shape if there isn't one with this shape_id
        try:
            feed.GetShape(shape_id)
        except KeyError:
            shape = transitfeed.Shape(shape_id)
            for point in itinerary.shape:
                shape.AddPoint(
                    lat=float(point["lat"]), lon=float(point["lon"]))
            feed.AddShapeObject(shape)
        return shape_id

    def _add_itinerary_trips(self, feed, itinerary, line, trip_builder,
                             shape_id):
        """
        Add all trips of an itinerary to the GTFS feed.
        """
        # Obtain GTFS route to add trips to it.
        route = feed.GetRoute(line.route_id)
        trips_count = 0

        # Loop through each timeslot for a trip
        for trip in trip_builder['schedule']:
            gtfs_trip = route.AddTrip(feed, headsign=itinerary.to,
                                      service_period=trip_builder['service_period'])
            trips_count += 1

            # Go through all stops of an itinerary
            for itinerary_stop_id in itinerary.get_stops():

                # Load full stop object
                try:
                    itinerary_stop = trip_builder[
                        'all_stops']['regular'][itinerary_stop_id]
                except ValueError:
                    print("Itinerary (" + itinerary.route_url +
                          ") misses a stop:")
                    print(" Please review:" + itinerary_stop.osm_url)
                    continue

                try:
                    # Load respective GTFS stop object
                    gtfs_stop = feed.GetStop(str(itinerary_stop.stop_id))
                except ValueError:
                    print("Warning: Stop in itinerary was not found in GTFS.")
                    print(" " + itinerary_stop.osm_url)

                # Make sure we compare same unicode encoding
                if type(itinerary_stop.name) is str:
                    itinerary_stop.name = itinerary_stop.name.decode('utf-8')

                time = "-"
                # Check if we have specific time information for this stop.
                try:
                    time = trip[trip_builder['stops'].index(itinerary_stop.name)]
                except ValueError:
                    pass

                # Validate time information
                if time != "-":
                    try:
                        time_at_stop = str(
                            datetime.strptime(time, "%H:%M").time())
                    except ValueError:
                        print("Warning: Time for a stop was not valid.")
                        print(" " + itinerary_stop.name +
                              " - " + itinerary_stop.osm_id)
                        break
                    gtfs_trip.AddStopTime(gtfs_stop, stop_time=time_at_stop)

                # Add stop without time information, too (we interpolate later)
                else:
                    try:
                        gtfs_trip.AddStopTime(gtfs_stop)
                    except ValueError:
                        print("Warning: Could not add first a stop to trip.")
                        print(" " + itinerary_stop.name +
                              " - " + itinerary_stop.osm_id)
                        break

                # Add reference to shape
                gtfs_trip.shape_id = shape_id

                # Add empty attributes to make navitia happy
                gtfs_trip.block_id = ""
                gtfs_trip.wheelchair_accessible = ""
                gtfs_trip.bikes_allowed = ""
                gtfs_trip.direction_id = ""

            # Calculate all times of stops, which were added with no time
            Helper.interpolate_stop_times(gtfs_trip)
        return trips_count

    def _create_gtfs_service_period(self, feed, service):
        """
        Generate a transitfeed ServicePeriod object
        from a time string according to the standard schedule:
        https://github.com/grote/osm2gtfs/wiki/Schedule

        :return: ServicePeriod object
        """
        try:
            gtfs_service = feed.GetServicePeriod(service)
            if gtfs_service is not None:
                return gtfs_service
        except KeyError:
            pass

        if service == "Mo-Fr":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(False)
        elif service == "Mo-Sa":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(5, True)
        elif service == "Mo-Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(True)
            gtfs_service.SetWeekendService(True)
        elif service == "Sa":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(5, True)
        elif service == "Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(False)
            gtfs_service.SetDayOfWeekHasService(6, True)
        elif service == "Sa-Su":
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetWeekdayService(False)
            gtfs_service.SetWeekendService(True)
        elif re.search(r'^([0-9]{4})-?(1[0-2]|0[1-9])-?(3[01]|0[1-9]|[12][0-9])$', service):
            service = service.replace('-', '')
            gtfs_service = ServicePeriod(service)
            gtfs_service.SetDateHasService(service)
        else:
            raise KeyError("Unknown service keyword: " + service)

        gtfs_service.SetStartDate(self.config['feed_info']['start_date'])
        gtfs_service.SetEndDate(self.config['feed_info']['end_date'])
        feed.AddServicePeriodObject(gtfs_service)
        return feed.GetServicePeriod(service)

    def _load_itinerary_schedule(self, schedule, itinerary, service):
        """
        Load the part of the provided schedule that fits to a particular
        itinerary.

        :return times: List of strings
        """
        times = None
        for trip in schedule['lines'][itinerary.route_id]:
            trip_services = trip["services"]
            if (trip[
                    "from"] == itinerary.fr and trip[
                        "to"] == itinerary.to and service in trip_services):
                times = trip["times"]

        if times is None:
            print("Warning: Couldn't load times from schedule for route")
        return times

    def _load_scheduled_stops(self, schedule, itinerary, service):
        """
        Load the name of stops that have time information in the provided
        schedule.

        :return stops: List of strings
        """
        stops = []
        for trip in schedule['lines'][itinerary.route_id]:
            trip_services = trip["services"]
            if (trip[
                    "from"] == itinerary.fr and trip[
                        "to"] == itinerary.to and service in trip_services):
                for stop in trip["stations"]:
                    stops.append(stop)
        return stops
