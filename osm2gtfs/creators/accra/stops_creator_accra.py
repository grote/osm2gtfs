# coding=utf-8


from osm2gtfs.creators.stops_creator import StopsCreator
import math


def get_crow_fly_distance(from_tuple, to_tuple):
    """
    Uses the Haversine formmula to compute distance
    (https://en.wikipedia.org/wiki/Haversine_formula#The_haversine_formula)
    """
    lat1, lon1 = from_tuple
    lat2, lon2 = to_tuple

    lat1 = float(lat1)
    lat2 = float(lat2)
    lon1 = float(lon1)
    lon2 = float(lon2)

    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c

    return d * 1000  # meters


def create_stop_area(stop_data, feed):
    gtfs_stop_area = feed.AddStop(
        lat=float(stop_data.lat),
        lng=float(stop_data.lon),
        name=stop_data.name,
        stop_id="SA" + str(stop_data.id)
    )
    gtfs_stop_area.location_type = 1
    return gtfs_stop_area


def create_stop_point(stop_data, feed):
    gtfs_stop_point = feed.AddStop(
        lat=float(stop_data.lat),
        lng=float(stop_data.lon),
        name=stop_data.name,
        stop_id=str(stop_data.id)
    )
    return gtfs_stop_point


def get_stop_id(stop):
    return stop.id


class StopsCreatorAccra(StopsCreator):

    def add_stops_to_feed(self, feed, data):
        stops = data.get_stops()
        stops_by_name = {}

        for a_stop_id, a_stop in stops.items():
            a_stop.osm_id = a_stop_id
            if a_stop.name not in stops_by_name:
                stops_by_name[a_stop.name] = []
            stops_by_name[a_stop.name].append(a_stop)

        for a_stop_name in stops_by_name:
            stop_areas = []

            for a_stop_point in sorted(stops_by_name[a_stop_name], key=get_stop_id):
                gtfs_stop_point = create_stop_point(a_stop_point, feed)
                stop_point_has_parent_location = False
                for a_stop_area in stop_areas:
                    distance_to_parent_station = get_crow_fly_distance(
                        (a_stop_area.stop_lat, a_stop_area.stop_lon),
                        (a_stop_point.lat, a_stop_point.lon)
                    )
                    if distance_to_parent_station < 500:
                        gtfs_stop_point.parent_station = a_stop_area.stop_id
                        stop_point_has_parent_location = True
                        break
                if not stop_point_has_parent_location:
                    new_sa = create_stop_area(a_stop_point, feed)
                    gtfs_stop_point.parent_station = new_sa.stop_id
                    stop_areas.append(new_sa)
