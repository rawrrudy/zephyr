from pathlib import Path
from itertools import combinations
import pandas as pd
import re

PROJECT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT / "data" / "ground_stations" / "raw"
OUT_DIR = PROJECT / "data" / "ground_stations" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def norm(x):
    return re.sub(r"\s+", " ", str(x).strip()).lower()


def find_col(cols, target):
    t = norm(target)
    return next((c for c in cols if norm(c) == t), None)


def load_station(path):
    df = pd.read_csv(path, low_memory=False)

    timestamp_col = find_col(df.columns, "Timestamp")
    pm_col = find_col(df.columns, "PM2.5 (ug/m3)")

    if timestamp_col is None or pm_col is None:
        raise ValueError(
            f"{path.name}: missing Timestamp or PM2.5 column"
        )

    ts = pd.to_datetime(
        df[timestamp_col],
        errors="coerce",
        format="mixed",
        utc=True
    )

    pm = pd.to_numeric(df[pm_col], errors="coerce")

    valid_timestamp = ts.notna()
    ts = ts[valid_timestamp]
    pm = pm[valid_timestamp]

    # Every timestamp actually present in the file
    observed = set(ts.unique())

    # Timestamp has a usable PM2.5 value
    valid_pm25 = set(
        ts[pm.notna() & (pm >= 0)].unique()
    )

    return observed, valid_pm25


files = sorted(RAW_DIR.glob("*.csv"))

if len(files) < 2:
    raise FileNotFoundError(
        f"Need at least 2 CSV files in {RAW_DIR}"
    )


stations = {}

for file in files:
    stations[file.stem] = load_station(file)
    print(f"[OK] Loaded {file.name}")


names = sorted(stations)


# ============================================================
# 1. PAIRWISE OVERLAP
# ============================================================

pair_results = []

for station_a, station_b in combinations(names, 2):

    observed_a = stations[station_a][0]
    observed_b = stations[station_b][0]

    valid_a = stations[station_a][1]
    valid_b = stations[station_b][1]

    common_observed = observed_a & observed_b
    common_valid = valid_a & valid_b

    pair_results.append({
        "station_a": station_a,
        "station_b": station_b,

        "common_timestamps":
            len(common_observed),

        "equivalent_observation_days":
            len(common_observed) * 15 / 1440,

        "common_valid_pm25_timestamps":
            len(common_valid),

        "equivalent_valid_pm25_days":
            len(common_valid) * 15 / 1440
    })


pair_df = pd.DataFrame(pair_results)

pair_df = pair_df.sort_values(
    "common_valid_pm25_timestamps",
    ascending=False
)

pair_df.to_csv(
    OUT_DIR / "EXP-002C_pairwise_overlap.csv",
    index=False
)


# ============================================================
# 2. ACTUAL OVERLAP OF ALL 12 STATIONS
# ============================================================

all_observed = set.intersection(
    *(stations[name][0] for name in names)
)

all_valid = set.intersection(
    *(stations[name][1] for name in names)
)


all_station_result = pd.DataFrame([{

    "number_of_stations":
        len(names),

    "stations":
        " | ".join(names),

    "common_observed_timestamps":
        len(all_observed),

    "equivalent_observation_days":
        len(all_observed) * 15 / 1440,

    "common_valid_pm25_timestamps":
        len(all_valid),

    "equivalent_valid_pm25_days":
        len(all_valid) * 15 / 1440,

    "first_common_timestamp":
        min(all_observed) if all_observed else pd.NaT,

    "last_common_timestamp":
        max(all_observed) if all_observed else pd.NaT

}])


all_station_result.to_csv(
    OUT_DIR / "EXP-002C_all_station_actual_overlap.csv",
    index=False
)


# ============================================================
# 3. STATION GROUP ANALYSIS
# ============================================================

group_results = []


# Test every possible group of 2–6 stations.
for group_size in range(
    2,
    min(6, len(names)) + 1
):

    for combination_group in combinations(
        names,
        group_size
    ):

        observed_sets = [
            stations[name][0]
            for name in combination_group
        ]

        valid_sets = [
            stations[name][1]
            for name in combination_group
        ]

        common_observed = set.intersection(
            *observed_sets
        )

        common_valid = set.intersection(
            *valid_sets
        )

        group_results.append({

            "group_size":
                group_size,

            "stations":
                " | ".join(combination_group),

            "common_observed_timestamps":
                len(common_observed),

            "equivalent_observation_days":
                len(common_observed) * 15 / 1440,

            "common_valid_pm25_timestamps":
                len(common_valid),

            "equivalent_valid_pm25_days":
                len(common_valid) * 15 / 1440,

            "first_common_valid_pm25_timestamp":
                min(common_valid)
                if common_valid else pd.NaT,

            "last_common_valid_pm25_timestamp":
                max(common_valid)
                if common_valid else pd.NaT
        })


groups_df = pd.DataFrame(group_results)


# Save EVERY tested combination.
groups_df.to_csv(
    OUT_DIR / "EXP-002C_station_group_overlap_all.csv",
    index=False
)


# Top 10 groups for each group size.
top_groups = (
    groups_df
    .sort_values(
        [
            "group_size",
            "common_valid_pm25_timestamps"
        ],
        ascending=[True, False]
    )
    .groupby(
        "group_size",
        group_keys=False
    )
    .head(10)
)


top_groups.to_csv(
    OUT_DIR / "EXP-002C_best_station_groups.csv",
    index=False
)


# ============================================================
# 4. PRINT RESULTS
# ============================================================

print("\n")
print("=" * 80)
print("EXP-002C — ACTUAL TEMPORAL OVERLAP")
print("=" * 80)


print("\n--- TOP 15 PAIRS BY VALID PM2.5 OVERLAP ---\n")

print(
    pair_df
    .head(15)
    .to_string(index=False)
)


print("\n--- ALL-STATION ACTUAL OVERLAP ---\n")

print(
    all_station_result
    .to_string(index=False)
)


print("\n--- BEST STATION GROUPS ---\n")


for group_size in range(
    2,
    min(6, len(names)) + 1
):

    subset = top_groups[
        top_groups["group_size"] == group_size
    ].head(5)

    print(
        f"\nGROUP SIZE {group_size}"
    )

    print("-" * 80)

    print(
        subset[
            [
                "stations",
                "common_valid_pm25_timestamps",
                "equivalent_valid_pm25_days",
                "first_common_valid_pm25_timestamp",
                "last_common_valid_pm25_timestamp"
            ]
        ].to_string(index=False)
    )


print("\n")
print("=" * 80)
print("EXP-002C OVERLAP ANALYSIS COMPLETE")
print("=" * 80)

print("\nResults saved to:")
print(OUT_DIR)
