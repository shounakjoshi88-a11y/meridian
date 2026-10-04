"""Tests for analytics.py. Plain asserts, no pytest.

Run from the project root:  python tests/test_analytics.py
"""

import json
import os
import sys

# Absolute path, so this works from any working directory and so the
# language server can resolve the import statically.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

import analytics  # noqa: E402


def assert_json_safe(payload, label):
    """Fail loudly if a payload is not valid strict JSON.

    allow_nan=False is what makes this a real check. By default json.dumps
    emits a bare NaN token, which is not valid JSON and breaks strict
    parsers on the frontend.
    """
    ok, message = analytics.json_check(payload)
    assert ok, f"{label} is not strict JSON: {message}"


def test_to_native_converts_numpy_types():
    """numpy int64 must become a plain int."""
    import numpy as np

    assert analytics.to_native(np.int64(5)) == 5
    assert isinstance(analytics.to_native(np.int64(5)), int)

    assert analytics.to_native(np.float64(1.5)) == 1.5
    assert analytics.to_native(np.int64(7) / np.int64(2)) == 3.5

    assert analytics.to_native(None) is None
    assert analytics.to_native(True) is True
    assert isinstance(analytics.to_native(True), bool)
    assert analytics.to_native("") is None
    assert analytics.to_native("abc") == "abc"
    print("  ok  to_native converts numpy ints, floats, None and blanks")


def test_to_native_converts_nan_to_none():
    """NaN becomes None so JSON says null rather than NaN."""
    import numpy as np

    assert analytics.to_native(float("nan")) is None
    assert analytics.to_native(np.float64("nan")) is None
    assert analytics.to_native({"a": float("nan")}) == {"a": None}
    assert analytics.to_native([float("nan"), 1.0]) == [None, 1.0]

    # Proof the conversion matters: raw NaN is rejected by strict JSON.
    try:
        json.dumps({"x": float("nan")}, allow_nan=False)
        raise AssertionError("expected raw NaN to be rejected by allow_nan=False")
    except ValueError:
        pass

    assert_json_safe(analytics.to_native({"x": float("nan")}), "NaN payload")
    print("  ok  NaN becomes None and never reaches json.dumps")


def test_to_native_handles_nested_structures():
    """Dicts and lists are converted recursively, keys stringified."""
    import numpy as np

    payload = {"rows": {np.int64(0): np.int64(768)},
               "cols": [np.int64(1), np.float64(2.5)]}

    out = analytics.to_native(payload)

    assert out == {"rows": {"0": 768}, "cols": [1, 2.5]}
    assert_json_safe(out, "nested payload")
    print("  ok  nested dicts and lists converted recursively")


def test_json_check_detects_bad_payloads():
    """The guard actually catches what it claims to."""
    assert analytics.json_check({"a": 1})[0] is True

    import numpy as np
    ok, msg = analytics.json_check({"a": np.int64(1)})
    assert ok is False, "int64 should have been rejected"
    assert "int64" in msg, msg

    ok2, _ = analytics.json_check({"a": float("nan")})
    assert ok2 is False, "NaN should have been rejected"
    print("  ok  json_check rejects int64 and NaN, accepts plain values")


def test_list_datasets_and_passing():
    """The recorded profile report is readable."""
    every = analytics.list_datasets()
    passing = analytics.passing_datasets()

    assert len(every) == 4, [d["file"] for d in every]
    assert len(passing) == 3, passing
    assert "pima_diabetes.csv" in passing
    assert "mammographic_masses.csv" not in passing
    assert_json_safe(every, "list_datasets")
    print(f"  ok  4 datasets recorded, {len(passing)} pass criteria")


def test_profile_every_passing_dataset():
    """Each selected dataset profiles without error."""
    for name in analytics.passing_datasets():
        p = analytics.profile(name)

        assert p["rows"] > 0, name
        assert p["cols"] > 0, name
        assert p["target"], f"{name} has no target"
        assert p["describe"], f"{name} describe empty"
        assert p["group_means"], f"{name} group_means empty"
        assert p["strongest_separators"], f"{name} no separators"
        assert_json_safe(p, f"profile({name})")

    print(f"  ok  {len(analytics.passing_datasets())} datasets profile cleanly")


def test_profile_payloads_are_strict_json():
    """The phase gate: every profile must survive json.dumps."""
    for name in analytics.passing_datasets():
        ok, msg = analytics.json_check(analytics.profile(name))
        assert ok, f"{name}: {msg}"
    print("  ok  every profile serialises as strict JSON, allow_nan=False")


def test_profile_rows_are_plain_ints():
    """shape values must be int, not numpy int."""
    p = analytics.profile("pima_diabetes.csv")

    assert isinstance(p["rows"], int), type(p["rows"])
    assert isinstance(p["cols"], int), type(p["cols"])

    dist = p["target_distribution"]["counts"]
    for value in dist.values():
        assert isinstance(value, int), (value, type(value))
    print("  ok  rows, cols and counts are plain Python ints")


def test_strongest_separators_excludes_target():
    """The target column must never be its own strongest separator."""
    for name in analytics.passing_datasets():
        p = analytics.profile(name)

        for s in p["strongest_separators"]:
            assert s["column"] != p["target"], (
                f"{name}: target {p['target']} ranked as a separator")
    print("  ok  target column excluded from strongest separators")


def test_strongest_separators_are_ranked():
    """Separators come back best first, with a positive spread."""
    for name in analytics.passing_datasets():
        seps = analytics.profile(name)["strongest_separators"]

        spreads = [s["relative_spread"] for s in seps]
        assert spreads == sorted(spreads, reverse=True), (name, spreads)
        assert all(s["relative_spread"] > 0 for s in seps), name
    print("  ok  separators ranked descending, all spreads positive")


def test_known_separator_values():
    """Spot check against numbers measured directly from the frames.

    These were computed with df.groupby(Outcome).mean() during phase 7
    exploration, so a change here means the analysis changed meaning.
    """
    pima = analytics.profile("pima_diabetes.csv")
    top = pima["strongest_separators"][0]

    assert top["column"] == "Pregnancies", top["column"]
    assert abs(top["group_means"]["0"] - 3.298) < 0.01, top["group_means"]
    assert abs(top["group_means"]["1"] - 4.866) < 0.01, top["group_means"]

    heart = analytics.profile("heart_disease.csv")
    htop = heart["strongest_separators"][0]
    assert htop["column"] == "ca", htop["column"]

    park = analytics.profile("parkinsons.csv")
    ptop = park["strongest_separators"][0]
    assert ptop["column"] == "nhr", ptop["column"]
    print("  ok  separator values match direct pandas measurements")


def test_group_means_covers_every_numeric_column():
    """group_means must not silently drop columns."""
    pima = analytics.profile("pima_diabetes.csv")

    assert len(pima["group_means"]) == 8, list(pima["group_means"])
    assert "Glucose" in pima["group_means"]
    assert "BMI" in pima["group_means"]
    assert "Outcome" not in pima["group_means"]
    print("  ok  group_means covers all 8 numeric columns, target excluded")


def test_missing_markers_become_null():
    """A '?' or -9 must arrive as None, never as the literal string."""
    df = analytics.read_dataset("heart_disease.csv")

    assert df["ca"].isnull().sum() == 4, df["ca"].isnull().sum()

    p = analytics.profile("heart_disease.csv")
    assert p["missing"].get("ca") == 4, p["missing"]
    assert_json_safe(p["missing"], "missing report")
    print("  ok  UCI '?' markers counted as missing, not as text")


def test_risk_band_boundaries():
    """Cut points are exclusive on the right, matching the BMI pattern."""
    t = [100, 140, 200]

    assert analytics.risk_band(99, t) == "low"
    assert analytics.risk_band(100, t) == "moderate"
    assert analytics.risk_band(139.9, t) == "moderate"
    assert analytics.risk_band(140, t) == "elevated"
    assert analytics.risk_band(199, t) == "elevated"
    assert analytics.risk_band(200, t) == "high"
    assert analytics.risk_band(999, t) == "high"
    print("  ok  risk_band boundaries behave like the BMI problem")


def test_risk_band_handles_junk_input():
    """None, blanks and non-numbers return unknown rather than raising."""
    t = [100, 140, 200]

    assert analytics.risk_band(None, t) == "unknown"
    assert analytics.risk_band("", t) == "unknown"
    assert analytics.risk_band("abc", t) == "unknown"
    assert analytics.risk_band(120, None) == "unknown"
    assert analytics.risk_band(float("nan"), t) == "unknown"
    print("  ok  risk_band returns unknown for missing or unparseable values")


def test_risk_bands_counts_sum_to_total():
    """Every row lands in exactly one band."""
    for name in analytics.passing_datasets():
        for col in analytics.available_risk_bands(name):
            b = analytics.risk_bands(name, col)
            assert sum(b["bands"].values()) == b["total"], (name, col, b)
            assert_json_safe(b, f"risk_bands({name},{col})")
    print("  ok  band counts sum to the row total for every column")


def test_risk_band_groups_are_reasonably_balanced():
    """Quartile cut points must not dump most rows in one band.

    The original textbook BMI cutoffs put 472 of 768 patients in the top
    band, which made the chart meaningless.
    """
    for name in analytics.passing_datasets():
        for col in analytics.available_risk_bands(name):
            b = analytics.risk_bands(name, col)
            largest = max(b["bands"].values())
            share = largest / b["total"]

            assert share < 0.60, (name, col, b["bands"])
    print("  ok  no band holds 60% or more of a cohort")


def test_glucose_outcome_rate_rises_monotonically():
    """The bands must be informative, not just tidy.

    Measured outcome rates for the Glucose bands are roughly 8%, 31% and
    69%. If the thresholds change such that these stop rising, the bands
    have stopped saying anything useful.
    """
    df = analytics.read_dataset("pima_diabetes.csv")
    b = analytics.risk_bands("pima_diabetes.csv", "Glucose")
    cuts = b["thresholds"]

    rates = []

    for label, lo, hi in [("low", 0, cuts[0]),
                          ("moderate", cuts[0], cuts[1]),
                          ("elevated", cuts[1], cuts[2])]:
        if label not in b["bands"]:
            continue
        sub = df[(df["Glucose"] >= lo) & (df["Glucose"] < hi)]
        rates.append(float(sub["Outcome"].mean()))

    assert len(rates) == 3, rates
    assert rates[0] < rates[1] < rates[2], rates
    assert rates[-1] > 0.6, rates
    print(f"  ok  glucose bands informative: {[round(r, 3) for r in rates]}")


def test_unreachable_bands_are_detected():
    """A band no row can enter must be reported, not drawn as empty.

    Glucose tops out at 199 with a top cut point of 200, so the high band
    can never be reached. This proves the detection works rather than
    merely returning an empty list every time.
    """
    glucose = analytics.risk_bands("pima_diabetes.csv", "Glucose")

    assert "high" in glucose["unreachable_bands"], glucose
    assert glucose["unreachable_bands"] == ["high"], glucose
    assert "high" not in glucose["bands"], glucose["bands"]

    # A unit level check, independent of any dataset. Values are 10..40.
    import pandas as pd
    series = pd.Series([10.0, 20.0, 30.0, 40.0])

    # Cuts above the whole range: everything is low, three bands unused.
    assert analytics.unreachable_bands(series, [100, 200, 300]) == \
        ["moderate", "elevated", "high"]

    # Cuts below the range: 10 falls into elevated, so low and moderate
    # are both skipped even though 10 exceeds the first cut point.
    assert analytics.unreachable_bands(series, [5, 10, 15]) == \
        ["low", "moderate"], analytics.unreachable_bands(series, [5, 10, 15])

    # Cuts spread across the range: every band used exactly once.
    assert analytics.unreachable_bands(series, [15, 25, 35]) == []

    # Straddling cuts leave the ends unused but keep the middle two.
    assert analytics.unreachable_bands(series, [5, 35, 45]) == ["low", "high"]

    # Datasets using quartile cut points should report nothing unreachable.
    for col in analytics.available_risk_bands("parkinsons.csv"):
        bands = analytics.risk_bands("parkinsons.csv", col)
        assert bands["unreachable_bands"] == [], (col, bands)
    print("  ok  unreachable bands detected correctly, none for parkinsons")


def test_risk_bands_rejects_unknown_column():
    """A column with no thresholds raises rather than returning junk."""
    for bad_column, bad_dataset in [("nosuchcol", "pima_diabetes.csv"),
                                    ("Glucose", "parkinsons.csv")]:
        try:
            analytics.risk_bands(bad_dataset, bad_column)
            raise AssertionError(f"expected failure for {bad_dataset}/{bad_column}")
        except KeyError:
            pass
    print("  ok  unknown column or unthresholds dataset raises KeyError")


def test_unknown_dataset_raises():
    """A missing dataset file is a clear error, not an empty result."""
    try:
        analytics.read_dataset("does_not_exist.csv")
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as e:
        assert "does_not_exist.csv" in str(e), e
    print("  ok  missing dataset raises FileNotFoundError naming the file")


def test_save_charts_writes_pngs():
    """Charts are written as real, non-empty PNG files."""
    import os as _os

    for name in analytics.passing_datasets():
        written = analytics.save_charts(name)

        assert len(written) >= 2, (name, written)
        assert_json_safe(written, "chart list")

        for path in written:
            assert _os.path.exists(path), path
            assert _os.path.getsize(path) > 1000, (path, _os.path.getsize(path))
            with open(path, "rb") as f:
                assert f.read(4) == b"\x89PNG", f"{path} is not a PNG"
    print("  ok  every dataset writes real PNG charts")


def test_value_counts_and_describe_present():
    """The describe and value_counts blocks are populated."""
    p = analytics.profile("pima_diabetes.csv")

    assert p["describe"]["Glucose"]["count"] == 768, p["describe"]["Glucose"]
    assert abs(p["describe"]["Glucose"]["mean"] - 120.89) < 0.1, p["describe"]["Glucose"]

    counts = p["target_distribution"]["counts"]
    assert counts == {"0": 500, "1": 268}, counts
    assert p["target_distribution"]["total"] == 768
    print("  ok  describe and value_counts return expected figures")


def test_excluded_dataset_still_profiles():
    """The excluded dataset must not crash if it is inspected."""
    p = analytics.profile("mammographic_masses.csv")

    assert p["target"] == "malignancy", p["target"]
    assert p["missing"], "expected missing counts"
    assert_json_safe(p, "excluded dataset profile")
    print("  ok  excluded dataset profiles without error")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"running {len(tests)} analytics tests\n")

    failures = []

    for fn in tests:
        try:
            fn()
        except AssertionError as e:
            failures.append(fn.__name__)
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            failures.append(fn.__name__)
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")

    print()
    if failures:
        print(f"{len(failures)} of {len(tests)} failed: {', '.join(failures)}")
        return 1

    print(f"all {len(tests)} analytics tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())