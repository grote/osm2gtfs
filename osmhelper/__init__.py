#!/usr/bin/env python 
# coding=utf-8

import overpy
from osmapi import OsmApi
import sys
import os
import pickle
from collections import OrderedDict
from osmhelper.osm_routes import Route, RouteMaster
from osmhelper.osm_stops import Stop

CHECK_FOR_NON_PLATFORMS = False



def refresh_data():
    get_stops(get_routes(refresh=True), refresh=True)


def read_route_masters_from_file():
    if os.path.isfile('data/route_masters.pkl'):
        with open('data/route_masters.pkl', 'rb') as f:
            routes = pickle.load(f)
        return routes
    else:
        return {}


def save_routes_to_file(routes):
    with open('data/routes.pkl', 'wb') as f:
        pickle.dump(routes, f, pickle.HIGHEST_PROTOCOL)


def read_routes_from_file():
    if os.path.isfile('data/route_masters.pkl'):
        with open('data/routes.pkl', 'rb') as f:
            routes = pickle.load(f)
        return routes
    else:
        return {}


def read_stops_from_file():
    try:
        with open('data/stops.pkl', 'rb') as f:
            stops = pickle.load(f)
        return stops
    except Exception:
        return {}


def get_routes(route, bbox, refresh=False):
    if refresh:
        print "Start with fresh routes"
        routes = {}
    else:
        routes = read_routes_from_file()
        if len(routes) > 1:
            return routes

    api = overpy.Overpass()

    result = api.query("""
    <query type="relation">
        <has-kv k="route" v="%s"/>
        <bbox-query e="%s" n="%s" s="%s" w="%s"/>
    </query>
    <print/>
    """ % (route, bbox["e"], bbox["n"], bbox["s"], bbox["w"]))

    route_masters = get_route_masters(refresh, route, bbox)

    for rel in result.get_relations():
        get_route(routes, route_masters, rel)

    for master_ref in route_masters.keys():
        if master_ref not in routes:
            routes[master_ref] = route_masters[master_ref]
            sys.stderr.write("Master route was missing: " + master_ref + "\n")
            sys.stderr.write(str(routes[master_ref]) + "\n\n")

    save_routes_to_file(routes)

    return routes


def get_route_masters(route, bbox,refresh=False):
    if refresh:
        print "Start with fresh route masters"
        route_masters = {}
    else:
        route_masters = read_route_masters_from_file()
        if len(route_masters) > 1:
            return route_masters

    api = overpy.Overpass()

    # get all route_master's in bbox area
    # start out from "route" (bus, train) relations,
    # because searching directly for type=route_master does not work with overpass
    result = api.query("""
    <query type="relation">
        <has-kv k="route" v="%s"/>
        <bbox-query e="%s" n="%s" s="%s" w="%s"/>
    </query>
    <recurse type="relation-backwards"/>
    <print/>
    """ % (route, bbox["e"], bbox["n"], bbox["s"], bbox["w"]))

    for rel in result.get_relations():

        if 'ref' in rel.tags:
            ref = rel.tags['ref']
        else:
            sys.stderr.write(
                "RELATION WITHOUT REF: https://www.openstreetmap.org/relation/" + rel.id + "\n")
            continue

        name = rel.tags['name']

        # use OsmApi library, because overpy does not return members
        osm_api = OsmApi()
        routes = OrderedDict()
        for member in osm_api.RelationGet(rel.id)['member']:
            # add incomplete route, will be completed later
            stops = get_stops_of_route(member['ref'])
            route = Route(member['ref'], None, None, stops, None, ref)
            route.add_shape()
            routes[member['ref']] = route

        route_master = RouteMaster(rel.id, ref, name, routes)

        print route_master

        route_masters[ref] = route_master

    # save route masters for next time
    with open('data/route_masters.pkl', 'wb') as f:
        pickle.dump(route_masters, f, pickle.HIGHEST_PROTOCOL)

    return route_masters


def get_route(routes, route_masters, rel, warn=True):
    if 'ref' in rel.tags:
        rid = rel.id
        ref = rel.tags['ref'].replace('B', '')
        if 'name' in rel.tags:
            name = rel.tags['name']
        else:
            name = "??????"

        if 'from' in rel.tags:
            fr = rel.tags['from']
        else:
            fr = None

        if 'to' in rel.tags:
            to = rel.tags['to']
        else:
            to = None

        # more tags: operator

        if ref in route_masters:
            # route has a master, so update it in the route_master and add it to the routes
            stops = route_masters[ref].routes[rid].stops
            route_masters[ref].routes[rid] = Route(rid, fr, to, stops, route_masters[ref], ref, name)
            route_masters[ref].routes[rid].add_shape()
            routes[ref] = route_masters[ref]
        elif ref not in routes:
            # we have not seen this route, so just add it
            stops = get_stops_of_route(rid)
            routes[ref] = Route(rid, fr, to, stops, None, ref, name)
            routes[ref].add_shape()
            if len(stops) == 0:
                sys.stderr.write("Route has no bus stops: " + "https://www.openstreetmap.org/relation/" + str(rel.id) + "\n")
        elif warn:
            # we've seen a route with this ref tag already, warn about it
            sys.stderr.write("Route with ref=%s is there more than once, but has no parent route_master:\n" % str(ref))
            sys.stderr.write("    https://www.openstreetmap.org/relation/" + str(routes[rel.tags['ref']].id) + "\n")
            sys.stderr.write("    https://www.openstreetmap.org/relation/" + str(rel.id) + "\n")

        return routes[ref]
    else:
        sys.stderr.write("Route has no ref tag: " + "https://www.openstreetmap.org/relation/" + str(rel.id) + "\n")


def get_stops(routes, refresh=False):
    if refresh:
        print "Start with fresh stops"
        stops = {}
    else:
        stops = read_stops_from_file()

    # Fill in the missing stop information
    for route_ref, route in sorted(routes.iteritems()):
        fill_stops(stops, route)

    for stop in stops.values():
        if stop.name == Stop.NO_NAME:
            stop.get_interim_stop_name()
            print stop

    # save stops
    with open('data/stops.pkl', 'wb') as f:
        pickle.dump(stops, f, pickle.HIGHEST_PROTOCOL)

    return stops


def fill_stops(stops, route):
    if isinstance(route, Route):
        i = 0
        for stop in route.stops:
            if stop.id in stops:
                route.stops[i] = stops[stop.id]
            else:
                stop.get_all_data()
                stops[stop.id] = stop
                route.stops[i] = stop
            i += 1
    elif isinstance(route, RouteMaster):
        for sub_route_ref, sub_route in route.routes.iteritems():
            fill_stops(stops, sub_route)
    else:
        raise RuntimeError("Unknown Route: " + str(route))


def get_stops_of_route(route_id):
    api = overpy.Overpass()

    result = api.query("""
    <id-query ref="%s" type="relation"/>
    <print/>
    """ % str(route_id))

    if len(result.get_relations()) == 0:
        raise RuntimeError(
            "Route not found: https://www.openstreetmap.org/relation/" + str(route_id))

    stops = []

    for member in result.get_relation(route_id, resolve_missing=True).members:
        if member.role.startswith('platform'):
            stop = Stop.from_relation_member(member)
            stops.append(stop)
        elif CHECK_FOR_NON_PLATFORMS:
            # It is possible bus_stops are not properly set to role=platform*

            if member.role == "forward" or member.role == "backward":
                continue

            print "Looking for bus stops without proper role in relation..."

            complete_member = member.resolve(resolve_missing=True)
            tags = complete_member.tags

            if isinstance(member, overpy.RelationNode):
                if 'highway' in tags and tags['highway'] == 'bus_stop':
                    stop = Stop.from_relation_member(member)
                    stops.append(stop)
                    sys.stderr.write("Node has no platform* role in relation " +
                                     str(route_id) + ": https://www.openstreetmap.org/node/" +
                                     str(member.ref) + "\n")
            elif isinstance(member, overpy.RelationWay):
                if 'amenity' in tags and tags['amenity'] == 'bus_station':
                    stop = Stop.from_relation_member(member)
                    stops.append(stop)
                    sys.stderr.write("Way has no platform* role in relation " + str(route_id) +
                                     ": https://www.openstreetmap.org/way/" + str(member.ref) +
                                     "\n")

    return stops


def refresh_route(route_ref):
    route_masters = get_route_masters()
    routes = get_routes()

    api = overpy.Overpass()
    result = api.query("""
    <query type="relation">
        <has-kv k="route" v="bus"/>
        <has-kv k="ref" v="%s"/>
        <bbox-query e="-48.27117919921875" n="-27.215556209029675" s="-27.94103350326715" w="-49.0155029296875"/>
    </query>
    <print/>
    """ % str(route_ref))

    if route_ref in route_masters:
        # TODO also refresh route master
        print route_masters[route_ref]
    elif route_ref in routes:
        print str(routes[route_ref])
    elif len(result.get_relations()) == 0:
        sys.stderr.write("No route %s found" % route_ref)
        return

    for rel in result.get_relations():
        print get_route(routes, route_masters, rel, warn=False)

    save_routes_to_file(routes)
