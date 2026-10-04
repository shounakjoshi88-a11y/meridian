"""Show, by running it, why a fixed seed matters and what survives a change.

Everything here uses only the standard library, which is the point: the
generator is not allowed numpy, and `random` is part of Python itself.
This script proves four things we rely on in the notes:

  1. `random` and `secrets` are standard library, so they need no install.
  2. random.seed(n) makes a whole sequence reproducible, byte for byte.
  3. Changing one draw anywhere shifts everything after it, so the order of
     the draws is part of the contract, not an implementation detail.
  4. random.choice over a *set* is not safe, because set iteration order is
     not guaranteed; over a list or dict it is.

Taught concepts used: functions, imports, lists, sets, dicts, tuples, string
formatting, f-strings (Lab 1-2).

Run it:

    python research/scripts/seed_determinism_demo.py
"""

import random
import secrets
import sys

SEED = 20261004


def draw_sequence(count, seed):
    """Return a list of `count` draws from a fresh generator at `seed`."""
    random.seed(seed)
    return [random.random() for _ in range(count)]


def make_patient(age_min, age_max):
    """One synthetic person, drawn from the global random module."""
    age = random.randint(age_min, age_max)
    return {
        "age": age,
        "pulse": round(random.gauss(76, 10), 1),
        "group": random.choices(
            ["O+", "B+", "A+", "AB+", "B-", "A-", "O-", "AB-"],
            weights=[35, 36, 22, 10, 2, 1, 1, 0.5],
            k=1,
        )[0],
    }


def build_cohort(size, seed):
    """Build a cohort deterministically from `seed`."""
    random.seed(seed)
    return [make_patient(0, 90) for _ in range(size)]


def main():
    print("python:", sys.version.split()[0])
    print("random module file:", random.__file__)
    print("secrets module file:", secrets.__file__)
    print("both are on the default import path, no install needed")
    print()

    # --- 2. same seed, same numbers -----------------------------------
    first = draw_sequence(6, SEED)
    second = draw_sequence(6, SEED)
    print("seed", SEED, "run 1:", [round(v, 6) for v in first])
    print("seed", SEED, "run 2:", [round(v, 6) for v in second])
    print("identical:", first == second)
    print()

    # --- 3. one extra draw changes everything downstream -------------
    random.seed(SEED)
    random.random()                     # a stray draw
    shifted = [random.random() for _ in range(6)]
    print("after one stray draw, same seed gives different numbers:",
          shifted != first)
    print()

    # --- 2 again, at cohort level ------------------------------------
    left = build_cohort(5, SEED)
    right = build_cohort(5, SEED)
    print("cohort A:")
    for row in left:
        print("  ", row)
    print("cohort B identical:", left == right)
    print()

    # --- 4. sets are not ordered, lists are --------------------------
    items = ["O+", "B+", "A+", "AB+", "B-", "A-", "O-", "AB-"]
    same_list = []
    for _ in range(4):
        random.seed(SEED)
        same_list.append(random.choice(items))
    print("random.choice over a list, 4 seeded runs:", same_list)
    print("  -> stable, because a list keeps its order")

    as_set = set(items)
    same_set = []
    for _ in range(4):
        random.seed(SEED)
        same_set.append(random.choice(sorted(as_set)))
    print("sorted(set) then choice, 4 seeded runs:", same_set)
    print("  -> sorting first makes a set usable as a lookup source")
    print()

    # weights must sum to the count you ask for
    random.seed(SEED)
    draws = random.choices(["only"], weights=[1.0], k=3)
    print("weights sanity:", draws)
    print("random.gauss sanity:", round(random.Random(1).gauss(0, 1), 6))


if __name__ == "__main__":
    main()