from pathlib import Path
import math
import pandas as pd
import numpy as np


# ============================================================
# EXP 02D B — SPATIAL COVERAGE GAP ANALYSIS
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
# 3. STUDY REGION
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


# ------------------------------------------------------------
# 4. CREATE REGULAR GRID
# ------------------------------------------------------------

# Approx 500 m grid spacing.

# At Pune's latitude:
#   0.005 degrees latitude  ≈ 0.56 km
#   0.005 degrees longitude ≈ 0.53 km

GRID_STEP = 0.005


grid_latitudes = np.arange(
    min_lat,
    max_lat + GRID_STEP,
    GRID_STEP
)

grid_longitudes = np.arange(
    min_lon,
    max_lon + GRID_STEP,
    GRID_STEP
)


# ------------------------------------------------------------
# 5. CALCULATE DISTANCE TO NEAREST STATION
# ------------------------------------------------------------

grid_results = []


for lat in grid_latitudes:

    for lon in grid_longitudes:

        distances = {}

        for station, (station_lat, station_lon) in stations.items():

            distances[station] = haversine(
                lat,
                lon,
                station_lat,
                station_lon
            )

        nearest_station = min(
            distances,
            key=distances.get
        )

        nearest_distance = distances[
            nearest_station
        ]

        grid_results.append({

            "latitude":
                lat,

            "longitude":
                lon,

            "nearest_station":
                nearest_station,

            "nearest_station_distance_km":
                nearest_distance
        })


grid_df = pd.DataFrame(grid_results)


# ------------------------------------------------------------
# 6. SAVE GRID
# ------------------------------------------------------------

grid_df.to_csv(
    OUT_DIR / "EXP-002D_spatial_coverage_grid.csv",
    index=False
)


# ------------------------------------------------------------
# 7. SUMMARY STATISTICS
# ------------------------------------------------------------

distances = grid_df[
    "nearest_station_distance_km"
]


summary = pd.DataFrame([{

    "grid_points":
        len(grid_df),

    "grid_step_degrees":
        GRID_STEP,

    "mean_nearest_station_distance_km":
        distances.mean(),

    "median_nearest_station_distance_km":
        distances.median(),

    "minimum_nearest_station_distance_km":
        distances.min(),

    "maximum_nearest_station_distance_km":
        distances.max(),

    "q25_nearest_station_distance_km":
        distances.quantile(0.25),

    "q75_nearest_station_distance_km":
        distances.quantile(0.75),

    "q90_nearest_station_distance_km":
        distances.quantile(0.90),

    "q95_nearest_station_distance_km":
        distances.quantile(0.95),

}])


# ------------------------------------------------------------
# 8. COVERAGE THRESHOLDS
# ------------------------------------------------------------

thresholds_km = [
    1,
    2,
    5,
    10
]


threshold_results = []


for threshold in thresholds_km:

    covered = (
        distances <= threshold
    ).sum()

    percentage = (
        covered
        / len(distances)
        * 100
    )

    threshold_results.append({

        "threshold_km":
            threshold,

        "grid_points_within_threshold":
            int(covered),

        "percentage_of_grid_within_threshold":
            percentage
    })


threshold_df = pd.DataFrame(
    threshold_results
)


summary = pd.concat(
    [
        summary,
        threshold_df
    ],
    axis=1
)


# ------------------------------------------------------------
# 9. GRID POINT EXTREMES
# ------------------------------------------------------------

worst_points = (
    grid_df
    .sort_values(
        "nearest_station_distance_km",
        ascending=False
    )
    .head(20)
)


worst_points.to_csv(
    OUT_DIR / "EXP-002D_largest_spatial_gaps.csv",
    index=False
)


# ------------------------------------------------------------
# 10. NEAREST STATION AREA DISTRIBUTION
# ------------------------------------------------------------

station_assignment = (
    grid_df
    .groupby("nearest_station")
    .size()
    .reset_index(
        name="grid_points_assigned"
    )
)


station_assignment[
    "percentage_of_grid"
] = (
    station_assignment[
        "grid_points_assigned"
    ]
    / len(grid_df)
    * 100
)


station_assignment.to_csv(
    OUT_DIR / "EXP-002D_nearest_station_grid_assignment.csv",
    index=False
)


# ------------------------------------------------------------
# 11. SAVE SUMMARY
# ------------------------------------------------------------

summary.to_csv(
    OUT_DIR / "EXP-002D_spatial_gap_summary.csv",
    index=False
)


# ------------------------------------------------------------
# 12. PRINT RESULTS
# ------------------------------------------------------------

print()
print("=" * 80)
print("EXP-002D-B — SPATIAL COVERAGE GAP ANALYSIS")
print("=" * 80)


print("\n--- COVERAGE SUMMARY ---\n")

print(
    summary.to_string(index=False)
)


print("\n--- 20 LARGEST SPATIAL GAPS ---\n")

print(
    worst_points.to_string(index=False)
)


print("\n--- GRID ASSIGNMENT BY NEAREST STATION ---\n")

print(
    station_assignment
    .sort_values(
        "grid_points_assigned",
        ascending=False
    )
    .to_string(index=False)
)


print()
print("=" * 80)
print("EXP-02D-B COMPLETE")
print("=" * 80)

print("\nResults saved to:")
print(OUT_DIR)
