"""Profile every candidate dataset and score it against our selection criteria.

Taught concepts: pandas Series/DataFrame, read_csv, shape, describe,
groupby, value_counts, isnull, select_dtypes (Practical 6) and os (Lab 4).
"""

import os
import pandas as pd

DATA_DIR = os.path.join("data", "datasets")
REPORT_PATH = os.path.join(DATA_DIR, "profile_report.csv")

TARGET_NAMES = ["target", "outcome", "class", "diagnosis", "status", "malignancy"]

MIN_ROWS = 150
MIN_NUMERIC = 5
MAX_MISSING_RATIO = 0.20

MISSING_MARKERS = ["?", "-9", "NA", "N/A", ""]


def read_dataset(path):
    """Read a CSV, treating UCI missing markers as real NaN.

    The UCI files use '?' for unknown and -9 for not-applicable. If we do not
    convert them, pandas reads the whole column as text and every numeric
    count comes back zero.
    """
    df = pd.read_csv(path, na_values=MISSING_MARKERS, keep_default_na=True)
    return df


def numeric_columns(df):
    """Return numeric column names, excluding the target."""
    target = find_target(df)
    cols = [c for c in df.select_dtypes(include="number").columns if c != target]
    return cols


def find_target(df):
    """Return the name of the target column, or None."""
    for col in df.columns:
        if col.strip().lower() in TARGET_NAMES:
            return col
    return None


def profile(path):
    """Build one summary dict for a single CSV file."""
    df = read_dataset(path)

    total_cells = df.shape[0] * df.shape[1]
    missing_cells = int(df.isnull().sum().sum())

    numeric_cols = numeric_columns(df)
    categorical_cols = [c for c in df.columns
                        if c not in numeric_cols and c != find_target(df)]

    return {
        "file": os.path.basename(path),
        "rows": df.shape[0],
        "cols": df.shape[1],
        "numeric_cols": len(numeric_cols),
        "categorical_cols": len(categorical_cols),
        "missing_cells": missing_cells,
        "missing_pct": round(100 * missing_cells / total_cells, 2),
        "target": find_target(df) or "NONE",
        "numeric_names": ", ".join(numeric_cols[:6]),
    }


def score_criteria(p):
    """Check the four criteria from Section 4 and explain any failure."""
    failures = []

    if p["target"] == "NONE":
        failures.append("no target column")
    if p["numeric_cols"] < MIN_NUMERIC:
        failures.append(f"only {p['numeric_cols']} numeric cols (need {MIN_NUMERIC})")
    if p["rows"] < MIN_ROWS:
        failures.append(f"only {p['rows']} rows (need {MIN_ROWS})")
    if p["missing_pct"] > MAX_MISSING_RATIO:
        failures.append(f"{p['missing_pct']}% missing (max {MAX_MISSING_RATIO * 100}%)")

    p["passes"] = "PASS" if not failures else "FAIL"
    p["reason"] = "meets all criteria" if not failures else "; ".join(failures)
    return p


def print_detail(path):
    """Print describe() and target breakdown for one dataset."""
    df = read_dataset(path)
    target = find_target(df)

    print("=" * 70)
    print(os.path.basename(path), "-", df.shape[0], "rows x", df.shape[1], "cols")

    print("\n-- describe() --")
    print(df.describe())

    if target:
        print(f"\n-- target: {target} --")
        print(df[target].value_counts())

        numeric = numeric_columns(df)
        if numeric:
            print("\n-- groupby(target).mean() --")
            print(df.groupby(target)[numeric].mean())

        categorical = [c for c in df.columns
                       if c not in numeric and c != target]
        for col in categorical:
            print(f"\n-- value_counts({col}) top 5 --")
            print(df[col].value_counts().head())


def main():
    files = []
    for name in sorted(os.listdir(DATA_DIR)):
        if name.endswith(".csv") and name != "profile_report.csv":
            files.append(os.path.join(DATA_DIR, name))

    print(f"Profiling {len(files)} datasets\n")

    profiles = []
    for path in files:
        p = score_criteria(profile(path))
        profiles.append(p)

    print("=" * 78)
    print(f"{'FILE':<28} {'ROWS':>6} {'COLS':>5} {'NUM':>4} {'MISS%':>7} "
          f"{'TARGET':<12} {'VERDICT':<6}")
    print("=" * 78)
    for p in profiles:
        print(f"{p['file']:<28} {p['rows']:>6} {p['cols']:>5} "
              f"{p['numeric_cols']:>4} {p['missing_pct']:>7} "
              f"{p['target']:<12} {p['passes']:<6}")

    print("\n" + "=" * 78)
    for p in profiles:
        print(f"{p['file']:<28} {p['reason']}")

    df = pd.DataFrame(profiles)
    df.to_csv(REPORT_PATH, index=False)
    print(f"\nReport written to {REPORT_PATH}")

    passing = [p["file"] for p in profiles if p["passes"] == "PASS"]
    print(f"\n{len(passing)} pass all criteria: {', '.join(passing)}")

    for p in profiles:
        print_detail(os.path.join(DATA_DIR, p["file"]))


if __name__ == "__main__":
    main()