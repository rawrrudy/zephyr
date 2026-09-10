from pathlib import Path
import math
import numpy as np
import pandas as pd


# ============================================================
# EXP-02D-C
# ============================================================

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "spatial_coverage"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. Candidate station coordinates
#    Format: latitude, longitude
# ------------------------------------------------------------

stations = {
    "Alandi": (18.675076, 73.892743),
    "Bhosari": (18.640051, 73.848956),
    "Bhukum Nagar": (18.605770, 73.749976),
    "Dhankawadi": (18.459883, 73.852193),
    "Hadapsar": (18.501793, 73.927532),
    "Karve Road": (18.501174, 73.816553),
    "Katraj Dairy": (18.454450, 73.854155),
    "Mhada Colony": (18.573040, 73.927715),
    "Panchawati/Pashan": (18.536457, 73.805454),
    "Revenue Colony/Shivajinagar": (18.530085, 73.849598),
    "SPPU": (18.547056, 73.826908),
    "Transport Nagar/Nigdi": (18.664282, 73.763966),
}


# ------------------------------------------------------------
# 2. Geographic utilities
# ------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two latitude/longitude points.
    """
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def latlon_to_xy(lat, lon, lat0, lon0):
    """
    Local equirectangular approximation.
    Converts latitude/longitude to kilometres relative to
    a reference point.
    """
    x = (
        math.radians(lon - lon0)
        * EARTH_RADIUS_KM
        * math.cos(math.radians(lat0))
    )

    y = math.radians(lat - lat0) * EARTH_RADIUS_KM

    return x, y


def xy_to_latlon(x, y, lat0, lon0):
    """
    Inverse of latlon_to_xy().
    """
    lat = lat0 + math.degrees(y / EARTH_RADIUS_KM)

    lon = lon0 + math.degrees(
        x / (EARTH_RADIUS_KM * math.cos(math.radians(lat0)))
    )

    return lat, lon


# ------------------------------------------------------------
# 3. Convert stations to local Cartesian coordinates
# ------------------------------------------------------------

station_names = list(stations.keys())

station_lats = np.array([stations[name][0] for name in station_names])
station_lons = np.array([stations[name][1] for name in station_names])

lat0 = float(np.mean(station_lats))
lon0 = float(np.mean(station_lons))

station_xy = np.array(
    [
        latlon_to_xy(lat, lon, lat0, lon0)
        for lat, lon in zip(station_lats, station_lons)
    ]
)


# ------------------------------------------------------------
# 4. Construct the convex hull using monotonic chain
# ------------------------------------------------------------

def cross(o, a, b):
    """
    2D cross product used by the convex hull algorithm.
    """
    return (
        (a[0] - o[0]) * (b[1] - o[1])
        - (a[1] - o[1]) * (b[0] - o[0])
    )


def convex_hull(points):
    """
    Return points forming the convex hull in counter-clockwise order.
    """
    points = sorted(set(map(tuple, points)))

    if len(points) <= 1:
        return points

    lower = []

    for point in points:
        while len(lower) >= 2 and cross(
            lower[-2], lower[-1], point
        ) <= 0:
            lower.pop()

        lower.append(point)

    upper = []

    for point in reversed(points):
        while len(upper) >= 2 and cross(
            upper[-2], upper[-1], point
        ) <= 0:
            upper.pop()

        upper.append(point)

    return lower[:-1] + upper[:-1]


hull_xy = convex_hull(station_xy)


# ------------------------------------------------------------
# 5. Point-in-polygon test
# ------------------------------------------------------------

def point_in_polygon(x, y, polygon):
    """
    Ray-casting point-in-polygon test.
    Boundary points are treated as inside.
    """
    inside = False
    n = len(polygon)

    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]

        # Boundary check
        cross_value = (
            (y - y1) * (x2 - x1)
            - (x - x1) * (y2 - y1)
        )

        if abs(cross_value) < 1e-10:
            if (
                min(x1, x2) - 1e-10 <= x <= max(x1, x2) + 1e-10
                and min(y1, y2) - 1e-10 <= y <= max(y1, y2) + 1e-10
            ):
                return True

        if (y1 > y) != (y2 > y):
            intersection_x = (
                (x2 - x1) * (y - y1) / (y2 - y1)
                + x1
            )

            if x < intersection_x:
                inside = not inside

    return inside


# ------------------------------------------------------------
# 6. Generate approximately 500 m grid
# ------------------------------------------------------------

GRID_SPACING_KM = 0.5

hull_x = [point[0] for point in hull_xy]
hull_y = [point[1] for point in hull_xy]

min_x = min(hull_x)
max_x = max(hull_x)
min_y = min(hull_y)
max_y = max(hull_y)

x_values = np.arange(
    min_x,
    max_x + GRID_SPACING_KM,
    GRID_SPACING_KM,
)

y_values = np.arange(
    min_y,
    max_y + GRID_SPACING_KM,
    GRID_SPACING_KM,
)


# ------------------------------------------------------------
# 7. Keep only grid points inside the station defined area
# ------------------------------------------------------------

grid_points = []

for x in x_values:
    for y in y_values:

        if point_in_polygon(x, y, hull_xy):
            lat, lon = xy_to_latlon(
                x, y, lat0, lon0
            )

            grid_points.append(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "x_km": x,
                    "y_km": y,
                }
            )


# ------------------------------------------------------------
# 8. Calculate nearest station distance
# ------------------------------------------------------------

results = []

for point in grid_points:

    lat = point["latitude"]
    lon = point["longitude"]

    distances = []

    for station_name, (station_lat, station_lon) in stations.items():
        distance = haversine_km(
            lat,
            lon,
            station_lat,
            station_lon,
        )

        distances.append(
            (distance, station_name)
        )

    nearest_distance, nearest_station = min(
        distances,
        key=lambda item: item[0]
    )

    results.append(
        {
            "latitude": lat,
            "longitude": lon,
            "nearest_station": nearest_station,
            "nearest_station_distance_km": nearest_distance,
        }
    )


df = pd.DataFrame(results)


# ------------------------------------------------------------
# 9. Summary statistics
# ------------------------------------------------------------

distances = df["nearest_station_distance_km"]

summary = {
    "station_count": len(stations),
    "grid_spacing_km": GRID_SPACING_KM,
    "study_area_grid_points": len(df),

    "mean_nearest_station_distance_km": distances.mean(),
    "median_nearest_station_distance_km": distances.median(),
    "minimum_nearest_station_distance_km": distances.min(),
    "maximum_nearest_station_distance_km": distances.max(),

    "q25_nearest_station_distance_km": distances.quantile(0.25),
    "q75_nearest_station_distance_km": distances.quantile(0.75),
    "q90_nearest_station_distance_km": distances.quantile(0.90),
    "q95_nearest_station_distance_km": distances.quantile(0.95),

    "within_1km_percent":
        (distances <= 1).mean() * 100,

    "within_2km_percent":
        (distances <= 2).mean() * 100,

    "within_5km_percent":
        (distances <= 5).mean() * 100,

    "within_10km_percent":
        (distances <= 10).mean() * 100,
}


# ------------------------------------------------------------
# 10. Print results
# ------------------------------------------------------------

print()
print("=" * 65)
print("EXP-002D-C — STUDY-AREA CONSTRAINED COVERAGE")
print("=" * 65)

print()
print("Study-area definition:")
print("Convex hull of the 12 candidate monitoring stations")

print()
print(f"Grid spacing: {GRID_SPACING_KM:.3f} km")
print(f"Grid points inside study area: {len(df)}")

print()
print("--- Nearest-station distance ---")

print(
    f"Mean:     "
    f"{summary['mean_nearest_station_distance_km']:.6f} km"
)

print(
    f"Median:   "
    f"{summary['median_nearest_station_distance_km']:.6f} km"
)

print(
    f"Minimum:  "
    f"{summary['minimum_nearest_station_distance_km']:.6f} km"
)

print(
    f"Maximum:  "
    f"{summary['maximum_nearest_station_distance_km']:.6f} km"
)

print(
    f"Q25:      "
    f"{summary['q25_nearest_station_distance_km']:.6f} km"
)

print(
    f"Q75:      "
    f"{summary['q75_nearest_station_distance_km']:.6f} km"
)

print(
    f"Q90:      "
    f"{summary['q90_nearest_station_distance_km']:.6f} km"
)

print(
    f"Q95:      "
    f"{summary['q95_nearest_station_distance_km']:.6f} km"
)

print()
print("--- Coverage thresholds ---")

print(
    f"Within 1 km:  "
    f"{summary['within_1km_percent']:.6f}%"
)

print(
    f"Within 2 km:  "
    f"{summary['within_2km_percent']:.6f}%"
)

print(
    f"Within 5 km:  "
    f"{summary['within_5km_percent']:.6f}%"
)

print(
    f"Within 10 km: "
    f"{summary['within_10km_percent']:.6f}%"
)


# ------------------------------------------------------------
# 11. Nearest station assignment counts
# ------------------------------------------------------------

assignment_counts = (
    df["nearest_station"]
    .value_counts()
    .rename_axis("station")
    .reset_index(name="grid_points")
)

assignment_counts["percent_of_study_area"] = (
    assignment_counts["grid_points"]
    / len(df)
    * 100
)

print()
print("--- Nearest-station assignments ---")

for _, row in assignment_counts.iterrows():

    print(
        f"{row['station']}: "
        f"{int(row['grid_points'])} grid points "
        f"({row['percent_of_study_area']:.4f}%)"
    )


# ------------------------------------------------------------
# 12. Save outputs
# ------------------------------------------------------------

grid_output = (
    OUTPUT_DIR
    / "EXP-002D-C_Study_Area_Grid.csv"
)

summary_output = (
    OUTPUT_DIR
    / "EXP-002D-C_Summary.csv"
)

assignment_output = (
    OUTPUT_DIR
    / "EXP-002D-C_Nearest_Station_Assignment.csv"
)

hull_output = (
    OUTPUT_DIR
    / "EXP-002D-C_Convex_Hull.csv"
)


df.to_csv(grid_output, index=False)

pd.DataFrame(
    [summary]
).to_csv(
    summary_output,
    index=False
)

assignment_counts.to_csv(
    assignment_output,
    index=False
)


# Save hull coordinates
hull_latlon = []

for x, y in hull_xy:
    lat, lon = xy_to_latlon(
        x, y, lat0, lon0
    )

    hull_latlon.append(
        {
            "latitude": lat,
            "longitude": lon,
        }
    )

pd.DataFrame(hull_latlon).to_csv(
    hull_output,
    index=False
)


print()
print("=" * 65)
print("OUTPUT FILES")
print("=" * 65)

print(grid_output)
print(summary_output)
print(assignment_output)
print(hull_output)

print()
print("EXP-02D-C COMPLETE.")
print()