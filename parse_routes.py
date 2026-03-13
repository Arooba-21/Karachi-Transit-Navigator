"""
Phase 1 - Step 1: Parse Bus Routes PDF → routes.csv
=====================================================
Reads the Karachi bus routes PDF and outputs a clean CSV with columns:
    route_id | stop_name | stop_order

Run: python parse_routes.py
Output: data/routes.csv
"""

import re
import csv
import pdfplumber

PDF_PATH = "data/Bus-Routes-Karachi.pdf"
OUTPUT_PATH = "data/routes.csv"


def clean_stop(stop: str) -> str:
    """Normalize a stop name: strip whitespace, fix common spacing issues."""
    stop = stop.strip()
    stop = re.sub(r'\s+', ' ', stop)   # collapse multiple spaces
    return stop


def parse_pdf(pdf_path: str) -> dict:
    """
    Extract all routes from the PDF.
    Returns: { route_id: [stop1, stop2, ...], ... }
    """
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += "\n" + text

    routes = {}

    # Split on "Route #:" to isolate each route block
    blocks = re.split(r'Route\s*#\s*:', full_text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split('\n')
        if not lines:
            continue

        # First line is the route ID
        route_id = lines[0].strip()
        # Remove trailing/leading junk from route ID
        route_id = re.sub(r'\s+', ' ', route_id).strip()

        # Find the stops section - everything after "Stops:"
        stops_text = ""
        found_stops = False
        for line in lines[1:]:
            if re.match(r'^\s*Stops\s*:', line, re.IGNORECASE):
                # Get text after "Stops:" on same line
                after = re.sub(r'^\s*Stops\s*:\s*', '', line, flags=re.IGNORECASE)
                stops_text += after + " "
                found_stops = True
            elif found_stops:
                stops_text += line + " "

        if not stops_text.strip():
            continue

        # Split stops by comma
        raw_stops = stops_text.split(',')
        stops = []
        for s in raw_stops:
            cleaned = clean_stop(s)
            # Filter out obvious noise (URLs, empty, page numbers)
            if cleaned and len(cleaned) > 1 and not cleaned.startswith('http'):
                stops.append(cleaned)

        if route_id and stops:
            # Handle duplicate route IDs by appending a suffix
            if route_id in routes:
                suffix = 2
                while f"{route_id}_v{suffix}" in routes:
                    suffix += 1
                route_id = f"{route_id}_v{suffix}"
            routes[route_id] = stops

    return routes


def save_csv(routes: dict, output_path: str):
    """Save parsed routes to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['route_id', 'stop_name', 'stop_order'])
        for route_id, stops in routes.items():
            for order, stop in enumerate(stops, start=1):
                writer.writerow([route_id, stop, order])
    print(f"✅ Saved {len(routes)} routes to {output_path}")


def print_summary(routes: dict):
    """Print a quick summary so you can verify the parsing."""
    total_stops = sum(len(v) for v in routes.values())
    print(f"\n📊 PARSING SUMMARY")
    print(f"   Routes found  : {len(routes)}")
    print(f"   Total stops   : {total_stops}")
    print(f"   Avg stops/route: {total_stops // len(routes)}")
    print(f"\n📋 SAMPLE (first 5 routes):")
    for i, (route_id, stops) in enumerate(routes.items()):
        if i >= 5:
            break
        print(f"   [{route_id}] → {', '.join(stops[:4])} ...")


if __name__ == "__main__":
    print("🚌 Parsing Karachi Bus Routes PDF...")
    routes = parse_pdf(PDF_PATH)
    print_summary(routes)
    save_csv(routes, OUTPUT_PATH)
