import unittest
import os
import logging
import overpy

from mock import patch
from osm2gtfs.tests.creators.creators_tests import CreatorsTestsAbstract
from osm2gtfs.core.osm_connector import OsmConnector
from osm2gtfs.core.cache import Cache

# Define logging level
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class TestCreatorsBrFlorianopolis(CreatorsTestsAbstract):

    def _get_selector(self):
        return "br_florianopolis"

    def _get_required_variables(self):
        # Define required values for the tests of this provider
        return {
            'routes_count': 73,
            'stops_count': 1433,
            'stations_count': 0,
            'stops_osm_count': 1433,
            'route_id_to_check': 20,
            'gtfs_files': [
                "agency.txt", "calendar.txt", "routes.txt",
                "shapes.txt", "stops.txt", "stop_times.txt", "trips.txt"
            ],
        }

    def _override_configuration(self):
        # Overriding some of the configuration options
        self.config.data['stops']['name_auto'] = "no"
        # Use local timetable.json
        self.config.data['schedule_source'] = os.path.join(
            self.standard_variables['fixture_dir'], "timetable.json")
        # Use timeframe of reference GTFS
        self.config.data['start_date'] = "201780101"
        self.config.data['end_date'] = "20180201"

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
        # The Florianopolis creator eliminates (eight) routes in the Trips creator.
        # This should be revised. Afterwards this overriden function can be removed.
        self.assertEqual(
            len(routes), self.required_variables['routes_count'] + 8,
            'Wrong count of routes in the cache file')


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    suite = unittest.TestSuite(map(TestCreatorsBrFlorianopolis, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
