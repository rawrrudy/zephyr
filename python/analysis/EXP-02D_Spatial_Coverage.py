from pathlib import Path
from itertools import combinations
import math
import pandas as pd
import numpy as np


# ============================================================
# EXP-02D-A — STATION SPATIAL GEOMETRY
# ============================================================

PROJECT = Path(__file__).resolve().parents[1]

OUT_DIR = (
    PROJECT
    / "data"
    / "ground_stations"
    / "processed"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 1. STATION COORDINATES
# ------------------------------------------------------------

# Latitude, Longitude
# Karve Road has two published candidate coordinates.
# We will explicitly test both later.

stations = {
    "Alandi": (18.675076, 73.892743),
    "Bhosari": (18.640051, 73.848956),
    "Bhukum Nagar": (18.605770, 73.749976),
    "Dhankawadi": (18.459883, 73.852193),
    "Hadapsar": (18.501793, 73.927532),

    # Working coordinate from EXP-002B
    "Karve Road": (18.501174, 73.816553),

    "Katraj Dairy": (18.454450, 73.854155),
    "Mhada Colony": (18.573040, 73.927715),
    "Panchawati/Pashan": (18.536457, 73.805454),
    "Revenue Colony/Shivajinagar": (18.530085, 73.849598),
    "SPPU": (18.547056, 73.826908),
    "Transport Nagar/Nigdi": (18.664282, 73.763966),
}


# ------------------------------------------------------------
# 2. HAVERSINE DISTANCE
# ------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0088


def haversine(lat1, lon1, lat2, lon2):

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return EARTH_RADIUS_KM * c


# ------------------------------------------------------------
# 3. PAIRWISE DISTANCE MATRIX
# ------------------------------------------------------------

names = list(stations.keys())

distance_matrix = pd.DataFrame(
    index=names,
    columns=names,
    dtype=float
)


for a in names:

    for b in names:

        lat1, lon1 = stations[a]
        lat2, lon2 = stations[b]

        distance_matrix.loc[a, b] = haversine(
            lat1,
            lon1,
            lat2,
            lon2
        )


distance_matrix.to_csv(
    OUT_DIR / "EXP-002D_pairwise_distance_matrix_km.csv"
)


# ------------------------------------------------------------
# 4. NEAREST-NEIGHBOR DISTANCE
# ------------------------------------------------------------

nearest_results = []


for station in names:

    distances = distance_matrix.loc[
        station
    ].drop(station)

    nearest_station = distances.idxmin()
    nearest_distance = distances.min()

    nearest_results.append({

        "station": station,

        "nearest_station":
            nearest_station,

        "nearest_neighbor_distance_km":
            nearest_distance
    })


nearest_df = pd.DataFrame(
    nearest_results
).sort_values(
    "nearest_neighbor_distance_km",
    ascending=False
)


nearest_df.to_csv(
    OUT_DIR / "EXP-002D_nearest_neighbor_distances.csv",
    index=False
)


# ------------------------------------------------------------
# 5. NETWORK BOUNDING BOX
# ------------------------------------------------------------

latitudes = np.array(
    [coord[0] for coord in stations.values()]
)

longitudes = np.array(
    [coord[1] for coord in stations.values()]
)


min_lat = latitudes.min()
max_lat = latitudes.max()

min_lon = longitudes.min()
max_lon = longitudes.max()


# Approximate physical dimensions
north_south_km = haversine(
    min_lat,
    longitudes.mean(),
    max_lat,
    longitudes.mean()
)

east_west_km = haversine(
    latitudes.mean(),
    min_lon,
    latitudes.mean(),
    max_lon
)


# ------------------------------------------------------------
# 6. ARITHMETIC CENTROID
# ------------------------------------------------------------

centroid_lat = latitudes.mean()
centroid_lon = longitudes.mean()


# ------------------------------------------------------------
# 7. SUMMARY
# ------------------------------------------------------------

summary = pd.DataFrame([{

    "number_of_stations":
        len(stations),

    "minimum_latitude":
        min_lat,

    "maximum_latitude":
        max_lat,

    "minimum_longitude":
        min_lon,

    "maximum_longitude":
        max_lon,

    "latitude_span_degrees":
        max_lat - min_lat,

    "longitude_span_degrees":
        max_lon - min_lon,

    "approx_north_south_extent_km":
        north_south_km,

    "approx_east_west_extent_km":
        east_west_km,

    "centroid_latitude":
        centroid_lat,

    "centroid_longitude":
        centroid_lon
}])


summary.to_csv(
    OUT_DIR / "EXP-002D_network_summary.csv",
    index=False
)


# ------------------------------------------------------------
# 8. PRINT RESULTS
# ------------------------------------------------------------

print()
print("=" * 80)
print("EXP-002D-A — STATION SPATIAL GEOMETRY")
print("=" * 80)

print("\n--- NETWORK SUMMARY ---\n")

print(
    summary.to_string(index=False)
)


print("\n--- NEAREST-NEIGHBOR DISTANCES ---\n")

print(
    nearest_df.to_string(index=False)
)


print("\n--- PAIRWISE DISTANCE MATRIX (km) ---\n")

print(
    distance_matrix.round(3).to_string()
)


print()
print("=" * 80)
print("EXP-002D-A COMPLETE")
print("=" * 80)

print("\nResults saved to:")
print(OUT_DIR)