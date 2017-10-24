# coding=utf-8

from osm2gtfs.core.helper import Helper
from osm2gtfs.creators.stops_creator import StopsCreator


def create_stop_area(stop_data, feed):
    stop_id = stop_data.osm_id
    gtfs_stop_area = feed.AddStop(
        lat=float(stop_data.lat),
        lng=float(stop_data.lon),
        name=stop_data.name,
        stop_id="SA" + str(stop_id)
    )
    gtfs_stop_area.location_type = 1
    return gtfs_stop_area


def create_stop_point(stop_data, feed):
    stop_id = stop_data.osm_id
    gtfs_stop_point = feed.AddStop(
        lat=float(stop_data.lat),
        lng=float(stop_data.lon),
        name=stop_data.name,
        stop_id=str(stop_id)
    )
    return gtfs_stop_point


def get_stop_id(stop):
    return stop.osm_id


class StopsCreatorGhAccra(StopsCreator):

    def add_stops_to_feed(self, feed, data):
        stops = data.get_stops()
        stops_by_name = {}

        for internal_stop_id, a_stop in stops['regular'].items():
            if a_stop.name not in stops_by_name:
                stops_by_name[a_stop.name] = []
            stops_by_name[a_stop.name].append(a_stop)

        for a_stop_name in stops_by_name:
            stop_areas = []

            for a_stop_point in sorted(stops_by_name[a_stop_name], key=get_stop_id):
                gtfs_stop_point = create_stop_point(a_stop_point, feed)
                stop_point_has_parent_location = False
                for a_stop_area in stop_areas:
                    distance_to_parent_station = Helper.get_crow_fly_distance(
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
