from pathlib import Path
import pandas as pd


# ============================================================
# EXP-02C-TZ-2
# Timestamp Convention Resolution
#
# Tests two hypotheses for timezone naive CPCB timestamps:
#
# H1: Naive timestamps represent UTC
# H2: Naive timestamps represent Asia/Kolkata (IST)
# ============================================================


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
    "alandi": DATA_DIR / "alandi.csv",
    "bhosari": DATA_DIR / "bhosari.csv",
    "bhukum_nagar": DATA_DIR / "bhukum_nagar.csv",
    "dhankawadi": DATA_DIR / "dhankawadi.csv",
    "hadapsar": DATA_DIR / "hadapsar.csv",
    "karve_road": DATA_DIR / "karve_road.csv",
    "katraj_dairy": DATA_DIR / "katraj_dairy.csv",
    "mhada_colony": DATA_DIR / "mhada_colony.csv",
    "panchwati_pashan": DATA_DIR / "panchwati_pashan.csv",
    "revenue_colony_shivajinagar":
        DATA_DIR / "revenue_colony_shivajinagar.csv",
    "sppu": DATA_DIR / "sppu.csv",
    "transport_nagar_ngidi":
        DATA_DIR / "transport_nagar_ngidi.csv",
}


# ------------------------------------------------------------
# PM2.5 column detection
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
# Load and normalize timestamps
# ------------------------------------------------------------

print()
print("=" * 75)
print("EXP-002C-TZ-2 — TIMESTAMP CONVENTION RESOLUTION")
print("=" * 75)


station_data = {}


for station, path in station_files.items():

    print()
    print(f"Loading: {station}")

    df = pd.read_csv(
        path,
        low_memory=False
    )

    timestamp_column = find_timestamp_column(df)

    if timestamp_column is None:
        raise ValueError(
            f"No timestamp column found in {path}"
        )

    pm25_column = find_pm25_column(df)

    if pm25_column is None:
        raise ValueError(
            f"No PM2.5 column found in {path}"
        )


    raw = df[timestamp_column].astype(str)

    # --------------------------------------------------------
    # Dhankawadi:
    # Explicit +0000 parse as UTC.
    # --------------------------------------------------------

    if station == "dhankawadi":

        timestamps = pd.to_datetime(
            raw,
            errors="coerce",
            format="mixed",
            utc=True
        )

        timestamps = timestamps.dt.tz_convert(
            "Asia/Kolkata"
        )

        timestamp_mode = (
            "explicit UTC → converted to Asia/Kolkata"
        )

    else:

        timestamps = pd.to_datetime(
            raw,
            errors="coerce",
            format="mixed"
        )

        timestamp_mode = (
            "timezone-naive source timestamp"
        )


    pm25 = pd.to_numeric(
        df[pm25_column],
        errors="coerce"
    )


    valid = (
        timestamps.notna()
        & pm25.notna()
    )

    station_data[station] = {
        "timestamps": timestamps[valid],
        "pm25": pm25[valid],
        "mode": timestamp_mode,
    }


    print(
        f"  valid PM2.5 rows: "
        f"{valid.sum():,}"
    )

    print(
        f"  timestamp mode: "
        f"{timestamp_mode}"
    )


# ------------------------------------------------------------
# Reference station
# ------------------------------------------------------------

reference_station = "dhankawadi"

reference = station_data[
    reference_station
]

reference_timestamps_ist = (
    reference["timestamps"]
)


# ------------------------------------------------------------
# Test the two hypotheses
# ------------------------------------------------------------

hypotheses = {

    "H1_naive_equals_UTC":
        "Interpret naive timestamps as UTC",

    "H2_naive_equals_IST":
        "Interpret naive timestamps as Asia/Kolkata",
}


results = []


for hypothesis_name, description in hypotheses.items():

    print()
    print("=" * 75)
    print(hypothesis_name)
    print(description)
    print("=" * 75)


    # Dhankawadi is already normalized to IST.
    ref_set = set(
        reference_timestamps_ist
    )


    for station, data in station_data.items():

        if station == reference_station:
            continue


        naive_timestamps = (
            data["timestamps"]
        )


        # ----------------------------------------------------
        # H1:
        # Naive timestamp represents UTC.
        # Convert UTC to IST.
        # ----------------------------------------------------

        if hypothesis_name == "H1_naive_equals_UTC":

            normalized = (
                naive_timestamps
                .dt
                .tz_localize("UTC")
                .dt
                .tz_convert("Asia/Kolkata")
            )


        # ----------------------------------------------------
        # H2:
        # Naive timestamp represents IST.
        # ----------------------------------------------------

        else:

            normalized = (
                naive_timestamps
                .dt
                .tz_localize("Asia/Kolkata")
            )


        normalized_set = set(
            normalized
        )


        intersection = (
            ref_set
            & normalized_set
        )


        count = len(intersection)


        equivalent_days = (
            count / 96
        )


        results.append(
            {
                "hypothesis":
                    hypothesis_name,

                "station":
                    station,

                "simultaneous_valid_pm25_timestamps":
                    count,

                "equivalent_15min_days":
                    equivalent_days,
            }
        )


        print(
            f"{station:<38} "
            f"{count:>7,} simultaneous timestamps "
            f"({equivalent_days:>8.2f} equivalent days)"
        )


# ------------------------------------------------------------
# Compare hypotheses
# ------------------------------------------------------------

results_df = pd.DataFrame(results)


print()
print("=" * 75)
print("HYPOTHESIS COMPARISON")
print("=" * 75)


summary = (
    results_df
    .groupby("hypothesis")
    .agg(
        total_simultaneous_timestamps=(
            "simultaneous_valid_pm25_timestamps",
            "sum"
        ),
        mean_simultaneous_timestamps=(
            "simultaneous_valid_pm25_timestamps",
            "mean"
        ),
        station_pairs_with_overlap=(
            "simultaneous_valid_pm25_timestamps",
            lambda x: (x > 0).sum()
        ),
    )
    .reset_index()
)


print(
    summary.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# Imp:
# This experiment does NOT automatically choose a winner.
# ------------------------------------------------------------

print()
print("=" * 75)
print("SCIENTIFIC INTERPRETATION")
print("=" * 75)

print()
print(
    "This experiment compares temporal overlap under two "
    "possible interpretations of the timezone naive files."
)

print()
print(
    "A larger overlap under one hypothesis is evidence about "
    "timestamp alignment, but is NOT by itself proof that the "
    "hypothesis represents the source's intended timezone."
)

print()
print(
    "Final timezone convention must be supported by source "
    "documentation or corroborating evidence."
)


# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

detailed_output = (
    OUTPUT_DIR
    / "EXP-02C-TZ-2_Hypothesis_Comparison.csv"
)

summary_output = (
    OUTPUT_DIR
    / "EXP-02C-TZ-2_Hypothesis_Summary.csv"
)


results_df.to_csv(
    detailed_output,
    index=False
)

summary.to_csv(
    summary_output,
    index=False
)


print()
print("=" * 75)
print("OUTPUT FILES")
print("=" * 75)

print(detailed_output)
print(summary_output)

print()
print("EXP-02C-TZ-2 COMPLETE.")
print()