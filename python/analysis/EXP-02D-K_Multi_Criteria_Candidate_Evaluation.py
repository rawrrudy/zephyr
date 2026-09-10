# ============================================================
# EXP-02D-K — MULTI-CRITERIA CANDIDATE EVALUATION
# ============================================================
#
# Consolidates:
#   02D-E = Sensor placement optimization
#   02D-F = Candidate robustness
#   02D-G = Environmental context
#   02D-H = Population + road exposure
#   02D-I = Road hierarchy
#   02D-J = Fine-scale building context
#
# IMPORTANT:
# This analysis does NOT assign arbitrary "PM2.5 suitability"
# scores to environmental variables.
#
# Objective performance is evaluated separately from contextual
# information.
#
# Analysis version: EXP-02D-K
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


# ------------------------------------------------------------
# 1. PROJECT ROOT
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    r"C:\PORTFOLIO\IRIS --- ISEF\zephyr"
)


# ------------------------------------------------------------
# 2. INPUT FILES
# ------------------------------------------------------------

FILES = {

    "placement":
        PROJECT_ROOT
        / "outputs"
        / "sensor_placement"
        / "EXP-02D-E_Selected_Sensor_Candidates.csv",

    "robustness":
        PROJECT_ROOT
        / "outputs"
        / "sensor_robustness"
        / "EXP-02D-F_Local_Candidate_Robustness.csv",

    "environment":
        PROJECT_ROOT
        / "outputs"
        / "environmental_context"
        / "EXP-02D-G_Candidate_Environmental_Context.csv",

    "exposure":
        PROJECT_ROOT
        / "outputs"
        / "road_population_exposure"
        / "EXP-02D-H_Road_Population_Exposure.csv",

    "road":
        PROJECT_ROOT
        / "outputs"
        / "road_hierarchy"
        / "EXP-02D-I_Road_Hierarchy_Screening.csv",

    "building":
        PROJECT_ROOT
        / "outputs"
        / "fine_scale_site_screening"
        / "EXP-02D-J_Fine_Scale_Site_Screening.csv"
}


# ------------------------------------------------------------
# 3. OUTPUT DIRECTORY
# ------------------------------------------------------------

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "candidate_evaluation"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ------------------------------------------------------------
# 4. LOAD DATA
# ------------------------------------------------------------

print()
print("=" * 70)
print("EXP-02D-K — MULTI-CRITERIA CANDIDATE EVALUATION")
print("=" * 70)

datasets = {}

for name, path in FILES.items():

    if not path.exists():

        raise FileNotFoundError(
            f"\nRequired dataset missing: {name}\n"
            f"Expected:\n{path}"
        )

    df = pd.read_csv(path)

    datasets[name] = df

    print()
    print(f"[OK] {name}")
    print(f"     File: {path.name}")
    print(f"     Rows: {len(df)}")
    print(f"     Columns: {len(df.columns)}")


# ------------------------------------------------------------
# 5. PRINT SCHEMAS
# ------------------------------------------------------------

print()
print("=" * 70)
print("INPUT SCHEMAS")
print("=" * 70)

for name, df in datasets.items():

    print()
    print(name.upper())
    print(df.columns.tolist())


# ------------------------------------------------------------
# 6. SENSOR IDENTIFIER NORMALIZATION
# ------------------------------------------------------------

def normalize_sensor_column(df, dataset_name):

    candidates = [

        "sensor",
        "sensor_number",
        "sensor_id",
        "candidate",
        "candidate_id"

    ]

    for col in candidates:

        if col in df.columns:

            out = df.copy()

            out["sensor"] = (
                out[col]
                .astype(str)
                .str.strip()
            )

            # Convert "1" -> "Sensor_1"
            out["sensor"] = out["sensor"].apply(
                lambda x:
                    x if x.startswith("Sensor_")
                    else f"Sensor_{x}"
            )

            return out

    raise ValueError(
        f"\nCould not identify sensor identifier "
        f"in {dataset_name}.\n"
        f"Available columns:\n"
        f"{df.columns.tolist()}"
    )


for name in datasets:

    datasets[name] = normalize_sensor_column(
        datasets[name],
        name
    )


# ------------------------------------------------------------
# 7. MASTER TABLE
# ------------------------------------------------------------

placement = datasets["placement"]

master = (
    placement[
        [
            "sensor",
            "latitude",
            "longitude"
        ]
    ]
    .drop_duplicates("sensor")
    .copy()
)


# ------------------------------------------------------------
# 8. 02D-E SPATIAL OPTIMIZATION
# ------------------------------------------------------------

placement = datasets["placement"]


# Final network mean distance associated with selecting
# each candidate.

if (
    "mean_nearest_distance_after_placement_km"
    in placement.columns
):

    temp = placement[
        [
            "sensor",
            "mean_nearest_distance_after_placement_km"
        ]
    ].copy()

    temp = temp.rename(
        columns={
            "mean_nearest_distance_after_placement_km":
                "mean_distance_after_candidate_km"
        }
    )

    master = master.merge(
        temp,
        on="sensor",
        how="left"
    )


# Distance to existing network.

if (
    "distance_to_existing_network_km"
    in placement.columns
):

    temp = placement[
        [
            "sensor",
            "distance_to_existing_network_km"
        ]
    ].copy()

    master = master.merge(
        temp,
        on="sensor",
        how="left"
    )


# ------------------------------------------------------------
# 9. CALCULATE MARGINAL IMPROVEMENT
# ------------------------------------------------------------
#
# The baseline from 02D-C:
#
#   mean nearest-station distance =
#   3.112151 km
#
# For each candidate:
#
#   improvement =
#   baseline - mean distance after candidate
#
# This represents the improvement in the complete network
# after adding that candidate at its corresponding greedy
# selection stage.
# ------------------------------------------------------------

BASELINE_MEAN_DISTANCE_KM = 3.112151


if (
    "mean_distance_after_candidate_km"
    in master.columns
):

    master[
        "spatial_improvement_km"
    ] = (
        BASELINE_MEAN_DISTANCE_KM
        -
        master[
            "mean_distance_after_candidate_km"
        ]
    )


# ------------------------------------------------------------
# 10. 02D-F ROBUSTNESS
# ------------------------------------------------------------

robustness = datasets["robustness"]


# Find the numerical performance column.

possible_robustness_columns = [

    "network_mean_distance_km",
    "mean_distance_km",
    "three_sensor_mean_distance_km",
    "mean_nearest_distance_km"

]

robustness_metric = None

for col in possible_robustness_columns:

    if col in robustness.columns:

        robustness_metric = col
        break


if robustness_metric is not None:

    robustness[
        robustness_metric
    ] = pd.to_numeric(
        robustness[
            robustness_metric
        ],
        errors="coerce"
    )

    grouped = (
        robustness
        .groupby("sensor")[robustness_metric]
        .agg(
            robustness_min_km="min",
            robustness_max_km="max",
            robustness_mean_km="mean"
        )
        .reset_index()
    )

    grouped[
        "robustness_range_km"
    ] = (
        grouped[
            "robustness_max_km"
        ]
        -
        grouped[
            "robustness_min_km"
        ]
    )

    master = master.merge(
        grouped,
        on="sensor",
        how="left"
    )

else:

    print()
    print(
        "WARNING: No recognized robustness metric "
        "was found in 02D-F."
    )


# ------------------------------------------------------------
# 11. ENVIRONMENTAL CONTEXT
# ------------------------------------------------------------

environment = datasets["environment"]


def merge_if_present(
    master_df,
    source_df,
    column,
    output_name=None
):

    if column not in source_df.columns:

        return master_df

    if output_name is None:

        output_name = column

    temp = source_df[
        [
            "sensor",
            column
        ]
    ].copy()

    temp = temp.rename(
        columns={
            column:
                output_name
        }
    )

    return master_df.merge(
        temp,
        on="sensor",
        how="left"
    )


# Environmental variables we want to preserve.

environment_targets = [

    (
        "LC_built-up_percent",
        "built_up_percent"
    ),

    (
        "LC_tree_cover_percent",
        "tree_cover_percent"
    ),

    (
        "LC_cropland_percent",
        "cropland_percent"
    ),

    (
        "LC_grassland_percent",
        "grassland_percent"
    ),

    (
        "LC_shrubland_percent",
        "shrubland_percent"
    ),

    (
        "estimated_built_surface_percent",
        "estimated_built_surface_percent"
    )

]


for source, output in environment_targets:

    master = merge_if_present(
        master,
        environment,
        source,
        output
    )


# ------------------------------------------------------------
# 12. POPULATION + ROAD EXPOSURE
# ------------------------------------------------------------

exposure = datasets["exposure"]


exposure_targets = [

    (
        "population_density_per_km2",
        "population_density_per_km2"
    ),

    (
        "road_density_km_per_km2",
        "road_density_km_per_km2"
    ),

    (
        "nearest_road_distance_m",
        "nearest_road_distance_m"
    )

]


for source, output in exposure_targets:

    master = merge_if_present(
        master,
        exposure,
        source,
        output
    )


# ------------------------------------------------------------
# 13. ROAD HIERARCHY
# ------------------------------------------------------------

road = datasets["road"]


road_targets = [

    (
        "major_road_density_500m_km_per_km2",
        "major_road_density_500m_km_per_km2"
    ),

    (
        "major_500m_km",
        "major_road_length_500m_km"
    ),

    (
        "nearest_primary_m",
        "nearest_primary_m"
    ),

    (
        "nearest_tertiary_m",
        "nearest_tertiary_m"
    )

]


for source, output in road_targets:

    master = merge_if_present(
        master,
        road,
        source,
        output
    )


# ------------------------------------------------------------
# 14. BUILDING CONTEXT
# ------------------------------------------------------------

building = datasets["building"]


building_targets = [

    (
        "building_count_100m",
        "building_count_100m"
    ),

    (
        "building_count_250m",
        "building_count_250m"
    ),

    (
        "building_coverage_100m_percent",
        "building_coverage_100m_percent"
    ),

    (
        "building_coverage_250m_percent",
        "building_coverage_250m_percent"
    ),

    (
        "building_density_100m_per_km2",
        "building_density_100m_per_km2"
    ),

    (
        "building_density_250m_per_km2",
        "building_density_250m_per_km2"
    ),

    (
        "nearest_building_distance_m",
        "nearest_building_distance_m"
    ),

    (
        "candidate_inside_mapped_building",
        "candidate_inside_mapped_building"
    )

]


for source, output in building_targets:

    master = merge_if_present(
        master,
        building,
        source,
        output
    )


# ------------------------------------------------------------
# 15. OBJECTIVE SPATIAL SCORE
# ------------------------------------------------------------
#
# Higher spatial improvement = better.
#
# We normalize only across the three candidates.
# ------------------------------------------------------------

def minmax(series):

    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    if values.dropna().empty:

        return pd.Series(
            np.nan,
            index=series.index
        )

    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:

        return pd.Series(
            1.0,
            index=series.index
        )

    return (
        values - minimum
    ) / (
        maximum - minimum
    )


if "spatial_improvement_km" in master.columns:

    master[
        "spatial_improvement_score"
    ] = minmax(
        master[
            "spatial_improvement_km"
        ]
    )


# ------------------------------------------------------------
# 16. ROBUSTNESS SCORE
# ------------------------------------------------------------
#
# Smaller local performance range = more robust.
# ------------------------------------------------------------

if "robustness_range_km" in master.columns:

    master[
        "robustness_score"
    ] = minmax(
        -master[
            "robustness_range_km"
        ]
    )


# ------------------------------------------------------------
# 17. OBJECTIVE PERFORMANCE SCORE
# ------------------------------------------------------------
#
# Equal weighting:
#
#   50% spatial improvement
#   50% robustness
#
# Contextual variables are NOT included.
# ------------------------------------------------------------

if (
    "spatial_improvement_score"
    in master.columns
    and
    "robustness_score"
    in master.columns
):

    master[
        "objective_performance_score"
    ] = (
        0.5
        * master[
            "spatial_improvement_score"
        ]
        +
        0.5
        * master[
            "robustness_score"
        ]
    )


# ------------------------------------------------------------
# 18. BUILDING CONFLICT SCREEN
# ------------------------------------------------------------

if "candidate_inside_mapped_building" in master.columns:

    master[
        "building_conflict"
    ] = (
        master[
            "candidate_inside_mapped_building"
        ]
        .astype(str)
        .str.lower()
        .isin(
            [
                "true",
                "1",
                "yes"
            ]
        )
    )


# ------------------------------------------------------------
# 19. OBJECTIVE RANK
# ------------------------------------------------------------

if "objective_performance_score" in master.columns:

    master[
        "objective_rank"
    ] = (
        master[
            "objective_performance_score"
        ]
        .rank(
            ascending=False,
            method="min"
        )
        .astype("Int64")
    )


# ------------------------------------------------------------
# 20. SCREENING DECISION
# ------------------------------------------------------------

def decision(row):

    if (
        "building_conflict"
        in row.index
        and
        row[
            "building_conflict"
        ]
        is True
    ):

        return (
            "REVIEW — mapped building conflict"
        )

    if (
        "objective_performance_score"
        not in row.index
        or
        pd.isna(
            row[
                "objective_performance_score"
            ]
        )
    ):

        return (
            "REVIEW — incomplete objective data"
        )

    return (
        "RETAIN — survives objective screening"
    )


master[
    "screening_decision"
] = master.apply(
    decision,
    axis=1
)


# ------------------------------------------------------------
# 21. SORT
# ------------------------------------------------------------

if "objective_rank" in master.columns:

    master = master.sort_values(
        [
            "objective_rank",
            "sensor"
        ]
    )

else:

    master = master.sort_values(
        "sensor"
    )


# ------------------------------------------------------------
# 22. ROUND NUMERICAL VALUES
# ------------------------------------------------------------

for col in master.columns:

    if pd.api.types.is_numeric_dtype(
        master[col]
    ):

        master[col] = master[col].round(6)


# ------------------------------------------------------------
# 23. PRINT FINAL EVALUATION
# ------------------------------------------------------------

print()
print("=" * 70)
print("FINAL CANDIDATE EVALUATION")
print("=" * 70)

print()

print(
    master.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 24. SAVE COMPLETE TABLE
# ------------------------------------------------------------

master_output = (
    OUTPUT_DIR
    / "EXP-02D-K_Candidate_Evaluation.csv"
)

master.to_csv(
    master_output,
    index=False
)


# ------------------------------------------------------------
# 25. SAVE OBJECTIVE RANKING
# ------------------------------------------------------------

ranking_columns = [

    "objective_rank",
    "sensor",
    "latitude",
    "longitude",
    "spatial_improvement_km",
    "robustness_range_km",
    "objective_performance_score",
    "screening_decision"

]

ranking_columns = [
    col
    for col in ranking_columns
    if col in master.columns
]


ranking_output = (
    OUTPUT_DIR
    / "EXP-02D-K_Objective_Ranking.csv"
)

master[
    ranking_columns
].to_csv(
    ranking_output,
    index=False
)


# ------------------------------------------------------------
# 26. SAVE PARAMETERS
# ------------------------------------------------------------

parameters = pd.DataFrame({

    "parameter": [

        "analysis_version",

        "baseline_mean_nearest_station_distance_km",

        "spatial_improvement_weight",

        "robustness_weight",

        "objective_score_definition",

        "context_variables_definition"

    ],

    "value": [

        "EXP-02D-K",

        BASELINE_MEAN_DISTANCE_KM,

        0.5,

        0.5,

        (
            "0.5 * normalized spatial improvement "
            "+ 0.5 * normalized robustness"
        ),

        (
            "Land cover, population, roads and "
            "buildings are retained as contextual "
            "descriptors and are not treated as "
            "intrinsically good or bad."
        )

    ]

})


parameters_output = (
    OUTPUT_DIR
    / "EXP-02D-K_Methodological_Parameters.csv"
)

parameters.to_csv(
    parameters_output,
    index=False
)


# ------------------------------------------------------------
# 27. FINAL STATUS
# ------------------------------------------------------------

print()
print("=" * 70)
print("EXP-02D-K COMPLETE")
print("=" * 70)

print()
print("Created:")

print(
    master_output
)

print(
    ranking_output
)

print(
    parameters_output
)

print()
print(
    "Objective ranking uses spatial performance "
    "and robustness only."
)

print(
    "Environmental variables remain contextual "
    "descriptors."
)