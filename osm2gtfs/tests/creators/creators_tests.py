import unittest
import os
import zipfile
import csv
import overpy
import transitfeed

from mock import patch
from osm2gtfs.core.configuration import Configuration
from osm2gtfs.core.osm_connector import OsmConnector
from osm2gtfs.core.creator_factory import CreatorFactory
from osm2gtfs.core.cache import Cache

current_dir = os.path.dirname(__file__)


class CreatorsTestsArgs():
    def __init__(self, config_file, selector):
        """
        Prepare arguments for the Initialization of an Configuration object
        (see osm2gtfs.core.configuration for more information)

        """
        # Basic preparations
        self.config = open(config_file)
        self.selector = selector

        # Overriding the output to not interfere with user's data
        self.output = os.path.realpath(
            os.path.join(current_dir, "../../../data/" + self.selector + "_tests.zip"))


class CreatorsTestsAbstract(unittest.TestCase):

    def _get_selector(self):
        """
        Needs to be implemented for providers. And return the selector stroing.
        """
        raise NotImplementedError

    def _get_required_variables(self):
        """
        Needs to be implemented for providers. And return the required values.
        A dictionary containing the following keys is expected to be returned:

        * routes_count
        * stops_count
        * stations_count
        * stops_osm_count
        * route_id_to_check
        * gtfs_files

        """
        raise NotImplementedError

    def _get_standard_variables(self):
        """
        This method provides flexible standard values.
        In case they need to change for certain providers, this method can easily
        be overridden.
        """

        # Default paths
        data_dir = os.path.realpath(os.path.join(current_dir, "../../../data/"))
        fixture_dir = os.path.join(os.path.realpath(current_dir), "fixtures/" + self.selector)

        # Define standard values
        standard_variables = {
            'config_file': os.path.realpath(
                os.path.join(current_dir, "../../creators/" + self.selector + "/config.json")),
            'data_dir': data_dir,
            'fixture_dir': fixture_dir,
            'output_file': os.path.realpath(os.path.join(
                data_dir, self.selector + "_tests.zip")),
            'reference_gtfs': os.path.join(fixture_dir, self.selector + "_gtfs.zip.ref"),
            'mocked_overpass_routes': os.path.join(fixture_dir, "overpass-routes.xml"),
            'mocked_overpass_stops': os.path.join(fixture_dir, "overpass-stops.xml"),
        }
        return standard_variables

    def _override_configuration(self):
        # Eventually configuration options can be overridden here
        #   Example: Use local timetable.json
        #   self.config.data['schedule_source'] = os.path.join(self.fixture_dir, "timetable.json")
        return

    def setUp(self):
        """
        This method sets the basic variables for testing of providers.
        It needs to be implemented for each provider in the heriting class.
        """

        # Define selector for this tests
        self.selector = self._get_selector()

        # Define expected results (need to be adjusted for providers)
        self.required_variables = self._get_required_variables()

        # Initialize some standard paths and variables
        self.standard_variables = self._get_standard_variables()

        # Load configuration
        self.config = Configuration(
            CreatorsTestsArgs(self.standard_variables['config_file'], self.selector))

        # Allow providers to override the  configuration for test cases
        self._override_configuration()

    def test_refresh_routes_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(
            self.standard_variables['data_dir'], self.selector + "-routes.pkl")
        mocked_overpass_data_file = self.standard_variables['mocked_overpass_routes']
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_routes") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_routes(refresh=True)
        self.assertTrue(os.path.isfile(cache_file), 'The routes cache file creation failed')
        cache = Cache()
        routes = cache.read_data(self.selector + "-routes")
        self.assertEqual(
            len(routes), self.required_variables['routes_count'],
            'Wrong count of routes in the cache file')

    def test_refresh_stops_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(self.standard_variables['data_dir'], self.selector + "-stops.pkl")
        mocked_overpass_data_file = self.standard_variables['mocked_overpass_stops']
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_stops") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_stops(refresh=True)
        self.assertTrue(os.path.isfile(cache_file), 'The stops cache file creation failed')
        cache = Cache()
        stops = cache.read_data(self.selector + "-stops")
        amount_of_stops = len(stops['regular']) + len(stops['stations'])
        print("> Amount of osm stops: " + str(amount_of_stops))
        self.assertEqual(
            amount_of_stops, self.required_variables['stops_osm_count'],
            'Wrong count of stops in the cache file')

    def test_gtfs_from_cache(self):
        # the cache is generated by the previous two functions
        routes_cache_file = os.path.join(
            self.standard_variables['data_dir'], self.selector + "-routes.pkl")
        stops_file = os.path.join(
            self.standard_variables['data_dir'], self.selector + "-stops.pkl")
        self.assertTrue(
            os.path.isfile(stops_file), "The stops cache file doesn't exists")
        self.assertTrue(
            os.path.isfile(routes_cache_file), "The routes cache file doesn't exists")

        data = OsmConnector(self.config)

        # Define (transitfeed) schedule object for GTFS creation
        feed = transitfeed.Schedule()
        # Initiate creators for GTFS components through an object factory
        factory = CreatorFactory(self.config)
        agency_creator = factory.get_agency_creator()
        feed_info_creator = factory.get_feed_info_creator()
        routes_creator = factory.get_routes_creator()
        stops_creator = factory.get_stops_creator()
        schedule_creator = factory.get_schedule_creator()
        trips_creator = factory.get_trips_creator()

        # Add data to schedule object
        agency_creator.add_agency_to_feed(feed)
        feed_info_creator.add_feed_info_to_feed(feed)
        stops_creator.add_stops_to_feed(feed, data)
        routes_creator.add_routes_to_feed(feed, data)
        schedule_creator.add_schedule_to_data(data)
        trips_creator.add_trips_to_feed(feed, data)

        # Write GTFS
        feed.WriteGoogleTransitFeed(self.config.output)
        gtfs_expected_result = self.standard_variables['reference_gtfs']
        gtfs_generated_result = self.standard_variables['output_file']

        # Verify GTFS
        self.assertTrue(
            CreatorsTestsHelper.is_valid_gtfs(
                gtfs_generated_result, self.required_variables['gtfs_files']),
            'The generated GTFS is not valid')

        self.assertTrue(
            CreatorsTestsHelper.is_valid_gtfs(
                gtfs_expected_result, self.required_variables['gtfs_files']),
            'The expected GTFS is not valid')

        self.assertTrue(
            CreatorsTestsHelper.is_identical_gtfs(gtfs_expected_result, gtfs_generated_result),
            "The generated GTFS is different from the expected one")

        # Obtain and print basic count infos about the GTFS
        gtfs_infos = CreatorsTestsHelper.get_gtfs_infos(gtfs_generated_result)
        print("> Information about the GTFS feed: " + str(gtfs_infos))

        # Verify stop and route counts against expected values
        self.assertEqual(gtfs_infos["stop_points_count"], self.required_variables['stops_count'],
                         "Wrong stop_points count in the generated GTFS")
        self.assertEqual(gtfs_infos["stop_areas_count"], self.required_variables['stations_count'],
                         "Wrong stop_areas count in the generated GTFS")
        self.assertEqual(gtfs_infos["routes_count"], self.required_variables['routes_count'],
                         "Wrong routes count in the generated GTFS")

        # Use one route to compare exact time information between both GTFSes
        self.assertTrue(
            CreatorsTestsHelper.check_osm_route_stop_times(
                gtfs_expected_result, gtfs_generated_result,
                self.required_variables['route_id_to_check']),
            "Error found on stop_times for the route " + str(
                self.required_variables['route_id_to_check']))


# pylint: disable=no-init
class CreatorsTestsHelper():
    @staticmethod
    def is_valid_gtfs(gtfs, gtfs_files):
        zf = zipfile.ZipFile(gtfs)
        info_list = zf.infolist()
        gtfs_files_name = [i.filename for i in info_list]
        for s in gtfs_files:
            if s not in gtfs_files_name:
                return False
        return True

    @staticmethod
    def is_identical_gtfs(gtfs1, gtfs2):
        zf1 = zipfile.ZipFile(gtfs1)
        zf2 = zipfile.ZipFile(gtfs2)
        info_list1 = zf1.infolist()
        info_list2 = zf2.infolist()
        # checking unzipped file size
        for info1 in info_list1:
            for info2 in info_list2:
                if info1.filename == info2.filename:
                    print("Validation of {:} size : size1={:} size2={:}".format(
                        info2.filename, info1.file_size, info2.file_size
                    ))
                if info1.filename == info2.filename and info1.file_size != info2.file_size:
                    print("Difference detected: " + info1.filename)
                    return False
        return True

    @staticmethod
    def check_osm_route_stop_times(gtfs1, gtfs2, route_id):
        route_id = str(route_id)
        zf1 = zipfile.ZipFile(gtfs1)
        zf2 = zipfile.ZipFile(gtfs2)
        # Grabbing the trip_ids from both gtfs
        trips_id1 = []
        with zf1.open("trips.txt") as trip_file:
            reader = csv.DictReader(trip_file)
            for row in reader:
                if row["route_id"] == route_id:
                    trips_id1.append(row['trip_id'])
        trips_id2 = []
        with zf2.open("trips.txt") as trip_file:
            reader = csv.DictReader(trip_file)
            for row in reader:
                if row["route_id"] == route_id:
                    trips_id2.append(row['trip_id'])
        if trips_id1 != trips_id2:
            print("Error on count of trips found ({:d} <> {:d})".format(
                len(trips_id1),
                len(trips_id2)
            ))
            return False
        # Grabbing simplified stop_times for found trips
        stop_times1 = []
        stop_times2 = []
        with zf1.open("stop_times.txt") as st_file:
            reader = csv.DictReader(st_file)
            for row in reader:
                if row["trip_id"] in trips_id1:
                    st = {
                        "trip_id": row['trip_id'],
                        "stop_id": row['stop_id'],
                        "stop_sequence": row['stop_sequence'],
                        "arrival_time": row['arrival_time'],
                        "departure_time": row['departure_time'],
                    }
                    stop_times1.append(st)
        with zf2.open("stop_times.txt") as st_file:
            reader = csv.DictReader(st_file)
            for row in reader:
                if row["trip_id"] in trips_id2:
                    st = {
                        "trip_id": row['trip_id'],
                        "stop_id": row['stop_id'],
                        "stop_sequence": row['stop_sequence'],
                        "arrival_time": row['arrival_time'],
                        "departure_time": row['departure_time'],
                    }
                    stop_times2.append(st)
        if len(stop_times1) != len(stop_times2):
            print("Error on count of stop_times found ({:d} <> {:d})".format(
                len(stop_times1),
                len(stop_times2)
            ))
            return False
        # Checking for the first error in stop_times with an explicit message
        for st1 in stop_times1:
            trip_point_found = False
            for st2 in stop_times2:
                if st1["trip_id"] == st2["trip_id"] \
                        and st1["stop_sequence"] == st2["stop_sequence"]:
                    trip_point_found = True
                    if st1["stop_id"] != st2["stop_id"]:
                        print(
                            "stop_id different for trip_id={} & stop_sequence={} ({} <> {})".format(
                                st1["trip_id"],
                                st1["stop_sequence"],
                                st1["stop_id"],
                                st2["stop_id"]
                            )
                        )
                        return False
                    elif st1["arrival_time"] != st2["arrival_time"] \
                            or st1["departure_time"] != st2["departure_time"]:
                        print(
                            "Stop times are different for trip_id={} and stop_sequence={}".format(
                                st1["trip_id"],
                                st1["stop_sequence"]
                            )
                        )
                        for st in [st1, st2]:
                            print(
                                "\t arrival_time={}   departure_time={}".format(
                                    st["arrival_time"],
                                    st["departure_time"],
                                )
                            )
                        return False
                    else:
                        # trip_point found with no difference, break for st2 loop
                        # to continue for the next st1
                        break
            if not trip_point_found:
                print(
                    "No matching stop_time for trip_id={} and stop_sequence={}".format(
                        st1["trip_id"],
                        st1["stop_sequence"]
                    )
                )
                return False
        return True

    @staticmethod
    def get_gtfs_infos(gtfs):
        gtfs_infos = {}
        gtfs_infos["stop_points_count"] = 0
        gtfs_infos["stop_areas_count"] = 0
        gtfs_infos["routes_count"] = 0
        with zipfile.ZipFile(gtfs) as zf:
            reader = csv.DictReader(zf.open("stops.txt"))
            for r in reader:
                if r["location_type"] == "1":
                    gtfs_infos["stop_areas_count"] += 1
                else:
                    gtfs_infos["stop_points_count"] += 1
            reader = csv.DictReader(zf.open("routes.txt"))
            for r in reader:
                gtfs_infos["routes_count"] += 1
        return gtfs_infos
