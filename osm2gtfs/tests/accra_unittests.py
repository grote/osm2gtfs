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
        self.selector = "accra"
        self.output = os.path.realpath(os.path.join(current_dir, "../../data/accra_tests.zip"))


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


class TestAccra(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.realpath(os.path.join(current_dir, "../../data/"))
        self.config_file = os.path.realpath(
            os.path.join(current_dir, "../creators/accra/accra.json")
        )
        self.fixture_folder = os.path.join(os.path.realpath(current_dir), "fixtures/accra/")
        args = Args(self.config_file)
        self.config = Configuration(args)
        # deactivation of Overpass calls for unnamed stops
        self.config.data['stops']['name_auto'] = "no"

    def test_refresh_routes_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(self.data_dir, "accra-routes.pkl")
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
        routes = cache.read_data('routes-accra')
        self.assertEqual(len(routes), 277, 'Wrong count of routes in the cache file')

    def test_refresh_stops_cache(self):
        data = OsmConnector(self.config)
        cache_file = os.path.join(self.data_dir, "accra-stops.pkl")
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
        stops = cache.read_data('stops-accra')
        self.assertEqual(len(stops), 2529, 'Wrong count of stops in the cache file')

    def test_gtfs_from_cache(self):
        # the cache is generated by the previous two functions
        routes_cache_file = os.path.join(self.data_dir, "accra-routes.pkl")
        stops_file = os.path.join(self.data_dir, "accra-stops.pkl")
        self.assertTrue(os.path.isfile(stops_file), "The stops cache file doesn't exists")
        self.assertTrue(os.path.isfile(routes_cache_file), "The routes cache file doesn't exists")

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
        gtfs_expected_result = os.path.join(self.fixture_folder, "accra_tests.zip.ref")
        gtfs_generated_result = os.path.join(self.data_dir, "accra_tests.zip")
        self.assertTrue(is_valid_gtfs(gtfs_generated_result), 'The generated GTFS is not valid')
        self.assertTrue(is_valid_gtfs(gtfs_expected_result), 'The expected GTFS is not valid')
        self.assertTrue(is_identical_gtfs(gtfs_expected_result, gtfs_generated_result),
                        'The generated GTFS is different from the expected one')
        gtfs_infos = get_gtfs_infos(gtfs_generated_result)
        self.assertEqual(gtfs_infos["stop_points_count"], 2529,
                         "Wrong stop_points count in the generated GTFS")
        self.assertEqual(gtfs_infos["stop_areas_count"], 1656,
                         "Wrong stop_areas count in the generated GTFS")
        self.assertEqual(gtfs_infos["routes_count"], 277,
                         "Wrong routes count in the generated GTFS")


def suite():
    tests = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    return unittest.TestSuite(map(TestAccra, tests))

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
