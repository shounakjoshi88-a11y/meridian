"""Run every Meridian test suite.

Plain functions and asserts, no pytest, because pytest is not covered by
any of the Software Lab-1 practicals.

Run from the project root:  python tests/run_tests.py
Exits 1 if anything fails, so it can gate a commit later.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.path.insert(0, os.path.join(ROOT, "backend"))

SUITES = ["test_triage", "test_registry", "test_store", "test_analytics",
          "test_app"]


def main():
    print("=" * 60)
    print("Meridian test run")
    print("=" * 60)

    passed_suites = []
    failed_suites = []
    missing = []
    total_passed = 0

    for name in SUITES:
        try:
            module = __import__(name)
        except ImportError:
            missing.append(name)
            print(f"\n{'':.<2} {name:<16} not written yet, skipping")
            continue

        tests = [v for k, v in sorted(vars(module).items())
                 if k.startswith("test_") and callable(v)]

        failures = []

        for fn in tests:
            try:
                fn()
            except AssertionError as e:
                failures.append((fn.__name__, str(e)))
            except Exception as e:
                failures.append((fn.__name__, f"{type(e).__name__}: {e}"))

        passed = len(tests) - len(failures)
        total_passed += passed

        if failures:
            failed_suites.append(name)
            print(f"\n{name}: {passed}/{len(tests)} passed")
            for fname, msg in failures:
                print(f"   FAIL  {fname}")
                print(f"         {msg}")
        else:
            passed_suites.append(name)
            print(f"\n{name}: all {len(tests)} passed")

    print()
    print("=" * 60)
    print(f"suites passed : {', '.join(passed_suites) or 'none'}")
    if failed_suites:
        print(f"suites failed : {', '.join(failed_suites)}")
    if missing:
        print(f"not yet built : {', '.join(missing)}")
    print(f"tests passed  : {total_passed}")
    print("=" * 60)

    return 1 if failed_suites else 0


if __name__ == "__main__":
    raise SystemExit(main())