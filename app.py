"""
Phase 3 — Flask Web App
========================
Routes:
    GET  /                          → main search page
    GET  /api/search?from=X&to=Y    → route search results (JSON)
    GET  /api/stops?q=query         → fuzzy stop search (JSON)
    GET  /api/bus/<route_id>        → all stops on a route (JSON)
    GET  /api/stop/<stop_name>      → all buses at a stop (JSON)
    GET  /api/all_stops             → all stops with coords (JSON, for map)
"""

from flask import Flask, render_template, request, jsonify
import csv
import os
from route_finder import (
    load_routes, build_stop_to_routes,
    find_direct_routes, find_indirect_routes,
    search_stops, get_stop_buses, get_route_stops
)

app = Flask(__name__)

# ── Load data once at startup ──────────────────────────────────────────────────
print("🚌 Loading bus route data...")
ROUTES        = load_routes()
STOP_TO_ROUTES = build_stop_to_routes(ROUTES)
ALL_STOPS     = sorted(STOP_TO_ROUTES.keys())

def load_stops_with_coords():
    stops = {}
    path = os.path.join("data", "stops.csv")
    if not os.path.exists(path):
        return stops
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['latitude'] and row['longitude']:
                stops[row['stop_name']] = {
                    "lat": float(row['latitude']),
                    "lon": float(row['longitude'])
                }
    return stops

STOPS_COORDS = load_stops_with_coords()
print(f"✅ Ready — {len(ROUTES)} routes, {len(ALL_STOPS)} stops, {len(STOPS_COORDS)} with coordinates")


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API ────────────────────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    source = request.args.get("from", "").strip()
    dest   = request.args.get("to", "").strip()

    if not source or not dest:
        return jsonify({"error": "Please provide both 'from' and 'to' stops"}), 400

    # Fuzzy-match to nearest real stop name
    source_match = search_stops(source, ALL_STOPS, max_results=1)
    dest_match   = search_stops(dest,   ALL_STOPS, max_results=1)

    if not source_match:
        return jsonify({"error": f"Stop not found: '{source}'"}), 404
    if not dest_match:
        return jsonify({"error": f"Stop not found: '{dest}'"}), 404

    source_name = source_match[0]
    dest_name   = dest_match[0]

    direct   = find_direct_routes(source_name, dest_name, ROUTES)
    indirect = find_indirect_routes(source_name, dest_name, ROUTES, STOP_TO_ROUTES)

    # Add coordinate hints for map highlighting
    def enrich_direct(r):
        stops = get_route_stops(r["route"], ROUTES)
        return {**r, "stops": stops}

    def enrich_indirect(r):
        stops_a = get_route_stops(r["route_a"], ROUTES)
        stops_b = get_route_stops(r["route_b"], ROUTES)
        return {**r, "stops_a": stops_a, "stops_b": stops_b}

    return jsonify({
        "source"  : source_name,
        "dest"    : dest_name,
        "direct"  : [enrich_direct(r) for r in direct],
        "indirect": [enrich_indirect(r) for r in indirect]
    })


@app.route("/api/stops")
def api_stops():
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify([])
    results = search_stops(query, ALL_STOPS, max_results=8)
    return jsonify(results)


@app.route("/api/bus/<path:route_id>")
def api_bus(route_id):
    # Try exact match first, then case-insensitive
    stops = get_route_stops(route_id, ROUTES)
    matched_id = route_id
    if not stops:
        route_id_lower = route_id.lower()
        for rid in ROUTES:
            if rid.lower() == route_id_lower:
                stops = ROUTES[rid]
                matched_id = rid
                break
    if not stops:
        return jsonify({"error": f"Route '{route_id}' not found. Try the autocomplete dropdown."}), 404
    coords = [STOPS_COORDS.get(s, {}) for s in stops]
    return jsonify({"route_id": matched_id, "stops": stops, "coords": coords})


@app.route("/api/stop/<path:stop_name>")
def api_stop(stop_name):
    buses = get_stop_buses(stop_name, STOP_TO_ROUTES)
    coord = STOPS_COORDS.get(stop_name, {})
    return jsonify({"stop": stop_name, "buses": buses, "coord": coord})


@app.route("/api/all_routes")
def api_all_routes():
    return jsonify(sorted(ROUTES.keys()))


@app.route("/api/bus-search")
def api_bus_search():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify([])
    matches = [r for r in ROUTES.keys() if q in r.lower()]
    return jsonify(sorted(matches)[:10])


@app.route("/api/all_stops")
def api_all_stops():
    result = []
    for stop_name, coord in STOPS_COORDS.items():
        buses = STOP_TO_ROUTES.get(stop_name, [])
        result.append({
            "name" : stop_name,
            "lat"  : coord["lat"],
            "lon"  : coord["lon"],
            "buses": buses[:6]  # cap for performance
        })
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)