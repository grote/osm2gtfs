# coding=utf-8


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
