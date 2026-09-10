from pathlib import Path
import math
import pandas as pd


# ============================================================
# EXP-02D-D
# TEMPORAL + SPATIAL COVERAGE ANALYSIS
#
# Combines:
#   EXP-02C corrected temporal coverage
#   EXP-02D-C study-area spatial coverage
#
# Naming convention:
#   EXP-02...
#
# This script intentionally uses the exact filenames currently
# produced by the project.
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

TEMPORAL_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "temporal_coverage"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "temporal_spatial_coverage"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# EXACT INPUT FILES
# ------------------------------------------------------------

TEMPORAL_FILE = (
    TEMPORAL_DIR
    / "EXP-02C_Corrected_Station_Temporal_Summary.csv"
)

SPATIAL_FILE = (
    SPATIAL_DIR
    / "EXP-02D-C_Study_Area_Grid.csv"
)


# ------------------------------------------------------------
# ANALYSIS THRESHOLDS
# ------------------------------------------------------------

# A grid point is spatially underserved when the nearest
# existing monitoring station is more than 5 km away.

SPATIAL_THRESHOLD_KM = 5.0


# A grid point is considered temporally underserved when the
# best-completeness station within 5 km has less than 75%
# timestamp completeness.

TEMPORAL_THRESHOLD_PERCENT = 75.0


# Radius used when searching for nearby stations.

NEARBY_RADIUS_KM = 5.0


# Extended radius reported as an additional network metric.

EXTENDED_RADIUS_KM = 10.0


# ------------------------------------------------------------
# STATION COORDINATES
#
# Latitude, longitude
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
# HAVERSINE DISTANCE
# ------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate great-circle distance between two
    latitude/longitude coordinates.
    """

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * EARTH_RADIUS_KM
        * math.asin(math.sqrt(a))
    )


# ------------------------------------------------------------
# START
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-02D-D — TEMPORAL + SPATIAL COVERAGE ANALYSIS")
print("=" * 75)


# ------------------------------------------------------------
# CHECK INPUT FILES
# ------------------------------------------------------------

print()
print("--- Checking input files ---")

print()
print("Temporal input:")
print(TEMPORAL_FILE)

if not TEMPORAL_FILE.exists():

    print()
    print("ERROR: Temporal input file does not exist.")

    print()
    print("Files currently present in temporal_coverage:")

    if TEMPORAL_DIR.exists():

        for file in sorted(
            TEMPORAL_DIR.glob("*.csv")
        ):
            print(
                f"  {file.name}"
            )

    raise FileNotFoundError(
        f"\nRequired file not found:\n{TEMPORAL_FILE}"
    )


print()
print("Spatial input:")
print(SPATIAL_FILE)

if not SPATIAL_FILE.exists():

    print()
    print("ERROR: Spatial input file does not exist.")

    print()
    print("Files currently present in spatial_coverage:")

    if SPATIAL_DIR.exists():

        for file in sorted(
            SPATIAL_DIR.glob("*.csv")
        ):
            print(
                f"  {file.name}"
            )

    raise FileNotFoundError(
        f"\nRequired file not found:\n{SPATIAL_FILE}"
    )


print()
print("Both required input files found.")


# ------------------------------------------------------------
# LOAD TEMPORAL SUMMARY
# ------------------------------------------------------------

print()
print("=" * 75)
print("LOADING EXP-02C TEMPORAL SUMMARY")
print("=" * 75)


temporal_df = pd.read_csv(
    TEMPORAL_FILE
)


required_temporal_columns = {
    "station",
    "timestamp_completeness_percent",
    "valid_pm25_observations",
}


missing_temporal_columns = (
    required_temporal_columns
    - set(temporal_df.columns)
)


if missing_temporal_columns:

    raise ValueError(
        "EXP-02C temporal summary is missing columns:\n"
        + "\n".join(
            sorted(missing_temporal_columns)
        )
    )


temporal_completeness = {}
valid_observations = {}


for _, row in temporal_df.iterrows():

    station = str(
        row["station"]
    )

    temporal_completeness[station] = float(
        row[
            "timestamp_completeness_percent"
        ]
    )

    valid_observations[station] = int(
        row[
            "valid_pm25_observations"
        ]
    )


# Verify station coverage.

missing_temporal_stations = [
    station
    for station in STATIONS
    if station not in temporal_completeness
]


if missing_temporal_stations:

    raise ValueError(
        "The following stations are missing from "
        "the EXP-02C temporal summary:\n"
        + "\n".join(
            missing_temporal_stations
        )
    )


print()
print(
    f"Temporal stations loaded: "
    f"{len(temporal_completeness)}"
)


# ------------------------------------------------------------
# PRINT TEMPORAL COMPLETENESS
# ------------------------------------------------------------

print()
print("--- Station temporal completeness ---")

for station in STATIONS:

    print(
        f"{station}: "
        f"{temporal_completeness[station]:.4f}%"
    )


# ------------------------------------------------------------
# LOAD EXP-02D-C GRID
# ------------------------------------------------------------

print()
print("=" * 75)
print("LOADING EXP-02D-C STUDY-AREA GRID")
print("=" * 75)


grid_df = pd.read_csv(
    SPATIAL_FILE
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
        "EXP-02D-C grid is missing columns:\n"
        + "\n".join(
            sorted(missing_grid_columns)
        )
    )


print()
print(
    f"Grid points loaded: "
    f"{len(grid_df):,}"
)


# ------------------------------------------------------------
# ANALYZE GRID
# ------------------------------------------------------------

print()
print("=" * 75)
print("CALCULATING TEMPORAL + SPATIAL COVERAGE")
print("=" * 75)


results = []


for _, grid_point in grid_df.iterrows():

    latitude = float(
        grid_point["latitude"]
    )

    longitude = float(
        grid_point["longitude"]
    )


    # --------------------------------------------------------
    # Calculate distance from this grid point to every station
    # --------------------------------------------------------

    station_information = []


    for station, (
        station_lat,
        station_lon
    ) in STATIONS.items():

        distance = haversine_km(
            latitude,
            longitude,
            station_lat,
            station_lon
        )


        station_information.append(
            {
                "station": station,
                "distance_km": distance,
                "temporal_completeness_percent":
                    temporal_completeness[
                        station
                    ],
                "valid_pm25_observations":
                    valid_observations[
                        station
                    ],
            }
        )


    # --------------------------------------------------------
    # Sort by distance
    # --------------------------------------------------------

    station_information.sort(
        key=lambda x:
            x["distance_km"]
    )


    nearest = station_information[0]


    nearest_station = nearest[
        "station"
    ]

    nearest_distance = nearest[
        "distance_km"
    ]

    nearest_temporal_completeness = nearest[
        "temporal_completeness_percent"
    ]


    # --------------------------------------------------------
    # Stations within 5 km
    # --------------------------------------------------------

    stations_within_5km = [

        item

        for item in station_information

        if item["distance_km"]
        <= NEARBY_RADIUS_KM
    ]


    # --------------------------------------------------------
    # Stations within 10 km
    # --------------------------------------------------------

    stations_within_10km = [

        item

        for item in station_information

        if item["distance_km"]
        <= EXTENDED_RADIUS_KM
    ]


    # --------------------------------------------------------
    # Best temporally available station within 5 km
    # --------------------------------------------------------

    if stations_within_5km:

        best_nearby = max(
            stations_within_5km,
            key=lambda x:
                x[
                    "temporal_completeness_percent"
                ]
        )


        best_5km_station = best_nearby[
            "station"
        ]

        best_5km_completeness = best_nearby[
            "temporal_completeness_percent"
        ]

    else:

        best_5km_station = None

        best_5km_completeness = 0.0


    # --------------------------------------------------------
    # Spatial underserved classification
    # --------------------------------------------------------

    spatially_underserved = (
        nearest_distance
        > SPATIAL_THRESHOLD_KM
    )


    # --------------------------------------------------------
    # Temporal underserved classification
    # --------------------------------------------------------

    temporally_underserved = (
        best_5km_completeness
        < TEMPORAL_THRESHOLD_PERCENT
    )


    # --------------------------------------------------------
    # Combined underserved classification
    # --------------------------------------------------------

    combined_underserved = (
        spatially_underserved
        and temporally_underserved
    )


    # --------------------------------------------------------
    # Save grid-point result
    # --------------------------------------------------------

    results.append(
        {

            "latitude":
                latitude,

            "longitude":
                longitude,

            "nearest_station":
                nearest_station,

            "nearest_station_distance_km":
                nearest_distance,

            "nearest_station_temporal_completeness_percent":
                nearest_temporal_completeness,

            "stations_within_5km":
                len(stations_within_5km),

            "stations_within_10km":
                len(stations_within_10km),

            "best_5km_station":
                best_5km_station,

            "best_5km_temporal_completeness_percent":
                best_5km_completeness,

            "spatially_underserved":
                spatially_underserved,

            "temporally_underserved":
                temporally_underserved,

            "combined_underserved":
                combined_underserved,
        }
    )


coverage_df = pd.DataFrame(
    results
)


# ------------------------------------------------------------
# SUMMARY STATISTICS
# ------------------------------------------------------------

nearest_distance_series = (
    coverage_df[
        "nearest_station_distance_km"
    ]
)


nearest_completeness_series = (
    coverage_df[
        "nearest_station_temporal_completeness_percent"
    ]
)


best_5km_completeness_series = (
    coverage_df[
        "best_5km_temporal_completeness_percent"
    ]
)


spatially_underserved_count = int(
    coverage_df[
        "spatially_underserved"
    ].sum()
)


temporally_underserved_count = int(
    coverage_df[
        "temporally_underserved"
    ].sum()
)


combined_underserved_count = int(
    coverage_df[
        "combined_underserved"
    ].sum()
)


summary = {

    "study_area_grid_points":
        len(coverage_df),

    "spatial_threshold_km":
        SPATIAL_THRESHOLD_KM,

    "temporal_threshold_percent":
        TEMPORAL_THRESHOLD_PERCENT,

    "nearby_station_radius_km":
        NEARBY_RADIUS_KM,

    "extended_station_radius_km":
        EXTENDED_RADIUS_KM,

    "mean_nearest_station_distance_km":
        nearest_distance_series.mean(),

    "median_nearest_station_distance_km":
        nearest_distance_series.median(),

    "minimum_nearest_station_distance_km":
        nearest_distance_series.min(),

    "maximum_nearest_station_distance_km":
        nearest_distance_series.max(),

    "q25_nearest_station_distance_km":
        nearest_distance_series.quantile(0.25),

    "q75_nearest_station_distance_km":
        nearest_distance_series.quantile(0.75),

    "q90_nearest_station_distance_km":
        nearest_distance_series.quantile(0.90),

    "q95_nearest_station_distance_km":
        nearest_distance_series.quantile(0.95),

    "mean_nearest_station_temporal_completeness_percent":
        nearest_completeness_series.mean(),

    "median_nearest_station_temporal_completeness_percent":
        nearest_completeness_series.median(),

    "mean_best_5km_temporal_completeness_percent":
        best_5km_completeness_series.mean(),

    "median_best_5km_temporal_completeness_percent":
        best_5km_completeness_series.median(),

    "spatially_underserved_grid_points":
        spatially_underserved_count,

    "spatially_underserved_percent":
        (
            spatially_underserved_count
            / len(coverage_df)
            * 100
        ),

    "temporally_underserved_grid_points":
        temporally_underserved_count,

    "temporally_underserved_percent":
        (
            temporally_underserved_count
            / len(coverage_df)
            * 100
        ),

    "combined_underserved_grid_points":
        combined_underserved_count,

    "combined_underserved_percent":
        (
            combined_underserved_count
            / len(coverage_df)
            * 100
        ),
}


# ------------------------------------------------------------
# NEAREST-STATION ASSIGNMENT
# ------------------------------------------------------------

station_assignment = (
    coverage_df[
        "nearest_station"
    ]
    .value_counts()
    .rename_axis(
        "station"
    )
    .reset_index(
        name="grid_points"
    )
)


station_assignment[
    "percent_of_study_area"
] = (
    station_assignment[
        "grid_points"
    ]
    / len(coverage_df)
    * 100
)


# ------------------------------------------------------------
# UNDERSERVED GRID POINTS
# ------------------------------------------------------------

underserved_df = coverage_df[
    coverage_df[
        "combined_underserved"
    ]
].copy()


underserved_df = (
    underserved_df
    .sort_values(
        [
            "nearest_station_distance_km",
            "best_5km_temporal_completeness_percent",
        ],
        ascending=[
            False,
            True,
        ]
    )
)


# ------------------------------------------------------------
# PRINT FINAL RESULTS
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-02D-D RESULTS")
print("=" * 75)


print()
print("Study area:")
print(
    "Convex hull of the 12 candidate monitoring stations"
)


print()
print(
    f"Grid points analyzed: "
    f"{len(coverage_df):,}"
)


print()
print("--- Analysis thresholds ---")

print(
    f"Spatially underserved: nearest station > "
    f"{SPATIAL_THRESHOLD_KM:.1f} km"
)

print(
    f"Temporally underserved: best station within "
    f"{NEARBY_RADIUS_KM:.1f} km has < "
    f"{TEMPORAL_THRESHOLD_PERCENT:.1f}% completeness"
)


print()
print("--- Spatial coverage ---")

print(
    f"Mean nearest-station distance: "
    f"{nearest_distance_series.mean():.6f} km"
)

print(
    f"Median nearest-station distance: "
    f"{nearest_distance_series.median():.6f} km"
)

print(
    f"Minimum nearest-station distance: "
    f"{nearest_distance_series.min():.6f} km"
)

print(
    f"Maximum nearest-station distance: "
    f"{nearest_distance_series.max():.6f} km"
)

print(
    f"Q25: "
    f"{nearest_distance_series.quantile(0.25):.6f} km"
)

print(
    f"Q75: "
    f"{nearest_distance_series.quantile(0.75):.6f} km"
)

print(
    f"Q90: "
    f"{nearest_distance_series.quantile(0.90):.6f} km"
)

print(
    f"Q95: "
    f"{nearest_distance_series.quantile(0.95):.6f} km"
)


print()
print("--- Temporal coverage ---")

print(
    f"Mean completeness of nearest station: "
    f"{nearest_completeness_series.mean():.6f}%"
)

print(
    f"Median completeness of nearest station: "
    f"{nearest_completeness_series.median():.6f}%"
)

print(
    f"Mean best completeness within 5 km: "
    f"{best_5km_completeness_series.mean():.6f}%"
)

print(
    f"Median best completeness within 5 km: "
    f"{best_5km_completeness_series.median():.6f}%"
)


print()
print("--- Underserved area ---")

print(
    f"Spatially underserved: "
    f"{spatially_underserved_count:,} grid points "
    f"("
    f"{spatially_underserved_count / len(coverage_df) * 100:.6f}"
    f"%)"
)

print(
    f"Temporally underserved: "
    f"{temporally_underserved_count:,} grid points "
    f"("
    f"{temporally_underserved_count / len(coverage_df) * 100:.6f}"
    f"%)"
)

print(
    f"Combined spatial + temporal underserved: "
    f"{combined_underserved_count:,} grid points "
    f"("
    f"{combined_underserved_count / len(coverage_df) * 100:.6f}"
    f"%)"
)


print()
print("--- Nearest-station assignments ---")

for _, row in station_assignment.iterrows():

    print(
        f"{row['station']}: "
        f"{int(row['grid_points']):,} grid points "
        f"("
        f"{row['percent_of_study_area']:.4f}"
        f"%)"
    )


# ------------------------------------------------------------
# MOST UNDERSERVED LOCATIONS
# ------------------------------------------------------------

print()
print("=" * 75)
print("MOST UNDERSERVED GRID POINTS")
print("=" * 75)


if underserved_df.empty:

    print()
    print(
        "No grid points satisfy both underserved criteria."
    )

else:

    for _, row in underserved_df.head(20).iterrows():

        print(
            f"Lat {row['latitude']:.6f}, "
            f"Lon {row['longitude']:.6f} | "
            f"Nearest: "
            f"{row['nearest_station']} "
            f"("
            f"{row['nearest_station_distance_km']:.3f}"
            f" km) | "
            f"Best 5-km completeness: "
            f"{row['best_5km_temporal_completeness_percent']:.2f}%"
        )


# ------------------------------------------------------------
# SAVE OUTPUTS
# ------------------------------------------------------------

GRID_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-D_Temporal_Spatial_Grid.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-D_Summary.csv"
)

ASSIGNMENT_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-D_Station_Assignment.csv"
)

UNDERSERVED_OUTPUT = (
    OUTPUT_DIR
    / "EXP-02D-D_Underserved_Grid_Points.csv"
)


coverage_df.to_csv(
    GRID_OUTPUT,
    index=False
)


pd.DataFrame(
    [summary]
).to_csv(
    SUMMARY_OUTPUT,
    index=False
)


station_assignment.to_csv(
    ASSIGNMENT_OUTPUT,
    index=False
)


underserved_df.to_csv(
    UNDERSERVED_OUTPUT,
    index=False
)


# ------------------------------------------------------------
# FINAL OUTPUT
# ------------------------------------------------------------

print()
print("=" * 75)
print("OUTPUT FILES")
print("=" * 75)

print()
print(GRID_OUTPUT)

print(
    SUMMARY_OUTPUT
)

print(
    ASSIGNMENT_OUTPUT
)

print(
    UNDERSERVED_OUTPUT
)


print()
print("=" * 75)
print("EXP-02D-D COMPLETE")
print("=" * 75)
print()