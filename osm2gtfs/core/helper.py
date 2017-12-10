# coding=utf-8

import sys
from math import cos, sin, atan2, sqrt, radians, degrees


class Helper(object):
    """The Helper class contains useful static functions

    """

    @staticmethod
    def print_shape_for_leaflet(shape):
        print "var shape = [",
        i = 0
        for node in shape:
            print "new L.LatLng(" + str(node["lat"]) + ", " + str(node["lon"]) + ")",
            if i != len(shape) - 1:
                print ",",
            i += 1
        print "];"
        i = 0
        for node in shape:
            print "L.marker([" + str(node["lat"]) + ", " + str(node["lon"]) + "]).addTo(map)"
            print "    .bindPopup(\"" + str(i) + "\").openPopup();"
            i += 1

    @staticmethod
    def get_center_of_nodes(nodes):
        """Helper function to get center coordinates of a group of nodes

        """
        x = 0
        y = 0
        z = 0

        if len(nodes) < 1:
            sys.stderr.write("Cannot find the center of zero nodes\n")
        for node in nodes:
            lat = radians(float(node.lat))
            lon = radians(float(node.lon))

            x += cos(lat) * cos(lon)
            y += cos(lat) * sin(lon)
            z += sin(lat)

        x = float(x / len(nodes))
        y = float(y / len(nodes))
        z = float(z / len(nodes))

        center_lat = degrees(atan2(z, sqrt(x * x + y * y)))
        center_lon = degrees(atan2(y, x))

        return center_lat, center_lon

    @staticmethod
    def interpolate_stop_times(trip):
        """
        Interpolate stop_times, because Navitia does not handle this itself
        """
        try:
            for secs, stop_time, is_timepoint in trip.GetTimeInterpolatedStops():
                if not is_timepoint:
                    stop_time.arrival_secs = secs
                    stop_time.departure_secs = secs
                    trip.ReplaceStopTimeObject(stop_time)
        except ValueError as e:
            print(e)
