import unittest
import os
import logging
from osm2gtfs.tests.creators.creators_tests import CreatorsTestsAbstract

# Define logging level
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class TestCreatorsNiManagua(CreatorsTestsAbstract):

    def _get_selector(self):
        return "ni_managua"

    def _get_required_variables(self):
        # Define required values for the tests of this provider
        return {
            'routes_count': 45,
            'stops_count': 1450,
            'stations_count': 547,
            'stops_osm_count': 1997,
            'route_id_to_check': 111,
            'gtfs_files': [
                "agency.txt", "calendar.txt", "routes.txt", "shapes.txt",
                "stops.txt", "stop_times.txt", "trips.txt"
            ],
        }

    def _override_configuration(self):
        # Overriding some of the configuration options
        # Use local timetable.json
        self.config.data['schedule_source'] = os.path.join(
            self.standard_variables['fixture_dir'], "timetable.json")
        # Use timeframe of reference GTFS
        self.config.data['start_date'] = "201780101"
        self.config.data['end_date'] = "20180201"


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    suite = unittest.TestSuite(map(TestCreatorsNiManagua, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
