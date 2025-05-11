# ship_route_optimizer.py
# Ship route optimization with real-time marine data and Folium visualization

import networkx as nx
import math
import requests
import folium

# Haversine formula to compute nautical miles between two (lat, lon)
def haversine(coord1, coord2):
    R = 3440.1  # Earth radius in nautical miles
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Example ship configuration class
class Ship:
    def __init__(self, base_speed=15, fuel_rate=1.5, wave_limit=3.0):
        self.base_speed = base_speed  # knots
        self.fuel_rate = fuel_rate    # tons/hour
        self.wave_limit = wave_limit  # meters
        self.max_speed = base_speed

# Use Open-Meteo API for real-time marine wave height (mocked fallback)
def get_wave(lat, lon):
    try:
        url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&hourly=wave_height&windspeed_unit=kn"
        response = requests.get(url)
        data = response.json()
        return data['hourly']['wave_height'][0]  # First hour
    except:
        return 2.0  # fallback wave height in meters

# Dummy current vector (use real current API later)
def get_current_vector(lat, lon):
    return (0.5, 0.0)  # (east, north) in knots

# Create grid graph with environmental weights
def build_graph(grid, ship):
    G = nx.DiGraph()
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            lat1, lon1 = grid[i][j]
            for di, dj in [(-1,0), (1,0), (0,-1), (0,1)]:
                ni, nj = i+di, j+dj
                if 0 <= ni < len(grid) and 0 <= nj < len(grid[0]):
                    lat2, lon2 = grid[ni][nj]
                    dist = haversine((lat1, lon1), (lat2, lon2))

                    current_east, current_north = get_current_vector(lat1, lon1)
                    wave_height = get_wave(lat1, lon1)

                    effective_speed = ship.base_speed + current_east
                    if wave_height > ship.wave_limit:
                        effective_speed *= 0.6  # reduce speed in high waves

                    effective_speed = max(effective_speed, 2.0)
                    time_h = dist / effective_speed
                    fuel = ship.fuel_rate * time_h

                    cost = time_h + 0.5 * fuel
                    G.add_edge((i, j), (ni, nj), weight=cost, time=time_h, fuel=fuel)
    return G

# A* heuristic: haversine distance divided by max speed
def heuristic(a, b, ship):
    return haversine(a, b) / ship.max_speed

# Convert grid path to lat/lon coordinates
def path_to_coords(path, grid):
    return [grid[i][j] for (i, j) in path]

# Plot ship route using Folium
def plot_route(static_coords, dynamic_coords):
    m = folium.Map(location=static_coords[0], zoom_start=5)
    folium.PolyLine(static_coords, color='blue', weight=2.5, tooltip='Static Route').add_to(m)
    folium.PolyLine(dynamic_coords, color='red', weight=2.5, tooltip='Dynamic Route').add_to(m)
    folium.Marker(static_coords[0], popup='Start', icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(dynamic_coords[-1], popup='End', icon=folium.Icon(color='red')).add_to(m)
    m.save('ship_routes.html')

# Main function to run static and dynamic route planning
def plan_routes():
    grid = [[(-10 + i, 60 + j) for j in range(5)] for i in range(5)]
    ship = Ship()

    G = build_graph(grid, ship)
    source = (0, 0)
    target = (4, 4)

    print("--- Static Routing (Dijkstra) ---")
    dijkstra_path = nx.dijkstra_path(G, source, target, weight='weight')
    print("Dijkstra Path:", dijkstra_path)

    print("\n--- Dynamic Routing (A*) ---")
    current_pos = (2, 2)
    goal_coord = grid[target[0]][target[1]]
    a_star_path = nx.astar_path(
        G,
        current_pos,
        target,
        heuristic=lambda a, b: heuristic(grid[a[0]][a[1]], goal_coord, ship),
        weight='weight')
    print("A* Path:", a_star_path)

    static_coords = path_to_coords(dijkstra_path, grid)
    dynamic_coords = path_to_coords(a_star_path, grid)
    plot_route(static_coords, dynamic_coords)

if __name__ == "__main__":
    plan_routes()