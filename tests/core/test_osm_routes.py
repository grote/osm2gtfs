# coding=utf-8
import unittest
from collections import OrderedDict
from datetime import timedelta
from osm_routes import Route, RouteMaster

class TestOsmRoutes(unittest.TestCase):

    global route
    route = Route

    global namelessRoute
    namelessRoute = Route

    global route_master
    route_master = RouteMaster

    global time_delta
    time_delta = timedelta

    global stops
    stops = {}

    def setUp(self):
        osm = 1;
        fr = 2;
        to = 3;
        ref = 1
        name = 'foo'
        shape = {}

        # Dictionary of routes
        route_master_routes = OrderedDict()

        route_master = RouteMaster(osm, ref, 'Route Master', route_master_routes)

        self.stops = [{"stop_id": "S1", "stop_name": "Mission St. & Silver Ave.", "parent_station": ""},{"stop_id": "S2", "stop_name": "Mission St. & Silver Ave.", "parent_station": "S1"}]
        self.route = Route(osm, fr, to, self.stops, route_master, ref, name, shape)
        self.namelessRoute  = Route(osm, fr, to, self.stops, route_master, ref, None, shape)

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
        route.set_duration(self.route, time_delta)
        self.assertEqual(self.route.duration, time_delta,
            "Assigned and stored timedeltas should be the same")

    def test_route_get_first_stop_should_return_none(self):
        """
        Should return None when there are no stops defined
        """
        self.route.stops = []
        first_stop = route.get_first_stop(self.route)
        self.assertIsNone(first_stop, "First stop expected to be None")

    def test_route_it_should_return_the_first_stop(self):
        """
        Should return the first stop from the stops property
        """
        first_stop = route.get_first_stop(self.route)
        self.assertEqual(self.stops[0], first_stop, "First stops didn't match")

    def test_it_should_have_a_proper_master(self):
        """
        Should return true when master is set and has at least one route
        """
        self.assertTrue(self.route.has_proper_master, "First stops didn't match")

    def test_is_should_have_string_representation(self):
        """
        Should print a description
        """
        expected = '1 | foo | Stops: 2 | https://www.openstreetmap.org/relation/1 http://www.consorciofenix.com.br/horarios?q=1'
        route_repr = repr(self.route)
        self.assertEqual(route_repr, expected)

if __name__ == '__main__':
    unittest.main()
