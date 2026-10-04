"""Cohort analytics over the downloaded clinical datasets.

Taught concepts: pandas read_csv, shape, describe, isnull, select_dtypes,
groupby, value_counts, sort_values, head, plus the os module and matplotlib.

Everything returned from here must survive json.dumps. pandas produces
numpy types and NaN, neither of which is valid strict JSON, so every
public function ends with to_native() and the test suite asserts
json.dumps(..., allow_nan=False) succeeds.

NaN becomes None rather than being dropped, because a missing value in a
clinical column is information. Silence would read as a real zero.
"""

import json
import os

import pandas as pd

DATA_DIR = os.path.join("data", "datasets")
REPORT_PATH = os.path.join(DATA_DIR, "profile_report.csv")
CHART_DIR = os.path.join("static", "charts")

# UCI files mark unknown values with ? and not-applicable with -9. Without
# these markers pandas reads the whole column as text and every numeric
# count comes back zero.
MISSING_MARKERS = ["?", "-9", "NA", "N/A", ""]

TARGET_NAMES = ["target", "outcome", "class", "diagnosis", "status", "malignancy"]

# Risk band cut points per dataset column. Modelled on the BMI
# categorisation problem from Practical 1, same if/elif shape.
#
# Cut points are the dataset's own quartiles rather than textbook clinical
# thresholds, because these are cohort risk bands, not diagnosis. Using
# textbook cutoffs made the bands useless: BMI quartiles are 27.3 / 32 /
# 36.6, so standard cutoffs of 18.5 / 25 / 30 put 472 of 768 patients in
# the top band. Quartiles give roughly equal groups.
#
# Glucose is the exception and keeps clinical cutoffs of 100 and 140,
# because they align with the diabetes screening threshold and produce a
# clean monotonic outcome rate: 8%, 29%, 50%, 82%.
RISK_THRESHOLDS = {
    "pima_diabetes.csv": {
        "Glucose": [100, 140, 200],
        "BMI": [27.3, 32.0, 36.6],
        "Age": [24, 29, 41],
    },
    "heart_disease.csv": {
        "chol": [200, 240, 280],
        "trestbps": [120, 140, 160],
        "oldpeak": [1.0, 2.0, 3.0],
    },
    "parkinsons.csv": {
        "nhr": [0.0059, 0.0117, 0.0256],
        "jitter_pct": [0.0035, 0.0049, 0.0074],
        "rpde": [0.4213, 0.4960, 0.5876],
    },
}


def read_dataset(name):
    """Read one dataset with missing markers converted to NaN."""
    path = os.path.join(DATA_DIR, name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"dataset not found: {name}")

    return pd.read_csv(path, na_values=MISSING_MARKERS, keep_default_na=True)


def find_target(df):
    """Return the name of the target column, or None."""
    for col in df.columns:
        if col.strip().casefold() in TARGET_NAMES:
            return col
    return None


def numeric_columns(df, exclude_target=True):
    """Return numeric column names, optionally excluding the target."""
    target = find_target(df)
    cols = list(df.select_dtypes(include="number").columns)

    if exclude_target and target:
        cols = [c for c in cols if c != target]

    return cols


def to_native(value):
    """Convert pandas and numpy values into plain Python.

    numpy int64 is not JSON serialisable. numpy float64 happens to be,
    because it subclasses float, but it is converted anyway so the output
    type is predictable. NaN and NaT become None, which is what JSON null
    means, rather than the bare NaN token json.dumps emits by default.

    Takes Any on purpose: it is a boundary function whose whole job is to
    accept whatever pandas produced and return something safe.
    """
    if value is None:
        return None

    if isinstance(value, (bool,)):
        return bool(value)

    if isinstance(value, int):
        return int(value)

    if isinstance(value, float):
        return None if pd.isna(value) else float(value)

    if isinstance(value, str):
        return None if value == "" else value

    if isinstance(value, dict):
        return {str(to_native(k)): to_native(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_native(v) for v in value]

    # Scalars only at this point. A Series or Index would make pd.isna
    # return an array, whose truth value is ambiguous.
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        return to_native(value.item())

    return value


def list_datasets():
    """Return the recorded profile of every dataset, or an empty list."""
    if not os.path.exists(REPORT_PATH):
        return []

    return to_native(pd.read_csv(REPORT_PATH).to_dict("records"))


def passing_datasets():
    """Return names of datasets that met every selection criterion."""
    return [d["file"] for d in list_datasets() if d.get("passes") == "PASS"]


def describe_numeric(df):
    """Return describe() for the numeric columns as a plain dict."""
    cols = numeric_columns(df)

    if not cols:
        return {}

    return to_native(df[cols].describe().to_dict())


def value_counts(df, column, limit=10):
    """Return the most common values in a column."""
    if column not in df.columns:
        return {}

    counts = df[column].value_counts(dropna=True)
    trimmed = counts.head(limit)

    return to_native({str(k): int(v) for k, v in trimmed.items()})


def group_means(df, limit=8):
    """Return mean of each numeric column grouped by the target.

    This is the analysis the whole project rests on: it is the Practical 6
    groupby exercise applied to real clinical columns.
    """
    target = find_target(df)

    if target is None:
        return {}

    cols = numeric_columns(df)[:limit]

    if not cols:
        return {}

    return to_native(df.groupby(target)[cols].mean().to_dict())


def target_distribution(df):
    """Return how the target column is distributed."""
    target = find_target(df)

    if target is None:
        return {}

    counts = df[target].value_counts(dropna=True)

    return {
        "column": target,
        "counts": to_native({str(k): int(v) for k, v in counts.items()}),
        "total": int(len(df)),
    }


def strongest_separators(df, limit=5):
    """Rank numeric columns by how differently they spread across targets.

    For each column we compare the spread of group means against the
    overall mean. A large ratio means the target classes sit far apart on
    that column, so it is the most informative one to look at.
    """
    target = find_target(df)

    if target is None:
        return []

    # The target itself is excluded. Grouping by target and then ranking the
    # target column always wins, which tells us nothing.
    cols = numeric_columns(df, exclude_target=True)
    means = df.groupby(target)[cols].mean()
    overall = df[cols].mean()

    ranked = []

    for col in cols:
        column_means = means[col].dropna()

        if column_means.empty:
            continue

        spread = column_means.max() - column_means.min()
        baseline = overall[col]

        if baseline is None or pd.isna(baseline) or baseline == 0:
            continue

        ranked.append({
            "column": col,
            "spread": round(float(spread), 4),
            "relative_spread": round(float(spread / abs(baseline)), 4),
            "group_means": to_native({str(k): float(v)
                                      for k, v in column_means.items()}),
        })

    ranked.sort(key=lambda r: r["relative_spread"], reverse=True)
    return ranked[:limit]


def missing_report(df):
    """Return missing value counts per column."""
    counts = df.isnull().sum()

    return to_native({str(k): int(v) for k, v in counts.items() if v > 0})


def profile(name):
    """Return a full profile of one dataset as JSON-safe values."""
    df = read_dataset(name)
    target = find_target(df)

    return {
        "name": name,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "target": target,
        "numeric_columns": numeric_columns(df),
        "describe": describe_numeric(df),
        "target_distribution": target_distribution(df),
        "group_means": group_means(df),
        "strongest_separators": strongest_separators(df),
        "missing": missing_report(df),
        "value_counts": {
            col: value_counts(df, col)
            for col in numeric_columns(df)[:4]
        },
    }


def risk_band(value, thresholds):
    """Bucket a value using cut points. Same shape as the BMI problem.

    thresholds is a list of three cut points, e.g. [100, 140, 200].
    Anything below the first is low, then moderate, elevated, high.

    None, NaN and unparseable values return "unknown" rather than falling
    through to "high". Every NaN comparison is False, so without the
    guard a missing measurement would be reported as the highest risk in
    the cohort, which is the opposite of what not knowing a value means.
    """
    if value is None or thresholds is None:
        return "unknown"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "unknown"

    if pd.isna(value):
        return "unknown"

    if value < thresholds[0]:
        return "low"
    if value < thresholds[1]:
        return "moderate"
    if value < thresholds[2]:
        return "elevated"
    return "high"


def risk_bands(name, column):
    """Return the distribution of one column across its risk bands."""
    df = read_dataset(name)

    if column not in df.columns:
        raise KeyError(f"{name} has no column {column}")

    thresholds = RISK_THRESHOLDS.get(name, {}).get(column)

    if thresholds is None:
        raise KeyError(f"no thresholds defined for {name} / {column}")

    bands = {}

    for value in df[column]:
        label = risk_band(value, thresholds)
        bands[label] = bands.get(label, 0) + 1

    order = ["low", "moderate", "elevated", "high", "unknown"]

    return {
        "dataset": name,
        "column": column,
        "thresholds": thresholds,
        "bands": {k: bands.get(k, 0) for k in order if bands.get(k, 0) > 0},
        "unreachable_bands": unreachable_bands(df[column], thresholds),
        "total": int(len(df)),
    }


def unreachable_bands(series, thresholds):
    """Return band names the column's range can never enter.

    A band no row can reach is misleading in a chart, because an empty bar
    looks like "nobody in this group" rather than "this group cannot
    exist". Glucose tops out at 199, so a cut point of 200 leaves the high
    band permanently empty.
    """
    values = series.dropna()

    if values.empty:
        return ["low", "moderate", "elevated", "high"]

    smallest = float(values.min())
    largest = float(values.max())

    unreachable = []

    if smallest >= thresholds[2]:
        unreachable.append("low")
        unreachable.append("moderate")
        unreachable.append("elevated")
    elif smallest >= thresholds[1]:
        unreachable.append("low")
        unreachable.append("moderate")
    elif smallest >= thresholds[0]:
        unreachable.append("low")

    if largest < thresholds[0]:
        unreachable.append("moderate")
        unreachable.append("elevated")
        unreachable.append("high")
    elif largest < thresholds[1]:
        unreachable.append("elevated")
        unreachable.append("high")
    elif largest < thresholds[2]:
        unreachable.append("high")

    return unreachable


def available_risk_bands(name):
    """Return which columns have thresholds defined for this dataset."""
    return sorted(RISK_THRESHOLDS.get(name, {}).keys())


def save_charts(name):
    """Render charts to static/charts and return the filenames written.

    Uses explicit plt calls rather than df.hist() or df.plot() so that
    every parameter can be explained.

    The group means chart normalises each column to its own mean before
    plotting. Without that, the widest-ranging column flattens the others.
    Measured on pima_diabetes: Glucose spans 0 to 199 while
    DiabetesPedigreeFunction sits around 0 to 0.4, so plotting raw means
    made the DPF bars a flat line at the bottom of the axis. Dividing each
    column by its own mean puts them on one readable scale.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = read_dataset(name)
    target = find_target(df)
    cols = numeric_columns(df)

    if not os.path.exists(CHART_DIR):
        os.makedirs(CHART_DIR)

    written = []
    slug = name.replace(".csv", "")

    # Histogram of the strongest separating column, split by target.
    separators = strongest_separators(df)
    focus = separators[0]["column"] if separators else (cols[0] if cols else None)

    if focus:
        fig, ax = plt.subplots(figsize=(7, 4))

        if target is not None:
            for label, group in df.groupby(target):
                ax.hist(group[focus].dropna(), bins=30, alpha=0.6,
                        label=f"{target}={label}")
            ax.legend()
        else:
            ax.hist(df[focus].dropna(), bins=30)

        ax.set_title(f"{name}: distribution of {focus}")
        ax.set_xlabel(focus)
        ax.set_ylabel("patients")
        path = os.path.join(CHART_DIR, f"{slug}_{focus}_hist.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        written.append(path)

    # Bar chart: each column as a fraction of its own mean, by target.
    # Dividing by the column mean puts glucose, insulin and BMI on one
    # readable scale, and picks the columns that actually separate.
    if target is not None and cols:
        chosen = [s["column"] for s in separators[:5]] or cols[:5]
        means = df.groupby(target)[chosen].mean()
        relative = means / means.mean()

        fig, ax = plt.subplots(figsize=(9, 4.5))
        relative.plot(kind="bar", ax=ax)
        ax.set_title(f"{name}: mean as a fraction of overall mean, by {target}")
        ax.set_ylabel("x average")
        ax.axhline(1.0, color="#888", linewidth=0.8, linestyle="--")
        ax.legend(title=target, loc="upper center",
                  bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
        plt.xticks(rotation=0)
        path = os.path.join(CHART_DIR, f"{slug}_groupmeans.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        written.append(path)

    # Risk band chart for the first defined column.
    for column in available_risk_bands(name):
        try:
            bands = risk_bands(name, column)
        except KeyError:
            continue

        labels = list(bands["bands"].keys())
        values = [bands["bands"][k] for k in labels]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(labels, values, color="#4a6fa5")
        ax.set_title(f"{name}: {column} risk bands")
        ax.set_ylabel("patients")

        if bands["unreachable_bands"]:
            ax.set_title(f"{name}: {column} risk bands\n"
                         f"(no {', '.join(bands['unreachable_bands'])} band: "
                         f"outside the data range)")

        path = os.path.join(CHART_DIR, f"{slug}_{column}_bands.png")
        fig.savefig(path, dpi=100, bbox_inches="tight")
        plt.close(fig)
        written.append(path)
        break

    return written


def json_check(payload):
    """Return (ok, message). Used by tests to prove a payload is safe."""
    try:
        json.dumps(payload, allow_nan=False)
        return True, "serialises as strict JSON"
    except (TypeError, ValueError) as e:
        return False, str(e)