import unittest
import shutil
import os
import overpy
import transitfeed
import filecmp
import zipfile

from mock import patch
from osm2gtfs.core.configuration import Configuration
from osm2gtfs.core.osm_connector import OsmConnector
from osm2gtfs.core.creator_factory import CreatorFactory

current_dir = os.path.dirname(__file__)


class Args():
    def __init__(self, config_file):
        self.config = open(config_file)
        self.selector = "accra"
        self.output = os.path.realpath(os.path.join(current_dir, "../../data/accra_tests.zip"))


def is_identical_gtfs(gtfs1, gtfs2):
    zf1 = zipfile.ZipFile(gtfs1)
    zf2 = zipfile.ZipFile(gtfs2)
    # only checking unzipped file size
    info_list1 = zf1.infolist()
    info_list2 = zf1.infolist()
    for info1 in info_list1:
        for info2 in info_list2:
            if info1.filename == info2.filename and info1.file_size != info2.file_size:
                return False
    return True


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
        self.config.config['stops']['name_auto'] = "no"

    def test_refresh_routes_cache(self):
        data = OsmConnector(self.config.config)
        cache_file = os.path.join(self.data_dir, "routes-accra.pkl")
        mocked_overpass_data_file = os.path.join(self.fixture_folder, "overpass-routes.xml")
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_routes") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_routes(refresh=True)
            self.assertTrue(os.path.isfile(cache_file))

    def test_refresh_stops_cache(self):
        data = OsmConnector(self.config.config)
        cache_file = os.path.join(self.data_dir, "stops-accra.pkl")
        mocked_overpass_data_file = os.path.join(self.fixture_folder, "overpass-stops.xml")
        if os.path.isfile(cache_file):
            os.remove(cache_file)
        with patch("osm2gtfs.core.osm_connector.OsmConnector._query_stops") as mocked1:
            overpass_xml = open(mocked_overpass_data_file, mode='r').read()
            api = overpy.Overpass()
            mocked1.return_value = api.parse_xml(overpass_xml)
            data.get_stops(refresh=True)
            self.assertTrue(os.path.isfile(cache_file))

    def test_gtfs_from_cache(self):
        # the cache is generated by the previous two functions
        data = OsmConnector(self.config.config)

        # Define (transitfeed) schedule object for GTFS creation
        schedule = transitfeed.Schedule()
        # Initiate creators for GTFS components through an object factory
        factory = CreatorFactory(self.config.config)
        agency_creator = factory.get_agency_creator()
        feed_info_creator = factory.get_feed_info_creator()
        routes_creator = factory.get_routes_creator()
        stops_creator = factory.get_stops_creator()
        trips_creator = factory.get_trips_creator()

        # Add data to schedule object
        agency_creator.add_agency_to_schedule(schedule)
        feed_info_creator.add_feed_info_to_schedule(schedule)
        routes_creator.add_routes_to_schedule(schedule, data)
        stops_creator.add_stops_to_schedule(schedule, data)
        trips_creator.add_trips_to_schedule(schedule, data)

        # Write GTFS
        schedule.WriteGoogleTransitFeed(self.config.output)
        gtfs_expected_result = os.path.join(self.fixture_folder, "accra_tests.zip.ref")
        gtfs_generated_result = os.path.join(self.data_dir, "accra_tests.zip")
        self.assertTrue(is_identical_gtfs(gtfs_expected_result, gtfs_generated_result))


def suite():
    tests = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    return unittest.TestSuite(map(TestAccra, tests))

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
