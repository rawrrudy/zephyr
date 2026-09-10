from pathlib import Path
import pandas as pd


# ============================================================
# EXP-02C-TZ
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "ground_stations" / "raw"


# ------------------------------------------------------------
# Station files
# ------------------------------------------------------------

station_files = sorted(DATA_DIR.glob("*.csv"))

if not station_files:
    raise FileNotFoundError(
        f"No CSV files found in:\n{DATA_DIR}"
    )


print()
print("=" * 75)
print("EXP-002C-TZ — TIMESTAMP CONVENTION VALIDATION")
print("=" * 75)

print()
print(f"Data directory: {DATA_DIR}")
print(f"CSV files found: {len(station_files)}")


# ------------------------------------------------------------
# identify timestamp column
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

    # Fallback: search column names
    for column in df.columns:
        name = str(column).lower()

        if (
            "timestamp" in name
            or "datetime" in name
            or name == "date"
        ):
            return column

    return None


# ------------------------------------------------------------
# Analyze every station
# ------------------------------------------------------------

results = []

for file_path in station_files:

    print()
    print("-" * 75)
    print(f"FILE: {file_path.name}")
    print("-" * 75)

    df = pd.read_csv(
        file_path,
        low_memory=False
    )

    timestamp_column = find_timestamp_column(df)

    if timestamp_column is None:

        print("ERROR: No timestamp column found.")

        results.append(
            {
                "file": file_path.name,
                "timestamp_column": None,
                "rows": len(df),
                "parseable": 0,
                "unparseable": len(df),
                "timezone_aware": None,
                "timezone_values": None,
                "first_raw_timestamp": None,
                "last_raw_timestamp": None,
            }
        )

        continue


    raw_timestamp = df[timestamp_column].astype(str)

    # Parse WITHOUT forcing UTC.
    parsed = pd.to_datetime(
        raw_timestamp,
        errors="coerce",
        format="mixed"
    )

    valid = parsed.dropna()

    parseable_count = len(valid)
    unparseable_count = len(parsed) - parseable_count

    # --------------------------------------------------------
    # Determine timezone awareness
    # --------------------------------------------------------

    timezone_aware = False
    timezone_values = set()

    if len(valid) > 0:

        # DatetimeIndex/Series timezone information
        try:
            timezone = valid.dt.tz

            if timezone is not None:
                timezone_aware = True
                timezone_values.add(str(timezone))

        except Exception:
            pass

    # --------------------------------------------------------
    # Raw timestamp characteristics
    # --------------------------------------------------------

    first_raw = (
        raw_timestamp.iloc[0]
        if len(raw_timestamp) > 0
        else None
    )

    last_raw = (
        raw_timestamp.iloc[-1]
        if len(raw_timestamp) > 0
        else None
    )

    first_parsed = (
        valid.iloc[0]
        if len(valid) > 0
        else None
    )

    last_parsed = (
        valid.iloc[-1]
        if len(valid) > 0
        else None
    )


    print(f"Timestamp column: {timestamp_column}")
    print(f"Rows: {len(df):,}")
    print(f"Parseable timestamps: {parseable_count:,}")
    print(f"Unparseable timestamps: {unparseable_count:,}")

    print()
    print(f"First RAW timestamp: {first_raw}")
    print(f"Last RAW timestamp:  {last_raw}")

    print()
    print(f"First PARSED timestamp: {first_parsed}")
    print(f"Last PARSED timestamp:  {last_parsed}")

    print()
    print(f"Timezone-aware: {timezone_aware}")

    if timezone_values:
        print(
            "Detected timezone information: "
            + ", ".join(sorted(timezone_values))
        )
    else:
        print(
            "Detected timezone information: NONE "
            "(timestamps appear timezone-naive)"
        )


    # --------------------------------------------------------
    # Examine timestamp formatting
    # --------------------------------------------------------

    print()
    print("Sample raw timestamps:")

    sample_count = min(10, len(raw_timestamp))

    for value in raw_timestamp.head(sample_count):
        print(f"  {value}")


    # --------------------------------------------------------
    # Check interval regularity
    # --------------------------------------------------------

    interval_minutes = None
    interval_counts = {}

    if len(valid) >= 2:

        # If timezone aware, this still works correctly.
        sorted_valid = valid.sort_values()

        differences = (
            sorted_valid
            .diff()
            .dropna()
            .dt.total_seconds()
            / 60
        )

        interval_counts = (
            differences
            .round(6)
            .value_counts()
            .head(10)
            .to_dict()
        )

        if len(interval_counts) > 0:
            interval_minutes = next(
                iter(interval_counts.keys())
            )

    print()
    print("Most common timestamp intervals (minutes):")

    if interval_counts:

        for interval, count in interval_counts.items():
            print(
                f"  {interval:g} min : "
                f"{int(count):,} occurrences"
            )

    else:
        print("  Unable to calculate.")


    # --------------------------------------------------------
    # Check for explicit timezone markers in raw strings
    # --------------------------------------------------------

    explicit_timezone_markers = 0

    for value in raw_timestamp:

        value = str(value).strip()

        # ISO style Z suffix
        if value.endswith("Z"):
            explicit_timezone_markers += 1
            continue

        # Look for +HH:MM or -HH:MM at end
        if len(value) >= 6:

            ending = value[-6:]

            if (
                (ending[0] in ["+", "-"])
                and ending[3] == ":"
                and ending[1:3].isdigit()
                and ending[4:6].isdigit()
            ):
                explicit_timezone_markers += 1

    print()
    print(
        "Rows with explicit timezone marker: "
        f"{explicit_timezone_markers:,}"
    )


    results.append(
        {
            "file": file_path.name,
            "timestamp_column": timestamp_column,
            "rows": len(df),
            "parseable": parseable_count,
            "unparseable": unparseable_count,
            "timezone_aware": timezone_aware,
            "timezone_values": (
                "; ".join(sorted(timezone_values))
                if timezone_values
                else ""
            ),
            "explicit_timezone_marker_rows":
                explicit_timezone_markers,
            "first_raw_timestamp": first_raw,
            "last_raw_timestamp": last_raw,
            "first_parsed_timestamp": first_parsed,
            "last_parsed_timestamp": last_parsed,
            "most_common_interval_minutes":
                interval_minutes,
        }
    )


# ------------------------------------------------------------
# Cross station comparison
# ------------------------------------------------------------

results_df = pd.DataFrame(results)


print()
print("=" * 75)
print("CROSS-STATION SUMMARY")
print("=" * 75)

print()

for _, row in results_df.iterrows():

    print(
        f"{row['file']:<38} "
        f"rows={int(row['rows']):>7,} | "
        f"aware={str(row['timezone_aware']):<5} | "
        f"interval={row['most_common_interval_minutes']}"
    )


# ------------------------------------------------------------
# Determine whether timestamp conventions are consistent
# ------------------------------------------------------------

timezone_states = (
    results_df["timezone_aware"]
    .dropna()
    .astype(str)
    .unique()
)

explicit_marker_counts = (
    results_df["explicit_timezone_marker_rows"]
    .fillna(0)
)


print()
print("=" * 75)
print("INTERPRETATION")
print("=" * 75)

if len(timezone_states) == 1:

    if timezone_states[0] == "False":

        print()
        print(
            "All successfully parsed station timestamps are "
            "timezone-naive."
        )

        print(
            "This means the source files do not explicitly "
            "encode a timezone."
        )

        print(
            "Do NOT yet assume that these timestamps are UTC."
        )

        print(
            "The next correction step should interpret the "
            "source timestamps according to the station/data "
            "provider's documented local-time convention."
        )

    else:

        print()
        print(
            "All successfully parsed station timestamps appear "
            "timezone-aware."
        )

else:

    print()
    print(
        "WARNING: Timestamp timezone awareness is inconsistent "
        "between files."
    )

    print(
        "Further normalization is required before calculating "
        "cross-station temporal overlap."
    )


# ------------------------------------------------------------
# Save summary
# ------------------------------------------------------------

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "temporal_coverage"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

output_file = (
    OUTPUT_DIR
    / "EXP-002C-TZ_Timestamp_Validation.csv"
)

results_df.to_csv(
    output_file,
    index=False
)


print()
print("=" * 75)
print("OUTPUT")
print("=" * 75)

print(output_file)

print()
print("EXP-02C-TZ COMPLETE.")
print()