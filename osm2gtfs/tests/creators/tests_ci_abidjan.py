import os
import unittest
import logging
from osm2gtfs.tests.creators.creators_tests import CreatorsTestsAbstract

# Define logging level
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class TestCreatorsCiAbidjan(CreatorsTestsAbstract):

    def _get_selector(self):
        return "ci_abidjan"

    def _get_required_variables(self):
        # Define required values for the tests of this provider
        return {
            'routes_count': 193,
            'stops_count': 2614,
            'stations_count': 0,
            'stops_osm_count': 2614,
            'route_id_to_check': 10192143,
            'gtfs_files': [
                "agency.txt", "calendar.txt", "frequencies.txt", "routes.txt",
                "shapes.txt", "stops.txt", "stop_times.txt", "trips.txt"
            ],
        }

    def _override_configuration(self):
        self.config.data['stops']['name_auto'] = "no"


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_refresh_routes_cache',
                  'test_refresh_stops_cache', 'test_gtfs_from_cache']
    suite = unittest.TestSuite(map(TestCreatorsCiAbidjan, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
