# Concepts beyond the lab syllabus

Every module and library used by Meridian that is **not** covered by the
Software Lab-1 practicals has its own explainer here. Each one is written
for a reader who has done Labs 1 to 6 and nothing more.

The rule the project follows: if a line of code needs a concept that never
appeared in a practical, that concept gets a file in this folder.

## The list

| File | Concept | Where it is used | Closest lab |
|------|---------|------------------|-------------|
| [flask.md](flask.md) | Flask routing, `jsonify`, `request` | `backend/app.py` | Lab 4, functions |
| [csv-module.md](csv-module.md) | `csv.DictReader`, `csv.DictWriter` | `backend/store.py` | Lab 4, file handling |
| [shutil-and-zipfile.md](shutil-and-zipfile.md) | `shutil.copyfile`, `zipfile.ZipFile` | `backend/store.py`, `scripts/fetch_datasets.py` | Lab 4, `os` module |
| [pandas-select-dtypes.md](pandas-select-dtypes.md) | `select_dtypes(include=...)` | `backend/analytics.py`, `scripts/profile_dataset.py` | Lab 6, pandas |
| [pandas-missing-values.md](pandas-missing-values.md) | `na_values`, `keep_default_na` | `backend/analytics.py`, `scripts/profile_dataset.py` | Lab 6, pandas |
| [matplotlib-basics.md](matplotlib-basics.md) | `pyplot`, figures, `savefig` | `backend/analytics.py` | Lab 5, matplotlib |
| [requests.md](requests.md) | `requests.get`, status codes | `scripts/fetch_datasets.py` | syllabus, web scraping |
| [json.md](json.md) | `json.dumps`, `json.loads`, `allow_nan` | `backend/analytics.py`, `tests/` | Lab 4, file handling |

## Concepts deliberately NOT used

Worth recording, because a reviewer may ask why these are absent:

| Concept | Why not |
|---------|---------|
| `bs4` / BeautifulSoup | The syllabus pairs it with `requests` for scraping HTML. Our goal was structured CSV files, not HTML pages, so parsing markup would have been the wrong tool. `requests.md` explains this. |
| `os.walk` | Used in an early version of `backup_all`. Removed: it swept `data/datasets/` too, where two files share a name with registry files and silently overwrote one another when flattened. See `shutil-and-zipfile.md`. |
| pytest | Not in any practical. Tests are plain functions with `assert`, run by `tests/run_tests.py`. |
| Any database | CSV only, by design. The brief called for file-based storage. |
| `scipy` | Listed in the syllabus but never needed. Everything numeric was done with NumPy and pandas. |

## Verifying this list is complete

Run:

```
python scripts/check_concept_coverage.py
```

It parses every `import` statement in `backend/` and `scripts/`, and
reports any module that is neither a standard library module explained
above nor covered by one of these files.