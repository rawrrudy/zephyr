from pathlib import Path
import math
import itertools
import pandas as pd
import numpy as np


# ============================================================
# EXP-02D-E
# CANDIDATE SENSOR PLACEMENT OPTIMIZATION
#
# Purpose:
# Identify candidate locations for 3 additional low-cost
# PM2.5 sensors that maximally improve spatial coverage of
# the existing monitoring network.
#
# Method:
# Greedy marginal spatial-coverage optimization.
#
# The algorithm:
#   1. Loads the EXP-02D-C study-area grid.
#   2. Loads the existing 12 station coordinates.
#   3. Calculates distance from every grid point to every
#      existing station.
#   4. Iteratively selects candidate sensor locations that
#      produce the greatest reduction in mean nearest-station
#      distance.
#   5. Requires each new sensor to be at least a minimum
#      separation distance from existing stations and from
#      previously selected sensors.
#   6. Compares the original network with the optimized
#      3-sensor network.
#
# IMPORTANT:
# These are mathematical candidate locations only.
# Final deployment requires field feasibility and safety
# verification.
# ============================================================


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SPATIAL_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "spatial_coverage"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sensor_placement"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# INPUT FILE
# ------------------------------------------------------------

GRID_FILE = (
    SPATIAL_DIR
    / "EXP-02D-C_Study_Area_Grid.csv"
)


# ------------------------------------------------------------
# SENSOR DESIGN
# ------------------------------------------------------------

NUMBER_OF_NEW_SENSORS = 3


# ------------------------------------------------------------
# CONSTRAINTS
# ------------------------------------------------------------

# Do not select a new candidate within 1 km of an existing
# monitoring station.
#
# This prevents the optimization from wasting a sensor on
# an already well-instrumented location.

MIN_DISTANCE_FROM_EXISTING_KM = 1.0


# Do not place two newly selected candidate locations within
# 2 km of each other.
#
# This encourages spatially distributed deployment.

MIN_DISTANCE_BETWEEN_NEW_SENSORS_KM = 2.0


# ------------------------------------------------------------
# EARTH MODEL
# ------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Great-circle distance between two geographic coordinates.
    """

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2.0) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2.0) ** 2
    )

    return (
        2.0
        * EARTH_RADIUS_KM
        * np.arcsin(
            np.sqrt(a)
        )
    )


# ------------------------------------------------------------
# EXISTING STATION COORDINATES
# ------------------------------------------------------------

STATIONS = {

    "Alandi":
        (18.675076, 73.892743),

    "Bhosari":
        (18.640051, 73.848956),

    "Bhukum Nagar":
        (18.605770, 73.749976),

    "Dhankawadi":
        (18.459883, 73.852193),

    "Hadapsar":
        (18.501793, 73.927532),

    "Karve Road":
        (18.501174, 73.816553),

    "Katraj Dairy":
        (18.454450, 73.854155),

    "Mhada Colony":
        (18.573040, 73.927715),

    "Panchawati/Pashan":
        (18.536457, 73.805454),

    "Revenue Colony/Shivajinagar":
        (18.530085, 73.849598),

    "SPPU":
        (18.547056, 73.826908),

    "Transport Nagar/Nigdi":
        (18.664282, 73.763966),
}


# ------------------------------------------------------------
# START
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-02D-E — SENSOR PLACEMENT OPTIMIZATION")
print("=" * 75)


# ------------------------------------------------------------
# CHECK GRID
# ------------------------------------------------------------

print()
print("--- Checking input ---")

print()
print(
    "Study-area grid:"
)

print(
    GRID_FILE
)


if not GRID_FILE.exists():

    raise FileNotFoundError(
        f"\nRequired grid file not found:\n"
        f"{GRID_FILE}\n\n"
        f"Run EXP-02D-Study_Area_Coverage.py first."
    )


# ------------------------------------------------------------
# LOAD GRID
# ------------------------------------------------------------

grid_df = pd.read_csv(
    GRID_FILE
)


required_columns = {
    "latitude",
    "longitude",
}


missing_columns = (
    required_columns
    - set(grid_df.columns)
)


if missing_columns:

    raise ValueError(
        "Grid is missing required columns:\n"
        + "\n".join(
            sorted(missing_columns)
        )
    )


grid_latitudes = (
    grid_df[
        "latitude"
    ]
    .to_numpy(
        dtype=float
    )
)


grid_longitudes = (
    grid_df[
        "longitude"
    ]
    .to_numpy(
        dtype=float
    )
)


number_of_grid_points = len(
    grid_df
)


print()
print(
    f"Grid points: "
    f"{number_of_grid_points:,}"
)


# ------------------------------------------------------------
# EXISTING STATION ARRAYS
# ------------------------------------------------------------

station_names = list(
    STATIONS.keys()
)


station_latitudes = np.array(
    [
        STATIONS[name][0]
        for name in station_names
    ],
    dtype=float
)


station_longitudes = np.array(
    [
        STATIONS[name][1]
        for name in station_names
    ],
    dtype=float
)


print(
    f"Existing stations: "
    f"{len(station_names)}"
)


# ------------------------------------------------------------
# DISTANCE: GRID → EXISTING STATIONS
# ------------------------------------------------------------

print()
print("=" * 75)
print("CALCULATING EXISTING NETWORK DISTANCES")
print("=" * 75)


# Shape:
#
# grid_points × existing_stations

grid_station_distances = np.zeros(
    (
        number_of_grid_points,
        len(station_names)
    ),
    dtype=float
)


for station_index in range(
    len(station_names)
):

    grid_station_distances[
        :,
        station_index
    ] = haversine_km(
        grid_latitudes,
        grid_longitudes,
        station_latitudes[
            station_index
        ],
        station_longitudes[
            station_index
        ]
    )


# Current nearest-station distance

current_nearest_distance = (
    grid_station_distances.min(
        axis=1
    )
)


current_nearest_station_index = (
    grid_station_distances.argmin(
        axis=1
    )
)


current_nearest_station = [
    station_names[index]
    for index in current_nearest_station_index
]


# ------------------------------------------------------------
# DISTANCE FROM CANDIDATE GRID POINTS TO EXISTING STATIONS
# ------------------------------------------------------------

# A candidate can only be selected if it is at least
# MIN_DISTANCE_FROM_EXISTING_KM away from every existing
# station.

minimum_existing_distance = (
    grid_station_distances.min(
        axis=1
    )
)


candidate_allowed = (
    minimum_existing_distance
    >= MIN_DISTANCE_FROM_EXISTING_KM
)


allowed_candidate_indices = np.where(
    candidate_allowed
)[0]


print()
print(
    f"Candidate grid points after "
    f"{MIN_DISTANCE_FROM_EXISTING_KM:.1f} km "
    f"existing-station exclusion: "
    f"{len(allowed_candidate_indices):,}"
)


if len(allowed_candidate_indices) == 0:

    raise RuntimeError(
        "No candidate grid points remain after "
        "the existing-station distance constraint."
    )


# ------------------------------------------------------------
# FUNCTION: COVERAGE METRICS
# ------------------------------------------------------------

def calculate_metrics(
    nearest_distances
):
    """
    Calculate spatial coverage statistics.
    """

    return {

        "mean_nearest_distance_km":
            float(
                np.mean(
                    nearest_distances
                )
            ),

        "median_nearest_distance_km":
            float(
                np.median(
                    nearest_distances
                )
            ),

        "minimum_nearest_distance_km":
            float(
                np.min(
                    nearest_distances
                )
            ),

        "maximum_nearest_distance_km":
            float(
                np.max(
                    nearest_distances
                )
            ),

        "within_1km_percent":
            float(
                np.mean(
                    nearest_distances
                    <= 1.0
                )
                * 100
            ),

        "within_2km_percent":
            float(
                np.mean(
                    nearest_distances
                    <= 2.0
                )
                * 100
            ),

        "within_5km_percent":
            float(
                np.mean(
                    nearest_distances
                    <= 5.0
                )
                * 100
            ),
    }


# ------------------------------------------------------------
# BASELINE
# ------------------------------------------------------------

baseline_metrics = calculate_metrics(
    current_nearest_distance
)


print()
print("=" * 75)
print("BASELINE NETWORK")
print("=" * 75)


for metric, value in baseline_metrics.items():

    print(
        f"{metric}: "
        f"{value:.6f}"
    )


# ------------------------------------------------------------
# GREEDY OPTIMIZATION
# ------------------------------------------------------------

print()
print("=" * 75)
print("GREEDY SENSOR PLACEMENT")
print("=" * 75)


selected_indices = []

optimized_nearest_distance = (
    current_nearest_distance.copy()
)


selection_records = []


for sensor_number in range(
    1,
    NUMBER_OF_NEW_SENSORS + 1
):

    best_candidate_index = None
    best_candidate_mean_distance = (
        float("inf")
    )
    best_candidate_updated_distances = None


    # --------------------------------------------------------
    # Evaluate every currently permitted candidate.
    # --------------------------------------------------------

    for candidate_index in allowed_candidate_indices:

        # Do not select a candidate twice.

        if candidate_index in selected_indices:
            continue


        # ----------------------------------------------------
        # Enforce minimum separation from already selected
        # new sensors.
        # ----------------------------------------------------

        candidate_is_too_close = False


        for selected_index in selected_indices:

            distance_between_candidates = (
                haversine_km(
                    grid_latitudes[
                        candidate_index
                    ],
                    grid_longitudes[
                        candidate_index
                    ],
                    grid_latitudes[
                        selected_index
                    ],
                    grid_longitudes[
                        selected_index
                    ]
                )
            )


            if (
                distance_between_candidates
                < MIN_DISTANCE_BETWEEN_NEW_SENSORS_KM
            ):

                candidate_is_too_close = True

                break


        if candidate_is_too_close:
            continue


        # ----------------------------------------------------
        # What would the nearest-station distance become if
        # this candidate sensor were added?
        # ----------------------------------------------------

        candidate_distances = haversine_km(
            grid_latitudes,
            grid_longitudes,
            grid_latitudes[
                candidate_index
            ],
            grid_longitudes[
                candidate_index
            ]
        )


        updated_distances = np.minimum(
            optimized_nearest_distance,
            candidate_distances
        )


        updated_mean = (
            np.mean(
                updated_distances
            )
        )


        # ----------------------------------------------------
        # Select candidate that minimizes mean nearest distance.
        # ----------------------------------------------------

        if (
            updated_mean
            < best_candidate_mean_distance
        ):

            best_candidate_mean_distance = (
                updated_mean
            )

            best_candidate_index = (
                candidate_index
            )

            best_candidate_updated_distances = (
                updated_distances
            )


    # --------------------------------------------------------
    # Verify a candidate was found.
    # --------------------------------------------------------

    if best_candidate_index is None:

        raise RuntimeError(
            f"Unable to select sensor #{sensor_number}. "
            f"Try reducing the candidate separation constraint."
        )


    # --------------------------------------------------------
    # Commit selection.
    # --------------------------------------------------------

    selected_indices.append(
        best_candidate_index
    )


    optimized_nearest_distance = (
        best_candidate_updated_distances
    )


    candidate_latitude = (
        grid_latitudes[
            best_candidate_index
        ]
    )

    candidate_longitude = (
        grid_longitudes[
            best_candidate_index
        ]
    )


    # Distance to nearest existing station

    distance_to_existing = (
        minimum_existing_distance[
            best_candidate_index
        ]
    )


    # Distance to previous new sensor

    if len(selected_indices) > 1:

        previous_distances = [

            haversine_km(
                candidate_latitude,
                candidate_longitude,
                grid_latitudes[
                    previous_index
                ],
                grid_longitudes[
                    previous_index
                ]
            )

            for previous_index
            in selected_indices[:-1]
        ]

        minimum_distance_to_new_sensor = min(
            previous_distances
        )

    else:

        minimum_distance_to_new_sensor = None


    metrics_after_selection = calculate_metrics(
        optimized_nearest_distance
    )


    mean_improvement = (
        baseline_metrics[
            "mean_nearest_distance_km"
        ]
        -
        metrics_after_selection[
            "mean_nearest_distance_km"
        ]
    )


    print()
    print(
        f"Sensor #{sensor_number}"
    )

    print(
        f"  Latitude: "
        f"{candidate_latitude:.6f}"
    )

    print(
        f"  Longitude: "
        f"{candidate_longitude:.6f}"
    )

    print(
        f"  Distance from existing network: "
        f"{distance_to_existing:.6f} km"
    )

    if (
        minimum_distance_to_new_sensor
        is not None
    ):

        print(
            f"  Distance from nearest new sensor: "
            f"{minimum_distance_to_new_sensor:.6f} km"
        )

    print(
        f"  Mean nearest distance after placement: "
        f"{metrics_after_selection['mean_nearest_distance_km']:.6f} km"
    )

    print(
        f"  Mean-distance improvement from baseline: "
        f"{mean_improvement:.6f} km"
    )


    selection_records.append(
        {
            "sensor_number":
                sensor_number,

            "grid_index":
                best_candidate_index,

            "latitude":
                candidate_latitude,

            "longitude":
                candidate_longitude,

            "distance_to_existing_network_km":
                distance_to_existing,

            "minimum_distance_to_other_new_sensor_km":
                minimum_distance_to_new_sensor,

            "mean_nearest_distance_after_placement_km":
                metrics_after_selection[
                    "mean_nearest_distance_km"
                ],

            "maximum_nearest_distance_after_placement_km":
                metrics_after_selection[
                    "maximum_nearest_distance_km"
                ],

            "within_1km_percent_after_placement":
                metrics_after_selection[
                    "within_1km_percent"
                ],

            "within_2km_percent_after_placement":
                metrics_after_selection[
                    "within_2km_percent"
                ],

            "within_5km_percent_after_placement":
                metrics_after_selection[
                    "within_5km_percent"
                ],
        }
    )


# ------------------------------------------------------------
# FINAL OPTIMIZED METRICS
# ------------------------------------------------------------

optimized_metrics = calculate_metrics(
    optimized_nearest_distance
)


print()
print("=" * 75)
print("FINAL 3-SENSOR NETWORK")
print("=" * 75)


print()
print("--- Baseline → Optimized ---")


for metric in baseline_metrics:

    baseline_value = (
        baseline_metrics[metric]
    )

    optimized_value = (
        optimized_metrics[metric]
    )

    improvement = (
        optimized_value
        - baseline_value
    )


    print()
    print(metric)

    print(
        f"  Baseline:  "
        f"{baseline_value:.6f}"
    )

    print(
        f"  Optimized: "
        f"{optimized_value:.6f}"
    )

    print(
        f"  Change:    "
        f"{improvement:+.6f}"
    )


# ------------------------------------------------------------
# GRID-POINT ASSIGNMENT AFTER OPTIMIZATION
# ------------------------------------------------------------

all_sensor_names = (
    station_names
    + [
        f"New Sensor {i}"
        for i in range(
            1,
            NUMBER_OF_NEW_SENSORS + 1
        )
    ]
)


selected_candidate_coordinates = [

    (
        grid_latitudes[index],
        grid_longitudes[index]
    )

    for index
    in selected_indices
]


new_sensor_distance_matrix = np.zeros(
    (
        number_of_grid_points,
        NUMBER_OF_NEW_SENSORS
    ),
    dtype=float
)


for sensor_index, (
    sensor_latitude,
    sensor_longitude
) in enumerate(
    selected_candidate_coordinates
):

    new_sensor_distance_matrix[
        :,
        sensor_index
    ] = haversine_km(
        grid_latitudes,
        grid_longitudes,
        sensor_latitude,
        sensor_longitude
    )


all_distances_after = np.column_stack(
    [
        grid_station_distances,
        new_sensor_distance_matrix
    ]
)


nearest_index_after = (
    all_distances_after.argmin(
        axis=1
    )
)


nearest_distance_after = (
    all_distances_after.min(
        axis=1
    )
)


nearest_source_after = [
    all_sensor_names[index]
    for index in nearest_index_after
]


assignment_df = pd.DataFrame(
    {
        "latitude":
            grid_latitudes,

        "longitude":
            grid_longitudes,

        "baseline_nearest_station":
            current_nearest_station,

        "baseline_nearest_distance_km":
            current_nearest_distance,

        "optimized_nearest_source":
            nearest_source_after,

        "optimized_nearest_distance_km":
            nearest_distance_after,

        "distance_reduction_km":
            (
                current_nearest_distance
                -
                nearest_distance_after
            ),
    }
)


# ------------------------------------------------------------
# SENSOR SUMMARY
# ------------------------------------------------------------

sensor_summary_df = pd.DataFrame(
    selection_records
)


# ------------------------------------------------------------
# METRICS TABLE
# ------------------------------------------------------------

metrics_rows = []


for stage, metrics in [
    (
        "baseline_12_station_network",
        baseline_metrics
    ),
    (
        "optimized_12_plus_3_network",
        optimized_metrics
    ),
]:

    row = {
        "network_stage":
            stage
    }

    row.update(
        metrics
    )

    metrics_rows.append(
        row
    )


metrics_df = pd.DataFrame(
    metrics_rows
)


# ------------------------------------------------------------
# OPTIMIZATION PARAMETERS
# ------------------------------------------------------------

parameters_df = pd.DataFrame(
    [
        {
            "number_of_new_sensors":
                NUMBER_OF_NEW_SENSORS,

            "minimum_distance_from_existing_km":
                MIN_DISTANCE_FROM_EXISTING_KM,

            "minimum_distance_between_new_sensors_km":
                MIN_DISTANCE_BETWEEN_NEW_SENSORS_KM,

            "candidate_grid_points":
                len(allowed_candidate_indices),

            "study_area_grid_points":
                number_of_grid_points,

            "optimization_objective":
                "Minimize mean nearest-station distance",
        }
    ]
)


# ------------------------------------------------------------
# SAVE OUTPUTS
# ------------------------------------------------------------

SENSOR_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-E_Selected_Sensor_Candidates.csv"
)

METRICS_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-E_Coverage_Comparison.csv"
)

ASSIGNMENT_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-E_Grid_Assignment.csv"
)

PARAMETERS_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-E_Optimization_Parameters.csv"
)


sensor_summary_df.to_csv(
    SENSOR_OUTPUT,
    index=False
)


metrics_df.to_csv(
    METRICS_OUTPUT,
    index=False
)


assignment_df.to_csv(
    ASSIGNMENT_OUTPUT,
    index=False
)


parameters_df.to_csv(
    PARAMETERS_OUTPUT,
    index=False
)


# ------------------------------------------------------------
# FINAL OUTPUT
# ------------------------------------------------------------

print()
print("=" * 75)
print("SELECTED CANDIDATE SENSOR LOCATIONS")
print("=" * 75)


for _, row in sensor_summary_df.iterrows():

    print()

    print(
        f"Sensor #{int(row['sensor_number'])}:"
    )

    print(
        f"  Latitude: "
        f"{row['latitude']:.6f}"
    )

    print(
        f"  Longitude: "
        f"{row['longitude']:.6f}"
    )

    print(
        f"  Distance from existing network: "
        f"{row['distance_to_existing_network_km']:.3f} km"
    )


print()
print("=" * 75)
print("OUTPUT FILES")
print("=" * 75)

print()
print(SENSOR_OUTPUT)

print(
    METRICS_OUTPUT
)

print(
    ASSIGNMENT_OUTPUT
)

print(
    PARAMETERS_OUTPUT
)


print()
print("=" * 75)
print("EXP-02D-E COMPLETE")
print("=" * 75)
print()