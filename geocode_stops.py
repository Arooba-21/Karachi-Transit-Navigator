"""
Phase 1 - Step 2: Geocode all unique stops → stops.csv
=======================================================
Uses Nominatim (OpenStreetMap) — completely FREE, no API key needed.

IMPORTANT: This script adds ", Karachi" to every stop name so the geocoder
knows we're searching in Karachi, not somewhere else in the world.

Rate limit: Nominatim allows 1 request/second. With ~800 unique stops
this will take ~15-20 minutes. The script saves progress as it goes,
so if it stops you can resume without losing work.

Run: python geocode_stops.py
Output: data/stops.csv
"""

import csv
import time
import json
import os
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

ROUTES_CSV = "data/routes.csv"
OUTPUT_CSV = "data/stops.csv"
CACHE_FILE = "data/geocode_cache.json"


def load_unique_stops(routes_csv: str) -> list:
    """Get all unique stop names from routes.csv."""
    stops = set()
    with open(routes_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stops.add(row['stop_name'].strip())
    return sorted(list(stops))


def load_cache(cache_file: str) -> dict:
    """Load previously geocoded results to avoid re-querying."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache: dict, cache_file: str):
    """Save geocoding cache to disk."""
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def geocode_stop(stop_name: str) -> tuple:
    """
    Query Nominatim for lat/lng of a stop in Karachi.
    Returns: (latitude, longitude) or (None, None) if not found.
    """
    query = f"{stop_name}, Karachi, Pakistan"
    encoded = quote(query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1&countrycodes=pk"

    headers = {
        'User-Agent': 'KarachiBusRouteApp/1.0 (portfolio project)'
    }

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except (URLError, Exception):
        pass

    return None, None


def geocode_all_stops(stops: list, cache: dict) -> dict:
    """
    Geocode all stops. Uses cache to skip already-processed ones.
    Returns updated cache dict.
    """
    total = len(stops)
    to_process = [s for s in stops if s not in cache]

    print(f"📍 Total unique stops : {total}")
    print(f"✅ Already cached     : {total - len(to_process)}")
    print(f"🔄 Need to geocode    : {len(to_process)}")

    if not to_process:
        print("Nothing to do — all stops already cached!")
        return cache

    print(f"\n⏳ Starting geocoding (1 request/second, ~{len(to_process) // 60} mins)...")
    print("   Progress saves every 50 stops. Safe to Ctrl+C and resume.\n")

    found = 0
    not_found = 0

    for i, stop in enumerate(to_process, start=1):
        lat, lon = geocode_stop(stop)

        if lat and lon:
            cache[stop] = {"lat": lat, "lon": lon}
            found += 1
            status = f"✅ {lat:.4f}, {lon:.4f}"
        else:
            cache[stop] = {"lat": None, "lon": None}
            not_found += 1
            status = "❌ not found"

        print(f"  [{i}/{len(to_process)}] {stop[:45]:<45} {status}")

        # Save progress every 50 stops
        if i % 50 == 0:
            save_cache(cache, CACHE_FILE)
            print(f"\n  💾 Progress saved ({i}/{len(to_process)})\n")

        # Nominatim rate limit: 1 request per second
        time.sleep(1)

    save_cache(cache, CACHE_FILE)
    print(f"\n📊 Geocoding complete: {found} found, {not_found} not found")
    return cache


def save_stops_csv(stops: list, cache: dict, output_csv: str):
    """Write final stops.csv with lat/lng from cache."""
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['stop_name', 'latitude', 'longitude'])
        for stop in stops:
            entry = cache.get(stop, {})
            lat = entry.get('lat', '')
            lon = entry.get('lon', '')
            writer.writerow([stop, lat, lon])

    # Count how many have coordinates
    with_coords = sum(1 for s in stops if cache.get(s, {}).get('lat'))
    print(f"\n✅ Saved stops.csv: {with_coords}/{len(stops)} stops have coordinates")


if __name__ == "__main__":
    print("🗺  Karachi Bus Stop Geocoder")
    print("=" * 45)

    stops = load_unique_stops(ROUTES_CSV)
    cache = load_cache(CACHE_FILE)
    cache = geocode_all_stops(stops, cache)
    save_stops_csv(stops, cache, OUTPUT_CSV)

    print(f"\n🎉 Done! Check data/stops.csv")
    print("    Next step: run  python build_graph.py  (Phase 2)")
