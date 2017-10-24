import unittest
import os
import overpy
import transitfeed
import zipfile
import csv

from mock import patch
from osm2gtfs.core.configuration import Configuration
from osm2gtfs.core.osm_connector import OsmConnector
from osm2gtfs.core.creator_factory import CreatorFactory
from osm2gtfs.core.cache import Cache

current_dir = os.path.dirname(__file__)


class Args():
    def __init__(self, config_file):
        self.config = open(config_file)
        self.selector = "gh_accra"
        self.output = os.path.realpath(
            os.path.join(current_dir, "../../../data/gh_accra_tests.zip"))


def is_valid_gtfs(gtfs):
    # checking Accra GTFS files are present in both files
    accra_gtfs_files = [
        "agency.txt", "stops.txt", "routes.txt", "trips.txt",
        "stop_times.txt", "calendar.txt", "frequencies.txt", "shapes.txt"
    ]
    zf = zipfile.ZipFile(gtfs)
    info_list = zf.infolist()
    gtfs_files_name = [i.filename for i in info_list]
    for s in accra_gtfs_files:
        if s not in gtfs_files_name:
            return False
    return True


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
                return False
    return True


def check_osm_route_stop_times(gtfs1, gtfs2, osm_relation_id):
    osm_relation_id = str(osm_relation_id)
    zf1 = zipfile.ZipFile(gtfs1)
    zf2 = zipfile.ZipFile(gtfs2)
    # Grabbing the trip_ids from both gtfs
    trips_id1 = []
    with zf1.open("trips.txt") as trip_file:
        reader = csv.DictReader(trip_file)
        for row in reader:
            if row["route_id"] == osm_relation_id:
                trips_id1.append(row['trip_id'])
    trips_id2 = []
    with zf2.open("trips.txt") as trip_file:
        reader = csv.DictReader(trip_file)
        for row in reader:
            if row["route_id"] == osm_relation_id:
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
                        "stop_id different for trip_id={} and stop_sequence={} ({} <> {})".format(
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
                "No corresponing stop_time for trip_id={} and stop_sequence={}".format(
                    st1["trip_id"],
                    st1["stop_sequence"]
                )
            )
            return False
    return True


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


class TestCreatorsGhAccra(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.realpath(os.path.join(current_dir, "../../../data/"))
        self.config_file = os.path.realpath(
            os.path.join(current_dir, "../../creators/gh_accra/config.json")
        )
        self.fixture_folder = os.path.join(os.path.realpath(current_dir), "fixtures/gh_accra/")
        args = Args(self.config_file)
        self.config = Configuration(args)
        # deactivation of Overpass calls for unnamed stops
        self.config.data['stops']['name_auto'] = "no"

    def test_refresh_routes_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(self.data_dir, "gh_accra-routes.pkl")
        mocked_overpass_data_file = os.path.join(self.fixture_folder, "overpass-routes.xml")
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_routes") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_routes(refresh=True)
        self.assertTrue(os.path.isfile(cache_file), 'The routes cache file creation failed')
        cache = Cache()
        routes = cache.read_data('gh_accra-routes')
        self.assertEqual(len(routes), 277, 'Wrong count of routes in the cache file')

    def test_refresh_stops_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(self.data_dir, "gh_accra-stops.pkl")
        mocked_overpass_data_file = os.path.join(self.fixture_folder, "overpass-stops.xml")
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_stops") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_stops(refresh=True)
        self.assertTrue(os.path.isfile(cache_file), 'The stops cache file creation failed')
        cache = Cache()
        stops = cache.read_data('gh_accra-stops')
        amount_of_stops = len(stops['regular']) + len(stops['stations'])
        self.assertEqual(amount_of_stops, 2529, 'Wrong count of stops in the cache file')

    def test_gtfs_from_cache(self):
        # the cache is generated by the previous two functions
        routes_cache_file = os.path.join(self.data_dir, "gh_accra-routes.pkl")
        stops_file = os.path.join(self.data_dir, "gh_accra-stops.pkl")
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
        trips_creator = factory.get_trips_creator()

        # Add data to schedule object
        agency_creator.add_agency_to_feed(feed)
        feed_info_creator.add_feed_info_to_feed(feed)
        routes_creator.add_routes_to_feed(feed, data)
        stops_creator.add_stops_to_feed(feed, data)
        trips_creator.add_trips_to_feed(feed, data)

        # Write GTFS
        feed.WriteGoogleTransitFeed(self.config.output)
        gtfs_expected_result = os.path.join(self.fixture_folder, "gh_accra_tests.zip.ref")
        gtfs_generated_result = os.path.join(self.data_dir, "gh_accra_tests.zip")
        self.assertTrue(is_valid_gtfs(gtfs_generated_result), 'The generated GTFS is not valid')
        self.assertTrue(is_valid_gtfs(gtfs_expected_result), 'The expected GTFS is not valid')

        self.assertTrue(is_identical_gtfs(gtfs_expected_result, gtfs_generated_result),
                        "The generated GTFS is different from the expected one")
        gtfs_infos = get_gtfs_infos(gtfs_generated_result)
        self.assertEqual(gtfs_infos["stop_points_count"], 2529,
                         "Wrong stop_points count in the generated GTFS")
        self.assertEqual(gtfs_infos["stop_areas_count"], 1656,
                         "Wrong stop_areas count in the generated GTFS")
        self.assertEqual(gtfs_infos["routes_count"], 277,
                         "Wrong routes count in the generated GTFS")
        self.assertTrue(
            check_osm_route_stop_times(gtfs_expected_result, gtfs_generated_result, 7551952),
            "Error found on stop_times of osm relation 7551952"
        )


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    suite = unittest.TestSuite(map(TestCreatorsGhAccra, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
