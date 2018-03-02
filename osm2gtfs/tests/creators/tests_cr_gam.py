import unittest
import os
import logging
from osm2gtfs.tests.creators.creators_tests import CreatorsTestsAbstract

# Define logging level
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class TestCreatorsCrGam(CreatorsTestsAbstract):

    def _get_selector(self):
        return "cr_gam"

    def _get_required_variables(self):
        # Define required values for the tests of this provider
        return {
            'routes_count': 3,
            'stops_count': 33,
            'stations_count': 1,
            'stops_osm_count': 34,
            'route_id_to_check': 2,
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
        self.config.data['start_date'] = "20200101"
        self.config.data['end_date'] = "20201231"


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_refresh_routes_cache', 'test_refresh_stops_cache', 'test_gtfs_from_cache']
    suite = unittest.TestSuite(map(TestCreatorsCrGam, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
