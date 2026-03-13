"""
Phase 2a — Build the Route Graph
=================================
Creates a NetworkX graph where:
    Nodes = bus stops
    Edges = a bus route connects two consecutive stops

Run standalone to verify: python build_graph.py
"""

import csv
import pickle
import networkx as nx
from collections import defaultdict

ROUTES_CSV = "data/routes.csv"
GRAPH_FILE  = "data/bus_graph.pkl"


def load_routes(routes_csv: str) -> dict:
    routes = defaultdict(list)
    with open(routes_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = sorted(reader, key=lambda r: (r['route_id'], int(r['stop_order'])))
        for row in rows:
            routes[row['route_id']].append(row['stop_name'].strip())
    return dict(routes)


def build_graph(routes: dict) -> nx.MultiGraph:
    G = nx.MultiGraph()
    for route_id, stops in routes.items():
        for i in range(len(stops) - 1):
            G.add_edge(stops[i], stops[i + 1], route=route_id)
    return G


def build_stop_to_routes(routes: dict) -> dict:
    stop_routes = defaultdict(set)
    for route_id, stops in routes.items():
        for stop in stops:
            stop_routes[stop].add(route_id)
    return {stop: sorted(list(rts)) for stop, rts in stop_routes.items()}


def save_graph(G, graph_file: str):
    with open(graph_file, 'wb') as f:
        pickle.dump(G, f)
    print(f"✅ Graph saved to {graph_file}")


def load_graph(graph_file: str) -> nx.MultiGraph:
    with open(graph_file, 'rb') as f:
        return pickle.load(f)


def print_graph_summary(G, routes):
    print(f"\n📊 GRAPH SUMMARY")
    print(f"   Nodes (unique stops) : {G.number_of_nodes()}")
    print(f"   Edges (connections)  : {G.number_of_edges()}")
    print(f"   Routes               : {len(routes)}")
    degree = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    print(f"\n🔗 TOP 10 HUB STOPS:")
    for stop, deg in degree[:10]:
        print(f"   {stop:<40} {deg} connections")


if __name__ == "__main__":
    print("🔨 Building route graph...")
    routes = load_routes(ROUTES_CSV)
    G = build_graph(routes)
    stop_to_routes = build_stop_to_routes(routes)
    print_graph_summary(G, routes)
    save_graph(G, GRAPH_FILE)
    print(f"\n🧪 SANITY CHECK — stops connected to 'Tower':")
    if "Tower" in G:
        print(f"   {list(G.neighbors('Tower'))[:8]}")
