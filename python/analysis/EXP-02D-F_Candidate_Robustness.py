from pathlib import Path
import math
import itertools
import pandas as pd
import numpy as np


# ============================================================
# EXP-02D-F
# CANDIDATE SENSOR LOCATION ROBUSTNESS ANALYSIS
#
# Purpose:
# Determine whether the sensor locations selected by
# EXP-02D-E represent robust spatial regions or merely
# isolated optimal grid points.
#
# Method:
# For each selected candidate:
#
#   1. Identify all study-area grid points within 1 km.
#   2. Evaluate each nearby point as an alternative location.
#   3. Calculate the resulting network coverage metrics.
#   4. Compare the selected point with its local alternatives.
#
# Additionally:
#
#   Each of the three selected sensors is independently
#   perturbed to nearby candidate locations while the other
#   two selected sensors remain fixed.
#
# This evaluates robustness of the COMPLETE 3-sensor network.
#
# IMPORTANT:
# This is a mathematical robustness analysis.
# It does NOT establish field feasibility.
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

PLACEMENT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sensor_placement"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sensor_robustness"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# INPUT FILES
# ------------------------------------------------------------

GRID_FILE = (
    SPATIAL_DIR
    / "EXP-02D-C_Study_Area_Grid.csv"
)

SELECTED_FILE = (
    PLACEMENT_DIR
    / "EXP-02D-E_Selected_Sensor_Candidates.csv"
)


# ------------------------------------------------------------
# ROBUSTNESS PARAMETERS
# ------------------------------------------------------------

# Radius around each selected candidate within which alternative
# grid locations are evaluated.

ROBUSTNESS_RADIUS_KM = 1.0


# Minimum distance between newly deployed sensors.

MIN_NEW_SENSOR_SEPARATION_KM = 2.0


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
    Calculate great-circle distance between geographic
    coordinates.
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
# EXISTING STATIONS
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
# LOAD INPUTS
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-02D-F — CANDIDATE SENSOR LOCATION ROBUSTNESS")
print("=" * 75)


print()
print("--- Checking input files ---")

print()
print("Study-area grid:")
print(GRID_FILE)

if not GRID_FILE.exists():

    raise FileNotFoundError(
        f"\nRequired grid file not found:\n{GRID_FILE}"
    )


print()
print("Selected sensor candidates:")
print(SELECTED_FILE)

if not SELECTED_FILE.exists():

    raise FileNotFoundError(
        f"\nRequired candidate file not found:\n{SELECTED_FILE}"
    )


# ------------------------------------------------------------
# LOAD GRID
# ------------------------------------------------------------

grid_df = pd.read_csv(
    GRID_FILE
)


required_grid_columns = {
    "latitude",
    "longitude",
}


missing_grid_columns = (
    required_grid_columns
    - set(grid_df.columns)
)


if missing_grid_columns:

    raise ValueError(
        "Study-area grid is missing:\n"
        + "\n".join(
            sorted(missing_grid_columns)
        )
    )


grid_lat = (
    grid_df[
        "latitude"
    ]
    .to_numpy(
        dtype=float
    )
)


grid_lon = (
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


# ------------------------------------------------------------
# LOAD SELECTED CANDIDATES
# ------------------------------------------------------------

selected_df = pd.read_csv(
    SELECTED_FILE
)


required_selected_columns = {
    "sensor_number",
    "latitude",
    "longitude",
}


missing_selected_columns = (
    required_selected_columns
    - set(selected_df.columns)
)


if missing_selected_columns:

    raise ValueError(
        "Selected candidate file is missing:\n"
        + "\n".join(
            sorted(missing_selected_columns)
        )
    )


selected_df = (
    selected_df
    .sort_values(
        "sensor_number"
    )
    .reset_index(
        drop=True
    )
)


if len(selected_df) != 3:

    raise ValueError(
        "Expected exactly 3 optimized sensor candidates, "
        f"but found {len(selected_df)}."
    )


selected_candidates = [

    (
        int(row["sensor_number"]),
        float(row["latitude"]),
        float(row["longitude"])
    )

    for _, row
    in selected_df.iterrows()
]


print()
print(
    f"Study-area grid points: "
    f"{number_of_grid_points:,}"
)

print(
    f"Selected candidates: "
    f"{len(selected_candidates)}"
)


# ------------------------------------------------------------
# EXISTING STATION DISTANCE MATRIX
# ------------------------------------------------------------

station_names = list(
    STATIONS.keys()
)


station_lat = np.array(
    [
        STATIONS[name][0]
        for name in station_names
    ],
    dtype=float
)


station_lon = np.array(
    [
        STATIONS[name][1]
        for name in station_names
    ],
    dtype=float
)


existing_distances = np.zeros(
    (
        number_of_grid_points,
        len(station_names)
    ),
    dtype=float
)


for i in range(
    len(station_names)
):

    existing_distances[
        :,
        i
    ] = haversine_km(
        grid_lat,
        grid_lon,
        station_lat[i],
        station_lon[i]
    )


baseline_nearest = (
    existing_distances.min(
        axis=1
    )
)


# ------------------------------------------------------------
# METRIC FUNCTION
# ------------------------------------------------------------

def calculate_metrics(
    nearest_distances
):

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

        "maximum_nearest_distance_km":
            float(
                np.max(
                    nearest_distances
                )
            ),

        "within_1km_percent":
            float(
                np.mean(
                    nearest_distances <= 1.0
                )
                * 100
            ),

        "within_2km_percent":
            float(
                np.mean(
                    nearest_distances <= 2.0
                )
                * 100
            ),

        "within_5km_percent":
            float(
                np.mean(
                    nearest_distances <= 5.0
                )
                * 100
            ),
    }


baseline_metrics = calculate_metrics(
    baseline_nearest
)


# ------------------------------------------------------------
# EVALUATE A SINGLE CANDIDATE
# ------------------------------------------------------------

def evaluate_single_candidate(
    latitude,
    longitude
):

    candidate_distance = haversine_km(
        grid_lat,
        grid_lon,
        latitude,
        longitude
    )


    updated_nearest = np.minimum(
        baseline_nearest,
        candidate_distance
    )


    metrics = calculate_metrics(
        updated_nearest
    )


    metrics[
        "improvement_mean_distance_km"
    ] = (
        baseline_metrics[
            "mean_nearest_distance_km"
        ]
        -
        metrics[
            "mean_nearest_distance_km"
        ]
    )


    return metrics


# ------------------------------------------------------------
# LOCAL ROBUSTNESS ANALYSIS
# ------------------------------------------------------------

print()
print("=" * 75)
print("LOCAL ROBUSTNESS ANALYSIS")
print("=" * 75)


local_results = []


for (
    sensor_number,
    selected_latitude,
    selected_longitude
) in selected_candidates:


    # --------------------------------------------------------
    # Find study-area grid points within robustness radius.
    # --------------------------------------------------------

    distances_to_selected = haversine_km(
        grid_lat,
        grid_lon,
        selected_latitude,
        selected_longitude
    )


    local_indices = np.where(
        distances_to_selected
        <= ROBUSTNESS_RADIUS_KM
    )[0]


    print()
    print(
        f"Sensor #{sensor_number}"
    )

    print(
        f"Selected location: "
        f"{selected_latitude:.6f}, "
        f"{selected_longitude:.6f}"
    )

    print(
        f"Nearby grid alternatives within "
        f"{ROBUSTNESS_RADIUS_KM:.1f} km: "
        f"{len(local_indices)}"
    )


    if len(local_indices) == 0:

        raise RuntimeError(
            f"No nearby grid alternatives found "
            f"for sensor #{sensor_number}."
        )


    # --------------------------------------------------------
    # Evaluate each local alternative.
    # --------------------------------------------------------

    for candidate_index in local_indices:

        candidate_latitude = (
            grid_lat[
                candidate_index
            ]
        )

        candidate_longitude = (
            grid_lon[
                candidate_index
            ]
        )


        distance_from_selected = (
            distances_to_selected[
                candidate_index
            ]
        )


        metrics = evaluate_single_candidate(
            candidate_latitude,
            candidate_longitude
        )


        is_original = (
            distance_from_selected
            < 1e-9
        )


        local_results.append(
            {

                "sensor_number":
                    sensor_number,

                "candidate_grid_index":
                    int(candidate_index),

                "candidate_latitude":
                    candidate_latitude,

                "candidate_longitude":
                    candidate_longitude,

                "distance_from_selected_km":
                    distance_from_selected,

                "is_original_selected_location":
                    is_original,

                "mean_nearest_distance_km":
                    metrics[
                        "mean_nearest_distance_km"
                    ],

                "median_nearest_distance_km":
                    metrics[
                        "median_nearest_distance_km"
                    ],

                "maximum_nearest_distance_km":
                    metrics[
                        "maximum_nearest_distance_km"
                    ],

                "within_1km_percent":
                    metrics[
                        "within_1km_percent"
                    ],

                "within_2km_percent":
                    metrics[
                        "within_2km_percent"
                    ],

                "within_5km_percent":
                    metrics[
                        "within_5km_percent"
                    ],

                "improvement_mean_distance_km":
                    metrics[
                        "improvement_mean_distance_km"
                    ],
            }
        )


local_results_df = pd.DataFrame(
    local_results
)


# ------------------------------------------------------------
# LOCAL ROBUSTNESS SUMMARY
# ------------------------------------------------------------

local_summary = []


for sensor_number in range(
    1,
    4
):

    subset = local_results_df[
        local_results_df[
            "sensor_number"
        ]
        == sensor_number
    ]


    original = subset[
        subset[
            "is_original_selected_location"
        ]
    ]


    if original.empty:

        raise RuntimeError(
            f"Original selected point for "
            f"sensor #{sensor_number} "
            f"was not found in local grid."
        )


    original_mean = float(
        original[
            "mean_nearest_distance_km"
        ].iloc[0]
    )


    local_mean_values = (
        subset[
            "mean_nearest_distance_km"
        ]
    )


    local_improvements = (
        subset[
            "improvement_mean_distance_km"
        ]
    )


    best_index = (
        subset[
            "mean_nearest_distance_km"
        ]
        .idxmin()
    )


    worst_index = (
        subset[
            "mean_nearest_distance_km"
        ]
        .idxmax()
    )


    best_row = subset.loc[
        best_index
    ]

    worst_row = subset.loc[
        worst_index
    ]


    local_summary.append(
        {

            "sensor_number":
                sensor_number,

            "local_alternative_count":
                len(subset),

            "original_mean_nearest_distance_km":
                original_mean,

            "local_mean_nearest_distance_min_km":
                local_mean_values.min(),

            "local_mean_nearest_distance_median_km":
                local_mean_values.median(),

            "local_mean_nearest_distance_max_km":
                local_mean_values.max(),

            "local_improvement_min_km":
                local_improvements.min(),

            "local_improvement_median_km":
                local_improvements.median(),

            "local_improvement_max_km":
                local_improvements.max(),

            "best_local_latitude":
                best_row[
                    "candidate_latitude"
                ],

            "best_local_longitude":
                best_row[
                    "candidate_longitude"
                ],

            "best_local_distance_from_original_km":
                best_row[
                    "distance_from_selected_km"
                ],

            "worst_local_latitude":
                worst_row[
                    "candidate_latitude"
                ],

            "worst_local_longitude":
                worst_row[
                    "candidate_longitude"
                ],

            "worst_local_distance_from_original_km":
                worst_row[
                    "distance_from_selected_km"
                ],
        }
    )


local_summary_df = pd.DataFrame(
    local_summary
)


# ------------------------------------------------------------
# THREE-SENSOR NETWORK ROBUSTNESS
# ------------------------------------------------------------

print()
print("=" * 75)
print("THREE-SENSOR NETWORK ROBUSTNESS")
print("=" * 75)


# Original three selected sensor coordinates

original_sensor_coordinates = [

    (
        latitude,
        longitude
    )

    for (
        _,
        latitude,
        longitude
    )
    in selected_candidates
]


three_sensor_results = []


for (
    perturbed_sensor_number,
    selected_latitude,
    selected_longitude
) in selected_candidates:


    distances_to_selected = haversine_km(
        grid_lat,
        grid_lon,
        selected_latitude,
        selected_longitude
    )


    local_indices = np.where(
        distances_to_selected
        <= ROBUSTNESS_RADIUS_KM
    )[0]


    for candidate_index in local_indices:

        candidate_latitude = (
            grid_lat[
                candidate_index
            ]
        )

        candidate_longitude = (
            grid_lon[
                candidate_index
            ]
        )


        # ----------------------------------------------------
        # Build perturbed three-sensor configuration.
        # ----------------------------------------------------

        perturbed_coordinates = []


        for sensor_number, (
            original_latitude,
            original_longitude
        ) in enumerate(
            original_sensor_coordinates,
            start=1
        ):

            if (
                sensor_number
                == perturbed_sensor_number
            ):

                perturbed_coordinates.append(
                    (
                        candidate_latitude,
                        candidate_longitude
                    )
                )

            else:

                perturbed_coordinates.append(
                    (
                        original_latitude,
                        original_longitude
                    )
                )


        # ----------------------------------------------------
        # Check minimum separation between new sensors.
        # ----------------------------------------------------

        valid_separation = True


        for pair_a, pair_b in itertools.combinations(
            perturbed_coordinates,
            2
        ):

            separation = haversine_km(
                pair_a[0],
                pair_a[1],
                pair_b[0],
                pair_b[1]
            )


            if (
                separation
                < MIN_NEW_SENSOR_SEPARATION_KM
            ):

                valid_separation = False

                break


        if not valid_separation:
            continue


        # ----------------------------------------------------
        # Calculate nearest distance using existing stations
        # plus all three new sensors.
        # ----------------------------------------------------

        optimized_distances = (
            baseline_nearest.copy()
        )


        for (
            sensor_latitude,
            sensor_longitude
        ) in perturbed_coordinates:

            sensor_distance = haversine_km(
                grid_lat,
                grid_lon,
                sensor_latitude,
                sensor_longitude
            )


            optimized_distances = np.minimum(
                optimized_distances,
                sensor_distance
            )


        metrics = calculate_metrics(
            optimized_distances
        )


        three_sensor_results.append(
            {

                "perturbed_sensor_number":
                    perturbed_sensor_number,

                "candidate_grid_index":
                    int(candidate_index),

                "candidate_latitude":
                    candidate_latitude,

                "candidate_longitude":
                    candidate_longitude,

                "distance_from_original_km":
                    distances_to_selected[
                        candidate_index
                    ],

                "mean_nearest_distance_km":
                    metrics[
                        "mean_nearest_distance_km"
                    ],

                "median_nearest_distance_km":
                    metrics[
                        "median_nearest_distance_km"
                    ],

                "maximum_nearest_distance_km":
                    metrics[
                        "maximum_nearest_distance_km"
                    ],

                "within_1km_percent":
                    metrics[
                        "within_1km_percent"
                    ],

                "within_2km_percent":
                    metrics[
                        "within_2km_percent"
                    ],

                "within_5km_percent":
                    metrics[
                        "within_5km_percent"
                    ],
            }
        )


three_sensor_df = pd.DataFrame(
    three_sensor_results
)


# ------------------------------------------------------------
# THREE-SENSOR SUMMARY
# ------------------------------------------------------------

network_summary = []


for sensor_number in range(
    1,
    4
):

    subset = three_sensor_df[
        three_sensor_df[
            "perturbed_sensor_number"
        ]
        == sensor_number
    ]


    if subset.empty:
        continue


    best_index = (
        subset[
            "mean_nearest_distance_km"
        ]
        .idxmin()
    )


    worst_index = (
        subset[
            "mean_nearest_distance_km"
        ]
        .idxmax()
    )


    best_row = subset.loc[
        best_index
    ]

    worst_row = subset.loc[
        worst_index
    ]


    network_summary.append(
        {

            "perturbed_sensor_number":
                sensor_number,

            "valid_local_alternatives":
                len(subset),

            "mean_distance_min_km":
                subset[
                    "mean_nearest_distance_km"
                ].min(),

            "mean_distance_median_km":
                subset[
                    "mean_nearest_distance_km"
                ].median(),

            "mean_distance_max_km":
                subset[
                    "mean_nearest_distance_km"
                ].max(),

            "best_local_latitude":
                best_row[
                    "candidate_latitude"
                ],

            "best_local_longitude":
                best_row[
                    "candidate_longitude"
                ],

            "best_local_offset_km":
                best_row[
                    "distance_from_original_km"
                ],

            "worst_local_latitude":
                worst_row[
                    "candidate_latitude"
                ],

            "worst_local_longitude":
                worst_row[
                    "candidate_longitude"
                ],

            "worst_local_offset_km":
                worst_row[
                    "distance_from_original_km"
                ],
        }
    )


network_summary_df = pd.DataFrame(
    network_summary
)


# ------------------------------------------------------------
# PRINT RESULTS
# ------------------------------------------------------------

print()
print("--- Selected candidate locations ---")


for (
    sensor_number,
    latitude,
    longitude
) in selected_candidates:

    print(
        f"Sensor #{sensor_number}: "
        f"{latitude:.6f}, "
        f"{longitude:.6f}"
    )


print()
print("--- Local robustness summaries ---")


for _, row in local_summary_df.iterrows():

    print()

    print(
        f"Sensor #{int(row['sensor_number'])}"
    )

    print(
        f"  Alternatives within "
        f"{ROBUSTNESS_RADIUS_KM:.1f} km: "
        f"{int(row['local_alternative_count'])}"
    )

    print(
        f"  Mean-distance range: "
        f"{row['local_mean_nearest_distance_min_km']:.6f} "
        f"to "
        f"{row['local_mean_nearest_distance_max_km']:.6f} km"
    )

    print(
        f"  Median local mean distance: "
        f"{row['local_mean_nearest_distance_median_km']:.6f} km"
    )

    print(
        f"  Best nearby location: "
        f"{row['best_local_latitude']:.6f}, "
        f"{row['best_local_longitude']:.6f}"
    )

    print(
        f"  Best nearby offset: "
        f"{row['best_local_distance_from_original_km']:.6f} km"
    )

    print(
        f"  Worst nearby location: "
        f"{row['worst_local_latitude']:.6f}, "
        f"{row['worst_local_longitude']:.6f}"
    )

    print(
        f"  Worst nearby offset: "
        f"{row['worst_local_distance_from_original_km']:.6f} km"
    )


print()
print("--- Three-sensor network robustness ---")


for _, row in network_summary_df.iterrows():

    print()

    print(
        f"When Sensor #{int(row['perturbed_sensor_number'])} "
        f"is moved locally:"
    )

    print(
        f"  Valid alternatives: "
        f"{int(row['valid_local_alternatives'])}"
    )

    print(
        f"  Mean-distance range: "
        f"{row['mean_distance_min_km']:.6f}"
        f" to "
        f"{row['mean_distance_max_km']:.6f} km"
    )

    print(
        f"  Best alternative: "
        f"{row['best_local_latitude']:.6f}, "
        f"{row['best_local_longitude']:.6f}"
    )

    print(
        f"  Worst alternative: "
        f"{row['worst_local_latitude']:.6f}, "
        f"{row['worst_local_longitude']:.6f}"
    )


# ------------------------------------------------------------
# SAVE OUTPUTS
# ------------------------------------------------------------

LOCAL_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-F_Local_Candidate_Robustness.csv"
)

LOCAL_SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-F_Local_Robustness_Summary.csv"
)

NETWORK_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-F_Three_Sensor_Robustness.csv"
)

NETWORK_SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-F_Three_Sensor_Robustness_Summary.csv"
)


local_results_df.to_csv(
    LOCAL_OUTPUT,
    index=False
)


local_summary_df.to_csv(
    LOCAL_SUMMARY_OUTPUT,
    index=False
)


three_sensor_df.to_csv(
    NETWORK_OUTPUT,
    index=False
)


network_summary_df.to_csv(
    NETWORK_SUMMARY_OUTPUT,
    index=False
)


# ------------------------------------------------------------
# COMPLETE
# ------------------------------------------------------------

print()
print("=" * 75)
print("OUTPUT FILES")
print("=" * 75)

print()
print(LOCAL_OUTPUT)

print(
    LOCAL_SUMMARY_OUTPUT
)

print(
    NETWORK_OUTPUT
)

print(
    NETWORK_SUMMARY_OUTPUT
)


print()
print("=" * 75)
print("EXP-02D-F COMPLETE")
print("=" * 75)
print()