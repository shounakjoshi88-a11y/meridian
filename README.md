# Meridian

A clinical records, triage and analytics tool built as a Software Lab-1 mini
project. Python backend, CSV storage, plain HTML/CSS/JS frontend.

![status](https://img.shields.io/badge/tests-135%20passing-4c9a6a)
![python](https://img.shields.io/badge/python-3.11%2B-4c9a6a)
![flask](https://img.shields.io/badge/API-Flask-4c9a6a)

---

## About this project

Meridian is a small hospital records system. It does three things:

**Symptom triage.** You enter the symptoms a patient reports and it ranks
candidate conditions using set algebra. Intersection and difference over
symptom sets, which is the Lab 3 Venn diagram problem with films replaced by
diseases. Severity breaks near ties, and drug contraindications are checked
against the patient's existing conditions.

**Clinical records.** Patients, consultations, doctors, hospitals, medicines
and pharmacies, all held in CSV files. Search tolerates incomplete records and
returns a ranked list rather than requiring an exact match. A patient with no
blood group on file is still findable by name.

**Cohort analytics.** Three public clinical datasets profiled with pandas:
`describe()`, `groupby().mean()`, `value_counts()`, missing value counts,
strongest separating feature ranking, and risk banding. Charts render
server-side with matplotlib.

### Why it is built this way

The brief for this project was a constraint, not just a suggestion: use only
the concepts taught in Software Lab-1 practicals 0 through 6. Anything outside
that list gets its own explainer in `docs/concepts/`. There are eight of them,
and `scripts/check_concept_coverage.py` proves the list is complete.

That rule shaped real decisions. There is no ORM because no lab covered one.
There is no build step or frontend framework because neither was taught.
`pytest` is absent, so the tests are plain functions with `assert`. Storage is
CSV, not a database, because file handling is Lab 4.

### What it is not

Meridian is a teaching project. It is not a medical device, not a diagnostic
tool, and not for clinical use. Every triage result carries a disclaimer
saying so. All patient, doctor and hospital records are synthetic. No real
patient data appears anywhere in this repository.

---

## Running it

Requires Python 3.11 or newer.

```
pip install flask pandas matplotlib requests
python backend/app.py
```

Open <http://127.0.0.1:8000>. The frontend is served by the same Flask process,
so there is nothing else to start.

Check it is alive:

```
GET /api/health
```

The clinical datasets are committed, so this is only needed to rebuild them
from scratch:

```
python scripts/fetch_datasets.py     # download from UCI and Plotly
python scripts/stage_datasets.py     # attach header rows
python scripts/profile_dataset.py    # score against selection criteria
```

---

## Tests

```
python tests/run_tests.py
```

Plain `assert`, no pytest. Exits non-zero on failure.

| Suite | Covers |
|---|---|
| `test_triage.py` | set scoring, severity bands, contraindications |
| `test_registry.py` | fuzzy search, field weights, validation |
| `test_store.py` | CSV read/write, models, backup, malformed rows |
| `test_analytics.py` | pandas profiling, JSON safety, charts |
| `test_app.py` | every route through Flask's test client |

Three more checks:

```
python scripts/verify_seed_data.py         # referential integrity of the CSVs
python scripts/check_concept_coverage.py   # every import has an explainer
python scripts/check_contrast.py           # WCAG contrast in light and dark
```

---

## Layout

```
backend/
  app.py         Flask routes only, no business logic
  store.py       CSV read/write, backup
  registry.py    fuzzy search and validation
  triage.py      set algebra and risk scoring
  analytics.py   pandas and matplotlib
  models.py      Patient, Visit
data/
  patients.csv  visits.csv  hospitals.csv  doctors.csv
  medicines.csv  stores.csv  diseases.csv
  datasets/      downloaded clinical CSVs and the profile report
docs/
  concepts/      one explainer per out-of-syllabus concept
  specs/         design spec
  plans/         implementation plan
frontend/
  index.html  tokens.css  app.css  app.js
scripts/         dataset pipeline and verification
tests/           five suites
```

---

## The concept boundary

Concepts used, by lab:

| Lab | Concepts | Where |
|---|---|---|
| 1 | variables, operators, typecasting | validation, risk band thresholds, BMI |
| 2 | strings, lists, tuples | CSV parsing, query normalisation, sorting |
| 3 | sets, dicts | symptom matching, contraindications, field weights |
| 4 | functions, files, `os`, classes | the whole persistence layer |
| 5 | `math`, formatted output | reports and scoring |
| 6 | pandas | all analytics |

Concepts not in the labs, each with an explainer in `docs/concepts/`:

Flask, `csv`, `shutil`, `zipfile`, `select_dtypes`, `na_values`, matplotlib,
`requests`, `json`

Deliberately unused, with reasons, in `docs/concepts/README.md`.

---

## Design notes

The frontend has one accent colour and two semantic colours. Severity is
ordered data, so only the two tiers that need action are coloured; the word
always carries the level. Both light and dark modes are designed rather than
inverted, and every text and border pair is contrast checked against WCAG.

A score of zero is rendered as "No match" rather than "0%", because it means
an absence of evidence rather than a measurement of nothing.

---

## Things that were wrong first

These are documented rather than quietly fixed, because they are the
interesting part. Each has a regression test named after the failure.

- `risk_band(NaN)` returned `"high"`. NaN fails every comparison, so a
  missing measurement was reported as the worst case.
- Appending to a CSV with no trailing newline merged two records into one
  malformed line and silently lost both.
- `csv.DictReader` pads short rows with `None` rather than omitting the keys,
  so the missing field check never fired and data was quietly blanked.
- The first group means chart flattened one column into an invisible sliver
  because of scale differences. Only visible by rendering it and looking.
- `backup_all` walked the whole data folder, where two files share a name and
  silently overwrote each other.
- BMI risk bands used textbook cutoffs and put 472 of 768 patients in the top
  band, making the chart meaningless.

---

## Ethics and honesty

The clinical datasets are real and public, downloaded from the UCI repository
and Plotly. Every row of `diseases.csv` uses a standard textbook presentation.

Everything else is synthetic. The hospital, doctor and patient names are
fictional, but the structure is realistic: Nagpur PIN code ranges, `+91` phone
formats, Maharashtra Medical Council style registration numbers, and vitals
inside plausible clinical ranges.

Using fictional entities with realistic formats is a deliberate choice.
Attaching invented doctors to real named hospitals would misrepresent actual
institutions.

## License

MIT