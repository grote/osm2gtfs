# coding=utf-8
import unittest
from collections import OrderedDict
from datetime import timedelta
from core.osm_routes import Route, RouteMaster


class TestOsmRoutes(unittest.TestCase):
    route = Route
    namelessRoute = Route
    route_master = RouteMaster
    time_delta = timedelta
    stops = []

    def setUp(self):
        osm = 1
        fr = 2
        to = 3
        ref = 1
        name = 'foo'
        shape = {}

        # Routes dictonary
        route_master_routes = OrderedDict()
        route_master = RouteMaster(osm, ref, 'Route Master', route_master_routes)

        self.stops = [
            {"stop_id": "S1", "stop_name": "Mission St.", "parent_station": ""},
            {"stop_id": "S2", "stop_name": "Silver Ave.", "parent_station": "S1"}
        ]

        self.route = Route(osm, fr, to, self.stops, route_master, ref, name, shape)
        self.namelessRoute = Route(osm, fr, to, self.stops, route_master, ref, None, shape)

    def test_route_with_no_name_should_have_name_set_to_none(self):
        """
        If no name is provided when creating a route than route.name should be
        None.
        """
        self.assertIsNone(self.namelessRoute.name, "Name should be None")

    def test_route_it_should_set_duration(self):
        """
        Should have a duration stored after set_duration is called
        """
        self.time_delta = timedelta(hours=1, minutes=25)
        self.route.set_duration(self.time_delta)
        self.assertEqual(self.route.duration, self.time_delta)

    def test_route_get_first_stop_should_return_none(self):
        """
        Should return None when there are no stops defined
        """
        self.route.stops = None
        self.assertTrue(self.route.stops is None, "First stop expected to be None")

    def test_route_it_should_return_the_first_stop(self):
        """
        Should return the first stop from the stops property
        """
        self.assertTrue(self.route.get_first_stop() == self.stops[0], "First stops didn't match")

    def test_it_should_have_a_proper_master(self):
        """
        Should return true when master is set and has at least one route
        """
        self.assertTrue(self.route.has_proper_master)

if __name__ == '__main__':
    unittest.main()
