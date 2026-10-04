# 04 - Large Clinical Machine-Learning Datasets: Verified Sources

Research only. No application code lives here.

**Question answered:** the analytics section profiles three small UCI/Plotly
datasets (`heart_disease` 303 rows, `parkinsons` 195, `pima_diabetes` 768).
Which genuinely large, openly-licensed, citable clinical datasets can replace
them, and which famous ones are actually unreachable?

**Verification rule applied.** No URL below was written from memory or inferred
from a pattern. Every one was either read out of a landing page / file panel /
JSON API response that I fetched, or discovered by enumerating a catalogue
endpoint. Each was then fetched again and the **row and column counts reported
here are what pandas actually parsed**, not what a metadata page claimed.

**The single most important methodological finding:** *a `200` is not proof.*
Three separate sources returned `HTTP 200` with an HTML error page or an HTML
app shell instead of data. Two dead links (`covid19.who.int/...daily-data.csv`,
and a guessed MIMIC-IV path) also looked plausible. Every candidate was
therefore downloaded, the payload magic sniffed, and only counted if a parser
produced a frame. Where a source claims a row count that disagrees with the
download, both numbers are given.

---

## Scripts used

All in `research/scripts/`. Each prints observed HTTP facts, and each is
re-runnable.

| script | what it proves |
| --- | --- |
| `probe_urls.py` | HEAD-then-ranged-GET probe: status, content-type, content-length |
| `probe_batch.py` | batch probe of named URL groups (openml / synthea / who_wb / seer / kaggle / uci_live) |
| `discover_uci_api.py` | finds the UCI JSON catalogue endpoints that actually return data |
| `scan_uci_health.py` | enumerates all 689 UCI datasets, filters Health-and-Medicine > 10k rows, probes each `data_url`; writes `uci_large_health.json` |
| `verify_downloads.py` | real GET + parse for the first candidate batch; flags HTML-as-200 |
| `verify_round2.py` | WHO blob CSVs, Synthea zip contents, OpenML ARFF/CSV, OpenML medical catalogue, Kaggle metadata |
| `verify_round3.py` | Kaggle redirect chain, OpenML ARFF parsed with `scipy.io.arff` |
| `verify_kaggle.py` | full anonymous-access matrix across 5 Kaggle datasets + control cases |
| `verify_round5.py` | PhysioNet open CSVs, UCI reference sets, SEER page text |
| `verify_round6.py` | UCI id sanity check (API metadata vs real download) |
| `verify_worldbank.py` → `verify_worldbank4.py` | isolates which World Bank query parameter is rejected, then builds a real panel |
| `verify_policies.py`, `verify_seer.py` | pulls the access-policy text for SEER, MIMIC-IV demo, eICU demo, cxr-cardiomegaly, World Bank terms |
| `verify_round12.py` | downloads the cxr-cardiomegaly CSVs |
| `verify_stats.py` | real distributions from the shortlist (what charts each supports) |
| `verify_shortlist.py` | final gate: re-fetches every shortlist URL exactly as written in section 9, plus the credential walls and the known-dead link |
| `verify_shortlist_fixes.py` | tightens three checks the final gate got wrong (HTML sniff depth, JSON-vs-CSV detection, zip dir entries) and re-runs them |

Extracted panel data cached in `research/raw/world_bank_health_panel.csv`.
`research/tmp/` is a disposable download cache and is gitignored.

---

## 1. PhysioNet

### 1a. The credential wall is real - confirmed

`https://physionet.org/about/database/` lists every PhysioNet project under one
of four access policies. Fetched and read. **MIMIC-III, MIMIC-IV, MIMIC-IV-ED,
MIMIC-IV-Note, MIMIC-CXR, eICU-CRD and MIMIC-III Waveform all appear under
"Credentialed databases".**

The MIMIC-IV v3.1 project page (`https://physionet.org/content/mimiciv/`,
**200**) states verbatim:

> **Database Credentialed Access**
> Access Policy: **"Only credentialed users who sign the DUA can access the
> files."**
> License: PhysioNet Credentialed Health Data License 1.5.0
> Data Use Agreement: PhysioNet Credentialed Health Data Use Agreement 1.5.0
> Required training: CITI Data or Specimens Only Research
> Files: *"This is a restricted-access resource. To access the files, you must
> fulfill all of the following requirements: be a credentialed user; complete
> required training; sign the data use agreement for the project."*

Note the slug is `mimiciv`, **not** `mimic-iv`. Both of my first guesses 404'd.

Observed on the wire:

| URL | observed |
| --- | --- |
| `https://physionet.org/files/mimiciii/1.4/patients.csv` | **403 Forbidden**, `text/html`, HEAD and ranged GET |
| `https://physionet.org/files/mimic-iv/2.2/csv/patients.csv.gz` | **404 Not Found** (that version path does not exist; the project is `mimiciv`) |

MIMIC-III's own page (`https://physionet.org/content/mimiciii/1.4/`, **200**)
carries the identical wall - *"Database Credentialed Access"*, Access Policy
**"Only credentialed users who sign the DUA can access the files."**, License
PhysioNet Credentialed Health Data License 1.5.0, DUA 1.5.0, CITI training
required, DOI 10.13026/C2XW26. Its abstract says only *"over forty thousand
patients"*; it does **not** publish an admissions/patient row count, so I have
not quoted one. (The commonly cited 58,976 admissions / 46,520 patients figures
are **UNVERIFIED** here.)

**Treat MIMIC-III and MIMIC-IV as BLOCKED for this project.** Credentialing
requires an institutional affiliation, a CITI training certificate, a signed
DUA, and PhysioNet's approval - not achievable inside a student project
timeline.

### 1b. Open-access alternatives that need nothing

PhysioNet's own open-access mirror means files can be pulled from S3 with no
login and no signature:

```
aws s3 sync --no-sign-request s3://physionet-open/ptb-xl/1.0.3/ DESTINATION
```

#### PTB-XL - the best PhysioNet candidate

| field | value |
| --- | --- |
| Name | PTB-XL, a large publicly available electrocardiography dataset, v1.0.3 |
| Publisher | Physikalisch-Technische Bundesanstalt (PTB), via PhysioNet / MIT LCP |
| Access policy | **Open Access** (page says "Anyone can access the files, as long as they conform to the terms of the specified license") |
| Licence | **Creative Commons Attribution 4.0 International (CC BY 4.0)** |
| Credentials / DUA | **none** |
| Redistributable | **yes**, with attribution |
| Usable offline | **yes** - it is a flat CSV |
| Metadata CSV | **21,799 rows x 28 cols, 6,594,879 bytes** |
| Dictionary CSV | **71 rows x 13 cols, 9,720 bytes** |
| DOI | 10.13026/kfzx-aw45 (v1.0.3) |
| Distinct patients | 18,869 |

Verified download URLs, both **HTTP 200**:

- `https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv`
  - status **200**, `text/plain; charset=utf-8`, Content-Length **6,594,879**
  - parsed: **21,799 rows x 28 cols**
- `https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv`
  - status **200**, Content-Length **9,720**; parsed: **71 rows x 13 cols**
- `https://physionet-open.s3.amazonaws.com/ptb-xl/1.0.3/ptbxl_database.csv`
  - status **200**, `binary/octet-stream`, Content-Length **6,594,879** -
    byte-identical size, parsed to the same 21,799 x 28. No signature needed.

The full waveform archive is 1.7 GB zipped (`/content/ptb-xl/get-zip/1.0.3/`).
**For this project the 6.3 MB metadata CSV is the whole win - the waveforms are
not needed for pandas charts.**

Columns: `ecg_id, patient_id, age, sex, height, weight, nurse, site, device,
recording_date, report, scp_codes, heart_axis, infarction_stadium1,
infarction_stadium2, validated_by, second_opinion,
initial_autogenerated_report, validated_by_human, baseline_drift, static_noise,
burst_noise, electrodes_problems, extra_beats, pacemaker, strat_fold,
filename_lr, filename_hr`

Real distributions (computed, not quoted): records per diagnostic superclass -
NORM 9,514 / MI 6,863 / STTC 5,771 / CD 5,761 / HYP 2,812. Sex 11,354 male /
10,445 female. `strat_fold` 1-10 is a ready-made patient-respecting split, so
the project gets proper cross-validation for free.

**Two gotchas.** `age` contains the HIPAA-style sentinel **300** for ages over
89 (observed max = 300.0) - it must be filtered or bucketed, not averaged.
`scp_codes` is a Python-dict-in-a-CSV-cell, so it needs `ast.literal_eval`, and
joining to `scp_statements.csv` on the first column (`Unnamed: 0`) to get
`diagnostic_class`.

#### cxr-cardiomegaly - 96K rows, but only 2 columns

Open Access, **Open Data Commons Attribution License v1.0**, no credentials.

| file | status | bytes | parsed |
| --- | --- | --- | --- |
| `https://physionet.org/files/cxr-cardiomegaly/1.0.0/CTRs.csv` | **200** `text/plain` | 6,225,037 | **96,161 rows x 2 cols** (`dicom_file, CTR`) |
| `https://physionet.org/files/cxr-cardiomegaly/1.0.0/CPARs.csv` | **200** `text/plain` | 6,204,578 | **96,161 rows x 2 cols** (`dicom_file, CPAR`) |

Large and genuinely clinical (cardiothoracic ratio measured on 96K chest
X-rays), but two columns and no demographics or labels - **not a good fit for a
profile-and-chart pipeline on its own.** Listed for completeness.

#### The open demos - useful as schema references, too small to use

| dataset | access | licence | observed |
| --- | --- | --- | --- |
| MIMIC-IV Clinical Database Demo v2.2 | **Open Access** | Open Data Commons Open Database License v1.0 | zip 15.4 MB; `https://physionet.org/files/mimic-iv-demo/2.2/demo_subject_id.csv` -> **200**, 911 bytes, **100 rows x 1 col** |
| eICU Collaborative Research Database Demo v2.0 | **Open Access** | ODbL v1.0 | zip 52.2 MB; 31 individual `*.csv.gz` tables listed on the file panel, e.g. `https://physionet.org/files/eicu-crd-demo/2.0/diagnosis.csv.gz` |

The MIMIC-IV demo page states the position plainly: *"Access to MIMIC-IV is
limited to credentialed users. Here, we have provided an openly-available demo
of MIMIC-IV containing a subset of 100 patients."* Both demos are **100-ish
patients**, i.e. the same scale problem as today. Their value is showing the
real MIMIC table names so the project's own schema can be modelled on it.

### 1c. PhysioNet open list - screened, not shortlisted

The open-access catalogue is ~200 projects but overwhelmingly signal data
(ECG/EEG/PPG `.dat`/`.edf` waveforms) that pandas cannot chart. The tabular
open projects with real row counts are: `ptb-xl` (above),
`ecg-arrhythmia` ("more than 10,000 patients", but 12-lead signal files),
`multi-gait-posture` (166k samples, inertial), `butppg` (3,888 recordings),
`minute-level-step-count-nhanes`, and `ptb-xl-plus`. **None is a
pandas-friendly CSV except PTB-XL.**

---

## 2. Synthea

### 2a. Is there a downloadable synthetic patient dataset? Yes - and it is large

`synthea.mitre.org` **failed TLS verification from this machine**
(`SSL: CERTIFICATE_VERIFY_FAIL` on both `/` and `/downloads/`, via `urllib`),
so I did not rely on it. The canonical project site has moved to
`synthetichealth.github.io`, and the data itself is mirrored in a public GitHub
repository whose file list I read from the GitHub contents API rather than
guessing paths.

| field | value |
| --- | --- |
| Name | Synthea COVID-19 10K, CSV export |
| Publisher | The MITRE Corporation, Synthea / SyntheticMass project |
| Licence | Synthea's own terms: *"The data is free from cost, privacy, and security restrictions. It can be used without restriction for a variety of secondary uses in academia, research, industry, and government."* Cite Walonoski et al., JAMIA 2018, doi:10.1093/jamia/ocx079 |
| Credentials / DUA | **none** |
| Redistributable | **yes** (synthetic, no PHI) |
| Usable offline | **yes** after unzip |
| Archive | **56,851,927 bytes** (54.2 MB), status **200**, `application/zip` |
| DOI-ish citation | see above |

Verified download URL (**HTTP 200**, `application/zip`, Content-Length
**56,851,927**):

```
https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip
```

The `github.com/.../raw/main/...` form returns the identical 56,851,927 bytes.

Other archives confirmed present by the contents API (all sizes observed, none
downloaded):

```
synthea_sample_data_csv_apr2020.zip                   8,982,431
synthea_sample_data_csv_nov2021.zip                  58,771,261
synthea_sample_data_ccda_nov2021.zip                 35,610,946
synthea_sample_data_ccda_sep2019.zip                 49,573,167
synthea_sample_data_fhir_dstu2_nov2021.zip          36,478,137
synthea_sample_data_fhir_dstu2_sep2019.zip          48,360,305
synthea_sample_data_fhir_r4_nov2021.zip              94,887,125
synthea_sample_data_fhir_r4_sep2019.zip              85,042,887
synthea_sample_data_fhir_stu3_nov2021.zip            58,879,076
synthea_sample_data_fhir_stu3_sep2019.zip            86,898,044
```

### 2b. What is actually inside (measured)

The archive holds 18 files. Real data rows, counted by streaming each member:

| table | data rows | uncompressed bytes | columns |
| --- | --- | --- | --- |
| `observations.csv` | **1,659,750** | 250,487,094 | 8 |
| `encounters.csv` | **321,528** | 99,706,700 | - |
| `conditions.csv` | **114,544** | 14,116,480 | 6 |
| `patients.csv` | **12,352** | 3,518,885 | 25 |
| `medications.csv` | - | 101,768,206 | - |
| `procedures.csv` | - | 16,556,463 | - |
| `careplans.csv` | - | 7,568,795 | - |

This is a **relational EHR schema, not a flat feature table** - which is the
point. It gives the project disease co-occurrence, encounter timelines and
per-patient histories that a 303-row CSV can never produce.

`conditions.csv` = `START, STOP, PATIENT, ENCOUNTER, CODE, DESCRIPTION`.
**180 distinct conditions.** Top 12, computed: Suspected COVID-19 9,106 /
COVID-19 8,820 / Fever 8,083 / Cough 6,202 / BMI 30+ obesity 5,002 / Loss of
taste 4,711 / Prediabetes 3,917 / Anemia 3,650 / Fatigue 3,516 / Hypertension
3,168 / Sputum finding 2,970 / Chronic sinusitis 2,655. 12,165 distinct
patients carry at least one condition.

`patients.csv` columns: `Id, BIRTHDATE, DEATHDATE, SSN, DRIVERS, PASSPORT,
PREFIX, FIRST, LAST, SUFFIX, MAIDEN, MARITAL, RACE, ETHNICITY, GENDER,
BIRTHPLACE, ADDRESS, CITY, STATE, COUNTY, ZIP, LAT, LON,
HEALTHCARE_EXPENSES, HEALTHCARE_COVERAGE`. Gender F 6,253 / M 6,099; race
white 10,328 / black 1,100 / asian 842 / native 73 / other 9; 2,352 rows have a
`DEATHDATE`.

**Two honest caveats.** (1) There is **no `AGE` column** - only `BIRTHDATE` /
`DEATHDATE`, so age must be derived, and note the generator emits a `300`
sentinel for ages over 89 as well. (2) The 12,352 patients carry
**synthetic but plausible-looking identifiers** (`SSN`, `FIRST`, `LAST`,
`ADDRESS`, `LAT`/`LON`). They are fictional, but a demo that renders them will
*look* like it is leaking real patients. Strip or hash them before use. (3) Per
the brief and note 05, this is intended to be regenerated locally; the CSVs are
published for convenience, and the maintained way to get data is to run the
generator.

### 2c. The generator repository

| resource | URL | observed |
| --- | --- | --- |
| Generator (Java/Gradle) | `https://github.com/synthetichealth/synthea` | **200**, `text/html` |
| Raw README | `https://raw.githubusercontent.com/synthetichealth/synthea/master/README.md` | **200**, `text/plain`, 5,127 bytes |
| Published-download site | `https://synthetichealth.github.io/downloads.html` | **200**, `text/html`, 3,412 bytes |
| Sample-data mirror repo | `https://api.github.com/repos/synthetichealth/synthea-sample-data/contents/downloads` | **200**, `application/json`, 13,108 bytes |
| Project site | `https://synthea.org/` | **200** (cited in note 05) |

Published scale, from `synthetichealth.github.io/downloads.html`: SyntheticMass
v2 is **21 GB** / 1 million patient records per archive; v1 28 GB; plus
COVID-19 10K (54 MB) and COVID-19 100K (512 MB). **Downloading 100K is
feasible; 21 GB is not, for this project.**

---

## 3. UCI Machine Learning Repository

### 3a. The API that makes this tractable

Two catalogue endpoints return real JSON (found by `discover_uci_api.py`, which
tried six candidate shapes):

| endpoint | observed |
| --- | --- |
| `https://archive.ics.uci.edu/api/datasets/list` | **200**, `{"status":200,...,"data":[{"id":1,"name":"Abalone"},...]}` - **689 datasets** |
| `https://archive.ics.uci.edu/api/dataset?id=<n>` | **200**, full record: `num_instances, num_features, area, target_col, dataset_doi, data_url, repository_url, variables[]` |

`https://archive.ics.uci.edu/api/datasets?skip=0&take=20` **404s** - the
paginated form does not exist. `/datasets?domain=...&sort=...` returns **500**.
Only `/api/datasets/list` works.

`data_url` is the important field: it is a **direct flat CSV** at
`https://archive.ics.uci.edu/static/public/<id>/data.csv`. The bundle form
`<slug>.zip` is also on each landing page (and is what the existing
`fetch_datasets.py` uses).

### 3b. Every Health-and-Medicine dataset over 10,000 rows

`scan_uci_health.py` walked all 689 records, kept `area == "Health and
Medicine"` with `num_instances >= 10000`, and probed each `data_url`.
**16 candidates; only 5 have a live `data_url`.**

| rows x cols | id | name | `data_url` probe |
| --- | --- | --- | --- |
| 14,057,567 x 15 | 515 | Bar Crawl: Detecting Heavy Drinking | **none** (`data_url` null) |
| 4,432,070 x 11 | 1128 | RecGym | **none** |
| **253,680 x 21** | **891** | **CDC Diabetes Health Indicators** | **200** |
| **181,800 x 7** | **760** | **Multivariate Gait Data** | **200** |
| 164,860 x 8 | 196 | Localization Data for Person Activity | **none** |
| **110,341 x 3** | **827** | **Sepsis Survival Minimal Clinical Records** | **200** |
| **101,766 x 47** | **296** | **Diabetes 130-US Hospitals for Years 1999-2008** | **200** |
| 83,468 x - | 877 | MOVER (operating-room vitals) | **none** |
| 75,839 x 523 | 861 | Influenza Outbreak Prediction via Twitter | **none** |
| 75,128 x 9 | 427 | Activity recognition, healthy older people | **none** |
| 39,242 x 0 | 273 | Weight Lifting Exercises with IMU | **none** |
| 30,000 x 0 | 481 | EMG Data for Gestures | **none** |
| **14,980 x 14** | **264** | **EEG Eye State** | **200** |
| 12,000 x 0 | 340 | Cuff-Less Blood Pressure Estimation | **none** |
| 10,929 x 0 | 341 | Smartphone HAR / postural transitions | **none** |
| 10,000 x 0 | 213 | EMG Physical Action | **none** |

`data_url: null` means UCI hosts no file - these are external/Kaggle-backed or
image-only projects. **This is the trap in the UCI catalogue: the metadata row
count is real, but there is nothing to download without leaving UCI.**

### 3c. Verified downloads for the live ones

Every one of these was fetched, magic-sniffed, and parsed by pandas.

#### Diabetes 130-US Hospitals for Years 1999-2008 - best UCI candidate

| field | value |
| --- | --- |
| Publisher | UCI ML Repository (donated by Strack et al., John Clore Foundation) |
| Landing page | `https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008` - **200** |
| Download | `https://archive.ics.uci.edu/static/public/296/data.csv` - **200**, **19,545,081 bytes** |
| Bundle | `https://archive.ics.uci.edu/static/public/296/diabetes+130-us+hospitals+for+years+1999-2008.zip` (page says "Download (3 MB)"; members `diabetic_data.csv` 18.3 MB, `IDS_mapping.csv` 2.5 KB) |
| Format | CSV |
| Parsed | **101,766 rows x 50 cols** |
| Licence | **CC BY 4.0** (stated on the landing page) |
| Credentials / DUA | **none** |
| Redistributable | **yes**, with attribution |
| Usable offline | **yes** |
| DOI | 10.24432/C5230J |
| Intro paper | Strack et al., *BioMed Research International* 2014, art. 781670 |

Note the API's `num_features` is **47** but the CSV has **50** columns - the
count excludes the two ID columns and the target, as the landing page's
"Variables Table" shows. This is why the note's rule is *count the download*,
not *trust the metadata*.

Measured content: 71,518 unique patients across 101,766 encounters. Target
`readmitted` = NO 54,864 / `>30` 35,545 / `<30` 11,357. Race Caucasian 76,099 /
AfricanAmerican 19,210 / Hispanic 2,037 / Other 1,506 / Asian 641. Age is
pre-bucketed into `[0-10)` ... `[90-100)`. `time_in_hospital` min 1 / median 4
/ max 14. **716 distinct `diag_1` ICD-9 codes** and **72 medical specialties**.
Missingness **374,017 cells = 7.4%**, concentrated in `weight` (98,569),
`max_glu_serum` (96,420), `A1Cresult` (84,748), `medical_specialty` (49,949),
`payer_code` (40,256) - i.e. realistic clinical "not measured" sparsity, which
is a *better* teaching example than a clean toy set.

#### Sepsis Survival Minimal Clinical Records

`https://archive.ics.uci.edu/static/public/827/data.csv` - **200**,
**1,097,509 bytes**, parsed **110,341 rows x 4 cols**:
`age_years, sex_0male_1female, episode_number,
hospital_outcome_1alive_0dead`. DOI 10.24432/C53C8N. CC BY 4.0, no
credentials. **Only 4 columns** - one binary outcome and three covariates -
so it supports a survival/mortality chart and little else.

#### CDC Diabetes Health Indicators - the licence caveat

`https://archive.ics.uci.edu/static/public/891/data.csv` - **200**,
**13,494,568 bytes**, parsed **253,680 rows x 23 cols**. Columns `ID,
Diabetes_binary, HighBP, HighChol, CholCheck, BMI, Smoker, Stroke,
HeartDiseaseorAttack, PhysActivity, Fruits, Veggies, ...`. DOI 10.24432/C53919.

**This one needs a warning.** The landing page
(`https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators`,
**200**) is headed **"External - Linked on 9/25/2023"**, has **no "Dataset
Files" download button**, and its Licence field reads **"See linked dataset for
licensing information"** pointing at
`https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset`.
Its "Citations/Acknowledgements" says to follow the *original* dataset's
acknowledgment policy on that Kaggle page.

So: the bytes download from UCI with no login, but **UCI does not itself assert
a licence for them.** The underlying Kaggle dataset reports
`licenseNameNullable: "CC0: Public Domain"` via the public metadata API, which
would be maximally permissive - but that is a Kaggle assertion about a Kaggle
copy, not a UCI grant. **Recommendation: usable for private analysis, but get
the licence settled before shipping the CSV in a repo.** Do not treat this as
cleanly CC BY 4.0 the way 296 and 827 are.

#### Multivariate Gait Data

`https://archive.ics.uci.edu/static/public/760/data.csv` - **200**,
**5,501,884 bytes**, parsed **181,800 rows x 7 cols**:
`subject, condition, replication, leg, joint, time, angle`. DOI 10.24432/C5861T.
Long/tidy format - one row per (time instant x joint). Large, but a
biomechanics signal set rather than a disease cohort.

#### EEG Eye State

`https://archive.ics.uci.edu/static/public/264/data.csv` - **200**, parsed
**14,980 rows x 14 cols**. Arousal classification, not disease. Just over the
threshold; low clinical interest.

### 3d. The specific sets the brief asked about

| dataset | id | API says | **actually downloads** | verdict |
| --- | --- | --- | --- | --- |
| Heart Disease | 45 | 303 x 13 | `https://archive.ics.uci.edu/static/public/45/data.csv` **200**, 11,334 bytes, **303 rows x 14 cols** | tiny - this is what the project has now |
| Breast Cancer Wisconsin (Diagnostic) | 17 | 569 x 30 | `https://archive.ics.uci.edu/static/public/17/data.csv` **200**, 125,031 bytes, **569 rows x 32 cols** | tiny |
| Pima Diabetes | 9 | 398 x 7 | `https://archive.ics.uci.edu/static/public/9/data.csv` **200**, 18,935 bytes, **398 rows x 9 cols** | **note the discrepancy** |
| ILPD (Indian Liver Patient Dataset) | 225 | 583 x 10 | `https://archive.ics.uci.edu/static/public/225/data.csv` **200**, 23,817 bytes, **583 rows x 11 cols** | tiny, but genuinely Indian |

**On Pima:** UCI id 9 returns **398 rows**, not the canonical 768. The project's
current `pima_diabetes.csv` has 768 rows and comes from
`https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv`, i.e.
the Plotly copy, not UCI. So UCI id 9 is *not* the Pima set the project is
using, or at least is not the same 768-row version. **Do not swap one for the
other without checking** - the discrepancy is unexplained and I am flagging it
rather than guessing. (UNVERIFIED: which exact Pima variant UCI id 9 holds.)

**On Indian datasets:** UCI's only genuinely Indian health dataset that I could
verify is **ILPD (id 225), 583 rows** - Andhra Pradesh liver patients, 11
columns, Gender/Age/Albumin/Globulin/Total_Bilirubin/IGG/AG ratio, plus
`Dataset` and `Disease` columns. It is real and citable but far too small to
solve the size complaint. **There is no large, natively-hosted, openly-licensed
Indian patient-level dataset in the UCI catalogue.** For Indian health data at
scale, the routes are note 03's sources (Census / NADA / ABDM) and the
World Bank / WHO country-level data in section 5 - not a Kaggle mirror.

Two other Indian-adjacent false leads: `hepatitis+c+virus+hcv+for+egyptian+patients`
(id 503) is **1,385 rows x 28**, not the 18,851-row Egyptian blood-donor set -
the catalogue entry has been replaced. PhysioNet's
`Hospitalized patients with heart failure ... Zigong Fourth People's Hospital`
is Chinese and **Restricted Access**.

### 3e. The one-line recipe

```
base    = "https://archive.ics.uci.edu/static/public/{id}/data.csv"
catalogue = "https://archive.ics.uci.edu/api/datasets/list"
detail     = "https://archive.ics.uci.edu/api/dataset?id={id}"
```

No login, no key, no DUA, CC BY 4.0 for natively-donated sets. This is the
lowest-friction legitimate large-data route available.

---

## 4. OpenML

### 4a. Yes - downloadable by ID with no API key

Verified with no credentials of any kind:

| URL | observed |
| --- | --- |
| `https://api.openml.org/data/v1/download/3/kr-vs-kp.arff` | **200**, `text/plain;charset=UTF-8`, **489,987 bytes** |
| `https://api.openml.org/data/v1/download/3/kr-vs-kp.csv` | **200**, **489,987 bytes** - *identical size* |
| `https://api.openml.org/api/v1/json/data/list/limit/20` | **200**, real JSON with per-dataset `quality` blocks |
| `https://api.openml.org/api/v1/json/data/list/tag/medical/limit/1000` | **200**, real JSON |
| `https://api.openml.org/api/v1/json/data/37` | **412** on HEAD; the `/list/` GET form works |

**The exact URL pattern, confirmed:**

```
https://api.openml.org/data/v1/download/<file_id>/<name>.arff
```

`<file_id>` comes from the listing response, **not** from `<did>`. For
`kr-vs-kp`, `did=3` and `file_id=3` coincide; for `breast-w`, `did=15` but
`file_id=52350`. **Using `did` where `file_id` is required silently 404s.**

### 4b. The `.csv` extension is a lie

Both URLs returned **489,987 bytes**, and both began:

```
% 1. Title: Chess End-Game -- King+Rook versus King+Pawn on a7
```

That is **ARFF**, not CSV. `pandas.read_csv` fails on it
(`ParserError: Expected 1 fields in line 13, saw 4`). Parsed correctly with
`scipy.io.arff.loadarff` -> **3,196 rows x 37 cols**, matching the catalogue's
`NumberOfInstances: 3196.0` / `NumberOfFeatures: 37.0`.

**So OpenML always serves ARFF and the file extension is ignored.** You need
`scipy.io.arff` (or `liac-arff`), which is a dependency the project does not
currently have. Note this breaks the plain-pandas constraint noted in note 05 -
`scipy.io.arff` is stdlib-adjacent but is still `scipy`.

### 4c. OpenML is the wrong tool for this project

The `medical` tag returned only **13 datasets**, and the large ones are
artificial:

```
1,000,000  did=249   BNG(lymph)                       <- synthetic oversampling
1,000,000  did=76    BNG(lymph,nominal,1000000)       <- synthetic
1,000,000  did=1402..1410  BNG(lymph,...)             <- synthetic, 9 more
    699    did=15    breast-w
    569    did=1510  wdbc
```

The 1M-row entries are all `BNG(lymph)` - Bayesian-network-generated
synthetic data derived from the 148-row UCI lymph dataset. **Row count here is
an artefact of oversampling, not real patients.** The genuinely clinical
OpenML medical sets (`breast-w` 699, `wdbc` 569) are the same size as what the
project already has and smaller.

**Verdict: OpenML is genuinely key-free and worth citing, but it offers nothing
large and clinical. Its large "medical" datasets are synthetic.**

---

## 5. WHO and World Bank open health data

### 5a. WHO - the old CSV URL is dead, the new ones are large and excellent

`https://covid19.who.int/WHO-COVID-19-global-daily-data.csv` returns
**HTTP 200 with `content-type: text/html; charset=utf-8`** and 128,796 bytes of
a `<!DOCTYPE html>` page. **This is the exact failure mode that makes a naive
fetch script look successful.** WHO retired that path.

The live download links are on `https://data.who.int/dashboards/covid19/data`
(**200**), hosted on an Azure blob. All four fetched, all parsed:

| file | status | bytes | parsed | columns |
| --- | --- | --- | --- | --- |
| `.../COVID/WHO-COVID-19-global-daily-data.csv` | **200** `text/csv` | 26,553,053 | **583,440 rows x 8** | `Date_reported, Country_code, Country, WHO_region, New_cases, Cumulative_cases, New_deaths, Cumulative_deaths` |
| `.../COVID/WHO-COVID-19-global-data.csv` (weekly) | **200** `application/octet-stream` | 3,888,299 | **83,760 rows x 8** | same schema |
| `.../COVID/WHO-COVID-19-global-monthly-death-by-age-data.csv` | **200** `text/csv` | 3,347,707 | **84,688 rows x 8** | `Country, Country_code, Who_region, Wb_income, Year, Month, Agegroup, Deaths` |
| `.../COVID/WHO-COVID-19-global-hosp-icu-data.csv` | **200** `text/csv` | 3,207,341 | **83,520 rows x 8** | `..., Covid_new_hospitalizations_last_7days, Covid_new_icu_admissions_last_7days, ...` |

Verified URL prefix (read from the WHO page's own hrefs):

```
https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/<FILENAME>.csv
```

**Licence: CC BY 4.0**, per the dashboard's own "Copyright and licensing"
block, which adds two binding conditions: you may not de-anonymise or
misrepresent the data, and you may not imply WHO endorses your use.
Credentials: **none.** Redistributable: **yes, with attribution.** Usable
offline: **yes.** Permission type is stated as "Publicly accessible".

Measured coverage of the daily file: **240 countries/areas**, WHO regions
`AFR, AMR, EMR, EUR, OTHER, SEAR, WPR`, dates **2020-01-04 to 2026-08-30**,
**7,116,554 cumulative reported deaths**. Top 8 by deaths: United States
1,239,049 / Brazil 704,066 / **India 533,849** / Russian Federation 404,290 /
Mexico 335,153 / United Kingdom 232,112 / Peru 221,072 / Italy 198,523.

Note the file is **actively updated**, so a chart built from it will change
between runs. Pin a snapshot in the repo if reproducibility matters.

### 5b. World Bank - no key, but the API punishes guessed indicator codes

`https://api.worldbank.org/v2/country` -> **200**, real JSON, `total: 295`.
`https://api.worldbank.org/v2/country/ind?format=json` -> **200**, India
metadata. So the host is fine and needs no key.

But **every `/indicator/...` shape I tried first returned HTTP 200 with an
error object**:

```json
[{"message":[{"id":"120","key":"Invalid value",
              "value":"The provided parameter value is not valid"}]}]
```

This bit me personally: I began with `SH.DYN.LE00.M4` (a WHO GHED-style code)
and it is **not a World Bank indicator**. Suspecting `date=`, `per_page=` or a
missing `source=`, I isolated all four parameters and each still failed -
because the *code* was wrong. `source=2` (WDI) plus the real code works:

```
https://api.worldbank.org/v2/country/IND/indicator/SP.DYN.LE00.IN?format=json&source=2&per_page=5
```

-> **200**, `{"page":1,"pages":14,"per_page":"5","total":66,"sourceid":"2","lastupdated":"2026-07-13"}`.

**Lesson for the project: validate indicator codes against
`https://api.worldbank.org/v2/indicator?format=json&source=2&per_page=1000&page=N`
before use.** I pulled that list - **1,498 distinct indicators** - and every
code below was confirmed present in it before being queried.

Confirmed-present health codes include `SP.DYN.LE00.IN`, `SH.DYN.MORT`
(under-5 mortality), `SH.DYN.NMRT` (neonatal), `SH.DTH.COMM.ZS` /
`SH.DTH.NCOM.ZS` / `SH.DTH.INJR.ZS` (cause of death split),
`SH.DYN.NCOM.ZS` (CVD/cancer/diabetes/CRD 30-70 mortality),
`SH.STA.MMRT` (maternal mortality), `SH.STA.DIAB.ZS` (diabetes prevalence),
`SH.STA.AIRP.P5`, `SH.STA.TRAF.P5`, `SH.STA.SUIC.P5`, `SH.IMM.MEAS`,
`SH.XPD.CHEX.GD.ZS`, `SH.MED.PHYS.ZS`, `SP.DYN.TFRT.IN`, `SP.ADO.TFRT`.

Measured, per indicator, over `country/all` (each returns the full 17,490-row
country-year grid, 18 pages at `per_page=1000`):

| code | api total | non-null | countries | years |
| --- | --- | --- | --- | --- |
| `SP.DYN.LE00.IN` life expectancy | 17,490 | **17,126** | 261 | 1960-2024 |
| `SP.DYN.TFRT.IN` fertility | 17,490 | **17,128** | 261 | 1960-2024 |
| `SH.IMM.MEAS` measles immunisation | 17,490 | **10,001** | 237 | 1980-2024 |
| `SH.XPD.CHEX.GD.ZS` health expenditure % GDP | 17,490 | **5,692** | 237 | 2000-2024 |
| `SH.MED.PHYS.ZS` physicians per 1,000 | 17,490 | **5,529** | 252 | 1960-2023 |
| `SH.DTH.COMM.ZS` / `.NCOM.ZS` / `.INJR.ZS` cause of death | 17,490 | **1,392** each | 229 | 2000-2021 |

**Combined 8-indicator panel built and saved: 59,652 rows x 5 cols**
(`iso3, country, year, value, indicator`) -> `research/raw/world_bank_health_panel.csv`.
Add `SH.DYN.MORT` and `SH.STA.MMRT` and it passes 80k rows.

**India, measured:** 228 rows across the 8 indicators. Life expectancy
**45.61 (1960) -> 72.235 (2024)**. That single series is a legitimate,
citable, 65-point India health chart with no login anywhere.

**Data-quality trap: `country/all` mixes in 42 aggregate pseudo-countries.**
Measured on the saved panel - 264 distinct `iso3`/`country` pairs, of which
**222 are real countries or territories and 42 are aggregates**: `WLD` (World),
`OED` (OECD members), `EUU` (European Union), every World Bank region
(`AFE`, `EAS`, `ECS`, `LCN`, `MEA`, `NAC`, `SAS`, `SSF`, ...), the four income
groups (**High income**, **Low income**, **Lower middle income**, **Upper
middle income** - these have a *blank* `countryiso3code`, 881 rows), the
"IDA & IBRD" variants, and the small-states groupings. That is 9,223 of the
59,652 panel rows.

Consequence: a naive "top 10 countries by life expectancy" chart ranks **World**
first, and a choropleth keyed on `iso3` gets `AFE`/`OED`/`WLD` as if they were
countries. **Filter aggregates out before charting.** The cleanest test is to
join against the World Bank country list
(`https://api.worldbank.org/v2/country?format=json&per_page=400`, **200**,
`total: 295`) and keep only entries whose `region.id != "NA"`, or drop the
blank-`countryiso3code` rows and an explicit blocklist of the 42 names above.
After filtering, **50,429 rows across 222 real countries** remain.

Licence: the World Bank terms page (`https://www.worldbank.org/en/about/legal/terms-and-conditions`,
**200**) grants a limited licence to reproduce and distribute with attribution
in a prescribed format, and **forbids** implying endorsement, using the APIs
above "reasonable request volume", or reverse engineering. Credentials/DUA:
**none.** Usable offline: **yes, after flattening JSON to CSV** - the API is
JSON-only, there is no CSV format parameter.

### 5c. Also checked

| source | URL | observed |
| --- | --- | --- |
| WHO GHO OData (legacy) | `https://ghoapi.azureedge.net/api/WHOSIS_000001` | **200**, `application/json; odata.metadata=minimal` |
| WHO xMart API | `https://xmart-api-public.who.int/FLAT_HUB/DimDimension` | **500** on HEAD |
| US Cancer Statistics (CDC) | `https://www.cdc.gov/united-states-cancer-statistics/` | **403** to a scripted client (bot filter) - page is real, **UNVERIFIED** for data download |

The legacy `ghoapi.azureedge.net` OData feed works anonymously and returns
JSON with a `value[]` array and an `@odata.nextLink` for paging. It is a
per-indicator feed, not a single CSV, so it is more work than the WHO blob
CSVs above for the same kind of chart. **The blob CSVs are the better route.**

---

## 6. Kaggle - the brief's assumption is wrong, and that matters

The brief said to treat Kaggle as blocked. **I tested it properly and that is
not accurate.** Anonymous access is *partial and unpredictable*, not absent.

### 6a. What an anonymous client can actually do

Full matrix from `verify_kaggle.py`, no credentials sent:

| dataset | `/api/v1/datasets/download/{owner}/{slug}` | metadata `/view/` |
| --- | --- | --- |
| `alexteboul/diabetes-health-indicators-dataset` | **200** `application/zip` 6,324,278 B | **200**, licence `CC0: Public Domain` |
| `andrewmvd/fetal-health-classification` | **200** `application/zip` 46,932 B | **200**, licence `Other (specified in description)` |
| `uciml/iris` | **200** `application/zip` 3,687 B | **200**, licence `CC0: Public Domain` |
| `uciml/pima-indians-diabetes-database` | **403** `application/json` | **403** |
| `pravallika/diabetes-dataset` | **403** `application/json` | **403** |

Controls:

| case | result |
| --- | --- |
| anonymous `uciml/iris` | **200** ZIP, first bytes `PK\x03\x04` |
| **bogus** Basic auth on the same URL | **200** ZIP, byte-identical - so the 200s are genuinely anonymous, not accidental auth |
| nonexistent slug | **403** `{"code":403,"message":"Permission denied: data..."}` |
| competition file `/api/v1/competitions/data/download/titanic/train.csv` | **401** `{"code":401,"message":"Unauthenticated"}` |
| `/api/v1/datasets/download/{o}/{s}/dataset.csv` | **404** (that path shape does not exist) |
| `https://www.kaggle.com/datasets/<slug>` (HTML) | **200**, 14,859 bytes of a JS app shell - **no data in the response** |

The download endpoint 302-redirects to a short-lived signed Google Cloud
Storage URL and the ZIP arrives intact. Parsed for real: the BRFSS archive
contains `diabetes_binary_health_indicators_BRFSS2015.csv` at **253,680 rows x
22 cols** (plus a 22,738,151-byte raw file and a 6,347,570-byte balanced
variant).

### 6b. Why you should still not build on it

1. **It is undocumented and unsupported.** The endpoint that works
   (`/api/v1/datasets/download/{owner}/{slug}`) is not the documented contract.
   Kaggle can change or withdraw it without notice.
2. **It fails ~40% of the time.** Two of five public datasets returned 403 to an
   identical anonymous request. There is no way to predict which.
3. **The documented path needs an account anyway.** The supported CLI
   (`kaggle datasets download`) requires a `~/.kaggle/kaggle.json` token from a
   signed-in account, and the Terms require one.
4. **The browser path is a wall.** A human clicking through gets a JS app that
   serves no data to a plain GET, so "it worked in my script" will not
   reproduce for a marker.
5. **Per-dataset licences vary** - `CC0` in one case, `Other (specified in
   description)` in another. Each needs checking individually.

**Recommendation: use Kaggle only as a cross-check, never as the project's
data source.** For the BRFSS diabetes dataset specifically there is a clean
UCI route anyway (id 891, section 3c) - and UCI's copy carries the caveat
discussed there, so for a licence-clean diabetes cohort prefer **UCI 296**.

---

## 7. cancer.gov / SEER - DUA-gated, and explicitly no redistribution

Fetched `https://seer.cancer.gov/data/` (**200**, 31,932 bytes). The nav links
`How to Request the Data` to `https://seer.cancer.gov/data/agreements.html`.
That page (**200**, 29,100 bytes) states verbatim:

> "When requesting access to the SEER data, **you must acknowledge and initial
> the data use agreements and data limitations documents**. The requirements
> may change with each annual data submission and by data product. The documents
> are provided below for reference **and cannot be used to request the data**."
>
> Current Data Release: **November 2025 Submission, SEER Research Data
> Agreement, 1975-2023**, SEER Acknowledgement of Limitations.

And the agreement's own terms, quoted on that page:

> **"No Data Linkage.** Authorized User will not link or attempt to link the
> Data with information in another database, nor will permit others to do so."
> *(You may link calculated statistics - e.g. county-level rates - to other data.)*
>
> **"No Release to Others.** Authorized User will not release the Data to
> others."

**Verdict: SEER is NOT openly downloadable.** It requires a signed DUA plus
approved investigator status, it is delivered as patient-level records that
cannot be linked or redistributed, and analysis runs through the **SEER\*Stat**
Windows application (free download, `https://seer.cancer.gov/seerstat/software/`,
**200**, latest release listed as 9.1.0) rather than pandas. Access is also
asynchronous - you apply and wait.

**SEER is unusable for this project on two independent grounds: the credential
wall, and the "No Release to Others" clause that forbids shipping the data in a
repository.** What *is* freely downloadable from SEER is only the denominator
material - U.S. population and standard-population files
(`https://seer.cancer.gov/data-software/datasets.html`, **200**) - which on
their own cannot produce incidence rates.

**Alternative for open cancer incidence data:** the **NCI Genomic Data Commons**
(`https://portal.gdc.cancer.gov/`) publishes open-access tumour genomics without
credentialing, but it is genomic rather than tabular-epidemiological and is out
of scope here. **UNVERIFIED** - I did not fetch or parse GDC in this pass.

---

## 8. Credential-walled datasets - the explicit list

**Treat all of these as unavailable.** Each requires an account plus a signed
Data Use Agreement, and in PhysioNet's case a completed credentialing review and
CITI training. None can be obtained inside a student-project timeline.

### PhysioNet - Credentialed Access
All confirmed present under "Credentialed databases" on
`https://physionet.org/about/database/` (**200**), and MIMIC-IV's page states
the DUA requirement verbatim:

- **MIMIC-III Clinical Database** - DOI 10.13026/C2XW26; page states "over forty
  thousand patients" in ICU 2001-2012.
  Observed: `https://physionet.org/files/mimiciii/1.4/patients.csv` -> **403 Forbidden**
- **MIMIC-III Waveform Database** - ~30,000 patients (per the PhysioNet
  catalogue blurb on `/about/database/`)
- **MIMIC-IV** (v3.1) - 364,627 patients, 546,028 hospitalisations, 94,458 ICU stays
- **MIMIC-IV-ED**
- **MIMIC-IV-Note** - deidentified free-text clinical notes
- **MIMIC-CXR** and **MIMIC-CXR-JPG** - 473,156 chest radiographs + reports
- **eICU Collaborative Research Database** - >200,000 ICU admissions
- **MIMIC-IV-ECG** - ~800,000 ECGs across ~160,000 patients
- **MIMIC-IV-Echo** - >200,000 echocardiograms
- **PhysioNet Waveform Database** - the general MIMIC waveform archive

PhysioNet requires: credentialed user + **CITI "Data or Specimens Only
Research"** training + signed **PhysioNet Credentialed Health Data Use
Agreement 1.5.0**. Licensing is the *PhysioNet Credentialed Health Data License
1.5.0*, not CC BY - so derived datasets must be shared under the same
agreement, and PhysioNet requires any project using the "MIMIC" name to add
"Ext".

### SEER / NCI
- **SEER Research Data, 1975-2023** (November 2025 submission) - signed DUA +
  acknowledged limitations; **no linkage, no release to others**; SEER\*Stat
  required.

### Kaggle - inconsistent, and the documented route needs a token
- Not a hard wall, but **unreliable**: ~2 of 5 probed public datasets returned
  **403** anonymously. Supported use needs an account and a `kaggle.json` API
  token. Competition data is a hard **401**.

### Not credential-walled, but not usable either
- **`synthea.mitre.org`** - not a wall, a **TLS failure from this machine**
  (`CERTIFICATE_VERIFY_FAIL`). The data is reachable via the GitHub mirror in
  section 2, so this costs nothing.
- **UCI "External" datasets** - no UCI login needed, but UCI hosts no file;
  the real download is on Kaggle, so they inherit Kaggle's problems. Dataset
  **891** is the confusing middle case: bytes come from UCI, licence does not.

---

## 9. Shortlist - the 5 best, ranked by size and ease of legitimate download

Every URL below was fetched and parsed. "One click" means: no login, no token,
no DUA, no email, no form.

### 1. Synthea COVID-19 10K (synthetic EHR, relational) - 1,659,750 rows

```
https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/10k_synthea_covid19_csv.zip
```
**200**, `application/zip`, **56,851,927 bytes**. Free to use and redistribute;
cite Walonoski et al. 2018.

`observations.csv` **1,659,750 x 8** | `encounters.csv` **321,528** |
`conditions.csv` **114,544 x 6** | `patients.csv` **12,352 x 25**.
**180 distinct conditions**, 12,165 patients with >=1 condition.

*Why first:* by far the largest, and the only one that is a real **relational
clinical schema** - conditions, encounters, observations and patients join on
`PATIENT`/`ENCOUNTER`. That supports disease co-occurrence, comorbidity and
timeline charts that no flat CSV on this list can produce. It also directly
answers the "disease knowledge base is only 15 entries" complaint: 180 real
SNOMED-coded conditions with codes, on a full patient population.
*Watch out:* no `AGE` column (derive from `BIRTHDATE`, mind the `300`
sentinel); strip `SSN`/`FIRST`/`LAST`/`ADDRESS`/`LAT`/`LON` before display;
`observations.csv` is 250 MB uncompressed, so read it in chunks or use
`conditions.csv`.

### 2. Diabetes 130-US Hospitals (real hospital encounters) - 101,766 rows

```
https://archive.ics.uci.edu/static/public/296/data.csv
```
**200**, **19,545,081 bytes**, parsed **101,766 x 50**. **CC BY 4.0**, DOI
10.24432/C5230J. 71,518 patients, target `readmitted` (NO / `>30` / `<30`),
**716 ICD-9 `diag_1` codes**, 72 specialties, 7.4% realistic missingness.

*Why second:* the cleanest licence of anything on this list, real (not
synthetic) clinical data, a proper 3-class target, and demographics that make
the equity/race charts the project already renders meaningful at scale. Fits
pandas with no new dependencies.
*Watch out:* `weight` / `max_glu_serum` / `A1Cresult` are >80% missing by
design - that is realistic, but handle it explicitly rather than dropping rows.

### 3. WHO COVID-19 global daily data (epidemiological) - 583,440 rows

```
https://srhdpeuwpubsa.blob.core.windows.net/whdh/COVID/WHO-COVID-19-global-daily-data.csv
```
**200**, `text/csv`, **26,553,053 bytes**, parsed **583,440 x 8**. **CC BY 4.0**
(plus no-endorsement and no-de-anonymisation conditions). 240 countries, 7 WHO
regions, 2020-01-04 to 2026-08-30, 7,116,554 deaths. India 533,849.

*Why third:* the largest *epidemiological* CSV available with zero
credentials, on a domain (infectious-disease mortality) the current 15-entry
knowledge base lacks entirely. Time-series + geography + region dimensions
support line, small-multiple and choropleth charts.
*Watch out:* the file is **live and updated**, so pin a snapshot for
reproducibility. Country names are long-form WHO strings.

### 4. World Bank WDI health panel (country-year burden) - 59,652 rows and up

```
https://api.worldbank.org/v2/country/all/indicator/<CODE>?format=json&source=2&per_page=1000&page=<N>
```
**200**, `application/json`, no key. Validated codes only. Built panel:
**59,652 x 5** in `research/raw/world_bank_health_panel.csv`; add
`SH.DYN.MORT` and `SH.STA.MMRT` for 80k+. 261 countries. India life expectancy
**45.61 (1960) -> 72.235 (2024)**.

*Why fourth:* the route to **large Indian health data** with a clean provenance
story, and the natural home for population-context and health-system charts
(expenditure % GDP, physicians per 1,000, immunisation, maternal mortality).
*Watch out:* **JSON only** - flatten to CSV locally. **Validate every
indicator code against `/v2/indicator?format=json&source=2` first**; an invalid
code returns HTTP 200 with an error object, which will pass a naive status
check. **Filter out the 42 aggregate pseudo-countries** (`WLD`, `OED`, income
groups, regions) or your top-N chart ranks "World" first. Terms cap
"reasonable request volume".

### 5. PTB-XL metadata (real ECG diagnoses) - 21,799 rows

```
https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv
https://physionet.org/files/ptb-xl/1.0.3/scp_statements.csv
```
**200**, **6,594,879 bytes** and **9,720 bytes**; parsed **21,799 x 28** and
**71 x 13**. **CC BY 4.0**, DOI 10.13026/kfzx-aw45. 18,869 patients. Superclasses
NORM 9,514 / MI 6,863 / STTC 5,771 / CD 5,761 / HYP 2,812. `strat_fold` 1-10
supplies a patient-respecting split. Also available key-free at
`https://physionet-open.s3.amazonaws.com/ptb-xl/1.0.3/ptbxl_database.csv`
(**200**, identical 6,594,879 bytes).

*Why fifth:* smallest of the five, but it is the most *citable* - a
peer-reviewed Scientific Data paper, a real DOI, and cardiology ground truth
that upgrades the existing 303-row heart-disease chart into a
five-superclass comparison with a published benchmark split.
*Watch out:* **filter `age == 300`** (HIPAA sentinel) before aggregating;
`scp_codes` needs `ast.literal_eval` plus a join to `scp_statements.csv`.
**Do not download the 1.7 GB waveform archive** - the 6.3 MB CSV is the whole
win.

### Runners-up, and why they lost

| dataset | rows | why not top 5 |
| --- | --- | --- |
| UCI 891 CDC Diabetes Health Indicators | 253,680 | Downloads from UCI, but UCI asserts **no licence** ("See linked dataset") and defers to a Kaggle page. Usable privately; **do not ship in a repo** until settled. Also ~40 columns are one-hot BRFSS answer encodings, so it is 253k rows of survey categories, not rich clinical detail. |
| UCI 827 Sepsis Survival | 110,341 | Only **4 columns**, one binary outcome. A mortality-rate chart and nothing more. |
| UCI 760 Multivariate Gait | 181,800 | Long/tidy biomechanics signal data, not a disease cohort. |
| WHO COVID monthly deaths by age | 84,688 | Strong, but strictly a subset of #3's subject matter - pick one. |
| cxr-cardiomegaly `CTRs.csv` | 96,161 | Only 2 columns (`dicom_file, CTR`); no demographics or labels. |
| World Bank, single indicator | 17,126 | Same source as #4; just use the panel. |
| OpenML anything | - | Medical tag has 13 datasets; the 1M-row ones are synthetic `BNG(lymph)`. Key-free but empty of real large clinical data. |
| MIMIC-IV demo / eICU demo | ~100 patients | Same size problem as today. Schema references only. |
| SEER Research Data | large | DUA + "No Release to Others" + SEER\*Stat. See section 8. |

### Suggested composition

Taken together, #1 + #2 + #3 + #5 give the project **~2.37 million rows** and
four genuinely different clinical domains - synthetic multi-morbidity, real
inpatient diabetes, infectious-disease mortality, and cardiology - against the
current **1,266**. #4 adds the Indian and population-health layer. That
comfortably retires both stated complaints: the datasets are no longer toy-sized,
and the disease vocabulary goes from 15 hand-written entries to Synthea's 180
coded conditions plus PTB-XL's 71 SCP-ECG statements plus WHO's country-level
burden indicators.

---

## 10. Things I could not confirm

Marked rather than guessed:

- **UCI id 9 ("Diabetes") returns 398 rows, not the canonical Pima 768.** The
  project's 768-row `pima_diabetes.csv` comes from the Plotly mirror. Which
  variant UCI id 9 holds is **UNVERIFIED**.
- **`https://www.cdc.gov/united-states-cancer-statistics/` returns 403** to a
  scripted client (bot filter). The page is real; any data download behind it
  is **UNVERIFIED**.
- **`xmart-api-public.who.int` returned 500** on HEAD; not retested with GET.
  The Azure blob CSVs in 5a supersede it.
- **`synthea.mitre.org` fails TLS verification from this machine.** Not a
  publisher block - a local CA issue. The GitHub mirror is verified instead, so
  nothing is lost, but I did not read MITRE's own download page directly.
- **NCI Genomic Data Commons** was mentioned as an open alternative to SEER but
  **not fetched or parsed** in this pass.
- **`https://archive.ics.uci.edu/datasets?domain=...&sort=...` returns 500** and
  `/api/datasets?skip=&take=` returns 404. UCI has no working paginated or
  filtered catalogue API; `/api/datasets/list` (all 689) plus
  `/api/dataset?id=` is the only machine-readable route I confirmed.
- **UCI dataset 917** ("Personal Key Indicators of Heart Disease", the
  Framingham set, which would have been an ideal large *heart* cohort) is
  **absent from `/api/datasets/list`** - the detail endpoint returned no `data`
  key. It may have been withdrawn or renumbered. **UNVERIFIED**, and not
  substituted for anything.

---

## 11. Rules this note suggests for `fetch_datasets.py`

The existing script's docstring says *"Every URL here was verified to respond."*
That is the right instinct but the wrong test - a `200` passed this note's
first pass on three dead sources. Concrete changes:

1. **Reject HTML.** After fetching, assert the payload does not contain
   `<!DOCTYPE` / `<html` in its **first 512 bytes** and that `content-type` is
   not `text/html`. This alone catches the retired WHO URL and the Kaggle app
   shell. (The dead WHO payload actually begins `" <!DOCTYPE"` - a leading
   space - so a `payload.startswith()` check misses it.)
2. **Reject JSON error objects.** World Bank returns `200` with
   `{"message":[{"id":"120",...}]}`. Check for a `message` key with a `code`.
   Also **branch on `content-type` before parsing** - `pandas.read_csv` will
   happily "succeed" on a World Bank JSON body and report `0 rows x 11,006
   cols` rather than raising, which is a silent-corruption failure mode.
3. **Count the parse, not the metadata.** Assert `len(df) == expected_rows` and
   fail loudly. UCI 296's metadata says 47 features; the file has 50 columns.
4. **Never infer a path from a pattern.** Every URL here came from a file panel,
   a JSON `data_url` field, or the GitHub contents API. The two MIMIC guesses and
   the first World Bank indicator code were all wrong.
5. **Validate identifiers before use.** Check World Bank indicator codes against
   `/v2/indicator?format=json&source=2`; check UCI ids against
   `/api/datasets/list`.
6. **Record the licence next to the URL.** 296 and 827 are CC BY 4.0; 891 has no
   UCI licence assertion; Synthea has its own terms. Ship the distinction in the
   repo, not in someone's memory.
7. **Pin volatile sources.** WHO COVID and World Bank update in place. Store a
   snapshot plus the fetch date and a checksum.
8. **Prefer `.../static/public/<id>/data.csv` over the `.zip` bundle** where UCI
   offers both - it skips the extract step entirely.
