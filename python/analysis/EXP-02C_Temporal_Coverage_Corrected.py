from pathlib import Path
from itertools import combinations
import pandas as pd
import numpy as np


# ============================================================
# EXP-02C — CORRECTED TEMPORAL COVERAGE ANALYSIS
# =============================================================


# ------------------------------------------------------------
# Project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "ground_stations"
    / "raw"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "temporal_coverage"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# Station files
# ------------------------------------------------------------

station_files = {
    "Alandi":
        DATA_DIR / "alandi.csv",

    "Bhosari":
        DATA_DIR / "bhosari.csv",

    "Bhukum Nagar":
        DATA_DIR / "bhukum_nagar.csv",

    "Dhankawadi":
        DATA_DIR / "dhankawadi.csv",

    "Hadapsar":
        DATA_DIR / "hadapsar.csv",

    "Karve Road":
        DATA_DIR / "karve_road.csv",

    "Katraj Dairy":
        DATA_DIR / "katraj_dairy.csv",

    "Mhada Colony":
        DATA_DIR / "mhada_colony.csv",

    "Panchawati/Pashan":
        DATA_DIR / "panchwati_pashan.csv",

    "Revenue Colony/Shivajinagar":
        DATA_DIR / "revenue_colony_shivajinagar.csv",

    "SPPU":
        DATA_DIR / "sppu.csv",

    "Transport Nagar/Nigdi":
        DATA_DIR / "transport_nagar_ngidi.csv",
}


# ------------------------------------------------------------
# Column detection
# ------------------------------------------------------------

def find_timestamp_column(df):

    candidates = [
        "Timestamp",
        "timestamp",
        "Date",
        "date",
        "Datetime",
        "datetime",
        "DateTime",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    for column in df.columns:

        name = str(column).lower()

        if (
            "timestamp" in name
            or "datetime" in name
            or name == "date"
        ):
            return column

    return None


def find_pm25_column(df):

    candidates = [
        "PM2.5 (ug/m3)",
        "PM2.5",
        "PM25",
        "pm2.5",
        "pm25",
    ]

    for column in candidates:

        if column in df.columns:
            return column

    for column in df.columns:

        name = str(column).lower()

        if (
            "pm2.5" in name
            or "pm25" in name
        ):
            return column

    return None


# ------------------------------------------------------------
# Load station data
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-02C — CORRECTED TEMPORAL COVERAGE ANALYSIS")
print("=" * 75)

print()
print("Timestamp normalization:")
print(
    "Naive source timestamps preserved as clock values; "
    "Dhankawadi UTC timestamps converted to IST clock values."
)

print()
print(f"Data directory: {DATA_DIR}")


station_data = {}


for station, file_path in station_files.items():

    print()
    print("-" * 75)
    print(f"Loading: {station}")
    print("-" * 75)

    df = pd.read_csv(
        file_path,
        low_memory=False
    )

    timestamp_column = find_timestamp_column(df)

    pm25_column = find_pm25_column(df)

    if timestamp_column is None:
        raise ValueError(
            f"No timestamp column found in {file_path}"
        )

    if pm25_column is None:
        raise ValueError(
            f"No PM2.5 column found in {file_path}"
        )


    raw_timestamps = (
        df[timestamp_column]
        .astype(str)
    )


    # --------------------------------------------------------
    # Dhankawadi:
    # explicit UTC to IST
    # --------------------------------------------------------

    if station == "Dhankawadi":

        timestamps = pd.to_datetime(
            raw_timestamps,
            errors="coerce",
            format="mixed",
            utc=True
        )

        timestamps = (
            timestamps
            .dt
            .tz_convert("Asia/Kolkata")
            .dt
            .tz_localize(None)
        )

        normalization_method = (
            "explicit UTC converted to IST clock time"
        )


    # --------------------------------------------------------
    # Other stations:
    # timezone naive clock values preserved
    # --------------------------------------------------------

    else:

        timestamps = pd.to_datetime(
            raw_timestamps,
            errors="coerce",
            format="mixed"
        )

        normalization_method = (
            "timezone-naive source clock preserved"
        )


    pm25 = pd.to_numeric(
        df[pm25_column],
        errors="coerce"
    )


    valid = (
        timestamps.notna()
        & pm25.notna()
    )


    normalized_timestamps = (
        timestamps[valid]
        .drop_duplicates()
        .sort_values()
    )


    station_data[station] = {
        "timestamps":
            normalized_timestamps,

        "pm25":
            pm25[valid],

        "valid_count":
            int(valid.sum()),

        "normalization":
            normalization_method,
    }


    print(
        f"Timestamp column: {timestamp_column}"
    )

    print(
        f"PM2.5 column: {pm25_column}"
    )

    print(
        f"Valid PM2.5 observations: "
        f"{valid.sum():,}"
    )

    print(
        f"Unique valid timestamps: "
        f"{len(normalized_timestamps):,}"
    )

    print(
        f"Normalization: "
        f"{normalization_method}"
    )

    if len(normalized_timestamps) > 0:

        print(
            f"First normalized timestamp: "
            f"{normalized_timestamps.iloc[0]}"
        )

        print(
            f"Last normalized timestamp:  "
            f"{normalized_timestamps.iloc[-1]}"
        )


# ------------------------------------------------------------
# Individual station temporal coverage
# ------------------------------------------------------------

station_summary = []


for station, data in station_data.items():

    timestamps = data["timestamps"]

    if len(timestamps) == 0:

        station_summary.append(
            {
                "station": station,
                "valid_pm25_observations": 0,
                "first_timestamp": None,
                "last_timestamp": None,
                "observed_span_days": None,
                "expected_15min_timestamps": None,
                "timestamp_completeness_percent": None,
            }
        )

        continue


    first_timestamp = timestamps.iloc[0]
    last_timestamp = timestamps.iloc[-1]


    observed_span_seconds = (
        last_timestamp - first_timestamp
    ).total_seconds()


    observed_span_days = (
        observed_span_seconds
        / 86400
    )


    expected_timestamps = (
        int(
            observed_span_seconds
            / (15 * 60)
        )
        + 1
    )


    completeness = (
        len(timestamps)
        / expected_timestamps
        * 100
    )


    station_summary.append(
        {
            "station": station,
            "valid_pm25_observations":
                len(timestamps),

            "first_timestamp":
                first_timestamp,

            "last_timestamp":
                last_timestamp,

            "observed_span_days":
                observed_span_days,

            "expected_15min_timestamps":
                expected_timestamps,

            "timestamp_completeness_percent":
                completeness,
        }
    )


station_summary_df = pd.DataFrame(
    station_summary
)


# ------------------------------------------------------------
# Pairwise simultaneous valid PM2.5 overlap
# ------------------------------------------------------------

pairwise_results = []


print()
print("=" * 75)
print("PAIRWISE SIMULTANEOUS VALID PM2.5 OVERLAP")
print("=" * 75)


for station_a, station_b in combinations(
    station_data.keys(),
    2
):

    timestamps_a = set(
        station_data[station_a]["timestamps"]
    )

    timestamps_b = set(
        station_data[station_b]["timestamps"]
    )


    intersection = (
        timestamps_a
        & timestamps_b
    )


    simultaneous_count = len(
        intersection
    )


    equivalent_days = (
        simultaneous_count / 96
    )


    pairwise_results.append(
        {
            "station_a": station_a,
            "station_b": station_b,
            "simultaneous_valid_timestamps":
                simultaneous_count,
            "equivalent_15min_observation_days":
                equivalent_days,
        }
    )


pairwise_df = pd.DataFrame(
    pairwise_results
)


pairwise_df = (
    pairwise_df
    .sort_values(
        "simultaneous_valid_timestamps",
        ascending=False
    )
    .reset_index(drop=True)
)


for _, row in pairwise_df.head(20).iterrows():

    print(
        f"{row['station_a']} + "
        f"{row['station_b']}: "
        f"{int(row['simultaneous_valid_timestamps']):,} "
        f"timestamps "
        f"({row['equivalent_15min_observation_days']:.2f} "
        f"equivalent days)"
    )


# ------------------------------------------------------------
# Group overlap analysis
# ------------------------------------------------------------

print()
print("=" * 75)
print("GROUP SIMULTANEOUS VALID PM2.5 OVERLAP")
print("=" * 75)


station_names = list(
    station_data.keys()
)


# For every timestamp, determine which stations have a valid PM2.5 measurement.

timestamp_to_stations = {}


for station, data in station_data.items():

    for timestamp in data["timestamps"]:

        timestamp_to_stations.setdefault(
            timestamp,
            set()
        ).add(station)


# Count observations by station group.

group_counts = {}


for timestamp, present_stations in (
    timestamp_to_stations.items()
):

    present_stations = frozenset(
        present_stations
    )

    # Count this timestamp for every subset size that is
    # actually represented at this timestamp.
    group_counts[present_stations] = (
        group_counts.get(
            present_stations,
            0
        )
        + 1
    )


# Instead of interpreting exact group composition as a
# fixed station group, calculate "at least N stations"
# simultaneous coverage.

group_size_counts = {}


for timestamp, present_stations in (
    timestamp_to_stations.items()
):

    group_size = len(
        present_stations
    )

    group_size_counts[group_size] = (
        group_size_counts.get(
            group_size,
            0
        )
        + 1
    )


print()
print("Simultaneous valid observations by number of stations:")

for group_size in sorted(
    group_size_counts.keys(),
    reverse=True
):

    count = group_size_counts[group_size]

    print(
        f"{group_size:2d} stations: "
        f"{count:,} timestamps "
        f"({count / 96:.2f} equivalent days)"
    )


# ------------------------------------------------------------
# Exact all station intersection
# ------------------------------------------------------------

all_station_timestamp_sets = [
    set(data["timestamps"])
    for data in station_data.values()
]


if all_station_timestamp_sets:

    all_common = set.intersection(
        *all_station_timestamp_sets
    )

else:

    all_common = set()


print()
print(
    f"All 12 stations simultaneous valid "
    f"timestamps: {len(all_common):,}"
)

print(
    f"All 12 stations equivalent observation days: "
    f"{len(all_common) / 96:.2f}"
)


# ------------------------------------------------------------
# Strongest station groups
# ------------------------------------------------------------

from itertools import combinations


best_group_results = []


for group_size in range(
    2,
    min(6, len(station_names)) + 1
):

    best_count = -1
    best_group = None


    for combination_group in combinations(
        station_names,
        group_size
    ):

        timestamp_sets = [
            set(
                station_data[station]["timestamps"]
            )
            for station in combination_group
        ]


        common = set.intersection(
            *timestamp_sets
        )


        count = len(common)


        if count > best_count:

            best_count = count
            best_group = combination_group


    best_group_results.append(
        {
            "group_size": group_size,
            "stations": " + ".join(best_group),
            "simultaneous_valid_timestamps":
                best_count,
            "equivalent_15min_observation_days":
                best_count / 96,
        }
    )


print()
print("=" * 75)
print("BEST OVERLAPPING STATION GROUPS")
print("=" * 75)


for result in best_group_results:

    print()
    print(
        f"{result['group_size']} stations:"
    )

    print(
        result["stations"]
    )

    print(
        f"Simultaneous timestamps: "
        f"{result['simultaneous_valid_timestamps']:,}"
    )

    print(
        f"Equivalent 15-min observation days: "
        f"{result['equivalent_15min_observation_days']:.2f}"
    )


best_group_df = pd.DataFrame(
    best_group_results
)


# ------------------------------------------------------------
# Save outputs
# ------------------------------------------------------------

station_summary_output = (
    OUTPUT_DIR
    / "EXP-02C_Corrected_Station_Temporal_Summary.csv"
)

pairwise_output = (
    OUTPUT_DIR
    / "EXP-02C_Corrected_Pairwise_Overlap.csv"
)

group_output = (
    OUTPUT_DIR
    / "EXP-02C_Corrected_Best_Group_Overlap.csv"
)


station_summary_df.to_csv(
    station_summary_output,
    index=False
)

pairwise_df.to_csv(
    pairwise_output,
    index=False
)

best_group_df.to_csv(
    group_output,
    index=False
)


# ------------------------------------------------------------
# Final interpretation
# ------------------------------------------------------------

print()
print("=" * 75)
print("METHODOLOGICAL NOTE")
print("=" * 75)

print()
print(
    "The public station files use inconsistent timezone "
    "encoding: most timestamps are timezone naive, while "
    "Dhankawadi contains explicit UTC timestamps."
)

print()
print(
    "For this corrected analysis, Dhankawadi timestamps "
    "were converted from UTC to IST clock time, while "
    "timezone naive timestamps were preserved as supplied."
)

print()
print(
    "Because the source documentation does not explicitly "
    "resolve the timezone convention of the naive exports, "
    "this remains a documented provenance limitation."
)

print()
print(
    "Equivalent observation days represent simultaneous "
    "valid 15 minute observations divided by 96. They do "
    "NOT necessarily represent uninterrupted calendar days."
)


print()
print("=" * 75)
print("OUTPUT FILES")
print("=" * 75)

print(station_summary_output)
print(pairwise_output)
print(group_output)

print()
print("EXP-02C CORRECTED COMPLETE.")
print()