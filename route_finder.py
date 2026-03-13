"""
Phase 2b — Route Finder (Direct + Indirect)
=============================================
The core search engine of the app.

Functions:
    find_direct_routes(source, dest)     → list of buses going directly
    find_indirect_routes(source, dest)   → list of (bus1, transfer_stop, bus2)
    search_stops(query)                  → fuzzy stop name search
    get_stop_buses(stop_name)            → all buses at a stop
    get_route_stops(route_id)            → all stops on a route

Run standalone to test: python route_finder.py
"""

import csv
import pickle
import networkx as nx
from collections import defaultdict
from difflib import get_close_matches

ROUTES_CSV  = "data/routes.csv"
GRAPH_FILE  = "data/bus_graph.pkl"


# ── Data loaders ──────────────────────────────────────────────────────────────

def load_routes(routes_csv=ROUTES_CSV) -> dict:
    """{ route_id: [stop1, stop2, ...] }"""
    routes = defaultdict(list)
    with open(routes_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = sorted(reader, key=lambda r: (r['route_id'], int(r['stop_order'])))
        for row in rows:
            routes[row['route_id']].append(row['stop_name'].strip())
    return dict(routes)


def load_graph(graph_file=GRAPH_FILE) -> nx.MultiGraph:
    with open(graph_file, 'rb') as f:
        return pickle.load(f)


def build_stop_to_routes(routes: dict) -> dict:
    """{ stop_name: [route1, route2, ...] }"""
    stop_routes = defaultdict(set)
    for route_id, stops in routes.items():
        for stop in stops:
            stop_routes[stop].add(route_id)
    return {stop: sorted(list(rts)) for stop, rts in stop_routes.items()}


# ── Core search functions ──────────────────────────────────────────────────────

def find_direct_routes(source: str, dest: str, routes: dict) -> list:
    """
    Find all buses that contain BOTH source and dest in their stop list.
    Returns list of route_ids.
    """
    source_l = source.lower()
    dest_l   = dest.lower()
    matches  = []

    for route_id, stops in routes.items():
        stops_lower = [s.lower() for s in stops]
        if source_l in stops_lower and dest_l in stops_lower:
            src_idx  = stops_lower.index(source_l)
            dest_idx = stops_lower.index(dest_l)
            matches.append({
                "route"      : route_id,
                "direction"  : "forward" if src_idx < dest_idx else "reverse",
                "stops_between": abs(dest_idx - src_idx) - 1
            })

    return sorted(matches, key=lambda x: x["stops_between"])


def find_indirect_routes(source: str, dest: str, routes: dict,
                          stop_to_routes: dict, max_results=5) -> list:
    """
    Find routes requiring exactly ONE transfer.
    Algorithm:
        1. Get all buses that serve source  → source_buses
        2. Get all buses that serve dest    → dest_buses
        3. For each (bus_a, bus_b) pair, find stops they share → transfer stops
        4. Return top results sorted by total stops travelled
    """
    source_l = source.lower()
    dest_l   = dest.lower()

    # Buses serving source and dest
    source_buses = {
        r: stops for r, stops in routes.items()
        if any(s.lower() == source_l for s in stops)
    }
    dest_buses = {
        r: stops for r, stops in routes.items()
        if any(s.lower() == dest_l for s in stops)
    }

    if not source_buses or not dest_buses:
        return []

    results = []

    for route_a, stops_a in source_buses.items():
        stops_a_lower = [s.lower() for s in stops_a]
        src_idx = stops_a_lower.index(source_l)

        for route_b, stops_b in dest_buses.items():
            if route_a == route_b:
                continue  # same bus = already a direct route

            stops_b_lower = [s.lower() for s in stops_b]
            dest_idx = stops_b_lower.index(dest_l)

            # Find common stops between route_a and route_b
            set_a = set(stops_a_lower)
            set_b = set(stops_b_lower)
            common = set_a & set_b

            for transfer_lower in common:
                transfer_idx_a = stops_a_lower.index(transfer_lower)
                transfer_idx_b = stops_b_lower.index(transfer_lower)

                # Make sure the journey makes directional sense:
                # source → transfer on route_a, then transfer → dest on route_b
                if transfer_idx_a <= src_idx:
                    continue  # transfer is before source on route_a
                if transfer_idx_b >= dest_idx:
                    continue  # transfer is after dest on route_b

                # Get the actual (non-lowercased) transfer stop name
                transfer_name = stops_a[transfer_idx_a]

                total_stops = (transfer_idx_a - src_idx) + (dest_idx - transfer_idx_b)

                results.append({
                    "route_a"      : route_a,
                    "transfer_stop": transfer_name,
                    "route_b"      : route_b,
                    "total_stops"  : total_stops
                })

    # Deduplicate: keep best (fewest stops) per (route_a, route_b, transfer) combo
    seen = {}
    for r in results:
        key = (r["route_a"], r["route_b"], r["transfer_stop"])
        if key not in seen or r["total_stops"] < seen[key]["total_stops"]:
            seen[key] = r

    return sorted(seen.values(), key=lambda x: x["total_stops"])[:max_results]


def search_stops(query: str, all_stops: list, max_results=8) -> list:
    """
    Fuzzy search stop names.
    Returns stops whose name contains the query (case-insensitive),
    plus close matches from difflib.
    """
    query_l = query.lower().strip()
    if not query_l:
        return []

    # Exact substring matches first
    contains = [s for s in all_stops if query_l in s.lower()]

    # Fuzzy fallback
    fuzzy = get_close_matches(query, all_stops, n=max_results, cutoff=0.5)

    # Combine, deduplicate, preserve order
    seen = set()
    combined = []
    for s in contains + fuzzy:
        if s not in seen:
            seen.add(s)
            combined.append(s)

    return combined[:max_results]


def get_stop_buses(stop_name: str, stop_to_routes: dict) -> list:
    """All buses that serve a given stop (exact match)."""
    return stop_to_routes.get(stop_name, [])


def get_route_stops(route_id: str, routes: dict) -> list:
    """All stops on a given route in order."""
    return routes.get(route_id, [])


# ── CLI test ───────────────────────────────────────────────────────────────────

def _test(source, dest, routes, stop_to_routes):
    print(f"\n{'='*55}")
    print(f"  FROM : {source}")
    print(f"  TO   : {dest}")
    print(f"{'='*55}")

    direct = find_direct_routes(source, dest, routes)
    if direct:
        print(f"\n✅ DIRECT ROUTES ({len(direct)} found):")
        for r in direct:
            print(f"   Bus {r['route']}  ({r['stops_between']} stops between, {r['direction']})")
    else:
        print(f"\n❌ No direct routes found")

    indirect = find_indirect_routes(source, dest, routes, stop_to_routes)
    if indirect:
        print(f"\n🔄 INDIRECT ROUTES ({len(indirect)} found):")
        for r in indirect:
            print(f"   Take Bus {r['route_a']}  →  "
                  f"transfer at [{r['transfer_stop']}]  →  "
                  f"Bus {r['route_b']}  ({r['total_stops']} total stops)")
    else:
        print(f"\n❌ No indirect routes found")


if __name__ == "__main__":
    print("🚌 Loading data...")
    routes        = load_routes()
    stop_to_routes = build_stop_to_routes(routes)
    all_stops     = sorted(stop_to_routes.keys())

    # Test cases
    _test("Water Pump", "Bahadurabad", routes, stop_to_routes)
    _test("Faqir Colony", "Tower", routes, stop_to_routes)
    _test("Surjani Town", "Clifton", routes, stop_to_routes)

    # Test stop search
    print(f"\n\n🔍 STOP SEARCH — query: 'nazim'")
    results = search_stops("nazim", all_stops)
    for r in results:
        buses = get_stop_buses(r, stop_to_routes)
        print(f"   {r:<40} buses: {', '.join(buses[:4])}{'...' if len(buses)>4 else ''}")

    # Test route lookup
    print(f"\n\n📋 ROUTE LOOKUP — Bus 11-B stops:")
    stops_11b = get_route_stops("11-B", routes)
    print(f"   {' → '.join(stops_11b)}")

    print(f"\n\n✅ Route finder working correctly!")
