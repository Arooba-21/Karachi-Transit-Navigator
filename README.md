# Karachi-Transit-Navigator
Web app to find bus routes across Karachi search by stop name, get direct & transfer routes, visualize on an interactive map.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?style=flat-square&logo=flask)
![NetworkX](https://img.shields.io/badge/NetworkX-graph-orange?style=flat-square)
![Leaflet](https://img.shields.io/badge/Leaflet.js-map-green?style=flat-square&logo=leaflet)
---

## The Problem

Karachi has one of the largest informal bus networks in the world hundreds of routes, thousands of stops and almost none of it is online. There's no app, no GTFS feed, no official map. If you don't already know which bus to take, you have to ask someone.
This project is an attempt to fix that.

---

## What It Does

**Route Search**: Enter a source and destination stop. The app finds:
- All **direct buses** between the two stops, sorted by fewest stops between them
- All **indirect routes** requiring one transfer, showing exactly where to switch buses

**Find Stop**: Search any stop name and see every bus that serves it, with a map flyover to its location.

**Bus Lookup**: Enter a bus number and see its full route plotted on the map, stop by stop.

**Interactive Map**: 1,097 stops plotted on a dark Leaflet map with:
- Hover tooltip showing stop name on any dot
- Auto-labels that appear when you zoom into a neighbourhood
- Permanent labels on whichever route you have selected
- Transfer stops highlighted in teal

---

## Project Structure

```
karachi-bus-finder/
├── app.py                 
├── parse_routes.py         
├── geocode_stops.py        
├── build_graph.py         
├── route_finder.py         
├── templates/
│   └── index.html          
├── data/
│   ├── routes.csv               # 344 routes, 5,698 stop entries
│   ├── stops.csv                # 1,947 unique stops with coords
│   ├── geocode_cache.json      
│   └── bus_graph.pkl            
└── requirements.txt
```

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/karachi-bus-finder.git
cd karachi-bus-finder
```

**2. Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate      # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
python app.py
```

**5. Open in browser**
```
http://127.0.0.1:5000
```

> The data files (`routes.csv`, `stops.csv`, `bus_graph.pkl`) are included — no need to re-run the parsing or geocoding steps.

---

### Dataset
⚠️ This data is ~15 years old. Routes, stops, and bus numbers may have changed significantly. This is a portfolio and research tool, not a live transit guide. Do not rely on it for actual navigation.

## Requirements

```
flask
pandas
networkx
pdfplumber
```
---

## Possible Improvements

- [ ] Updated route data (2024+)
- [ ] Mobile-responsive layout
- [ ] Multi-transfer routing (2+ changes)
- [ ] Journey time estimates
- [ ] Fare information
- [ ] PWA / offline support

---

*Built as a portfolio project to demonstrate data engineering, graph algorithms, and full-stack Python development.*
