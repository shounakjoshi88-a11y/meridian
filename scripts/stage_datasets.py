"""Attach header rows to the downloaded clinical datasets.

Taught concepts: os (Lab 4), string methods (Lab 2), loops and lists (Lab 1).

The UCI archives ship raw .data files with no header row, so pandas would
otherwise read the first data row as column names. The real column names
come from each dataset's official .names documentation and are attached
here.

Taught concepts: os (P4), string methods (P2), loops and lists (P1).
Some UCI downloads ship headerless; we attach real column names from the
official .names documentation so pandas reads them correctly.
"""

import os
import shutil

RAW = os.path.join("data", "datasets", "raw")
STAGED = os.path.join("data", "datasets")

HEART_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target",
]

MASS_COLUMNS = [
    "biopsy", "age", "density", "parenchymal_sparsity",
    "texture", "shape", "malignancy",
]

PARKINSONS_RENAME = {
    "name": "patient",
    "MDVP:Fo(Hz)": "fo_hz",
    "MDVP:Fhi(Hz)": "fhi_hz",
    "MDVP:Flo(Hz)": "flo_hz",
    "MDVP:Jitter(%)": "jitter_pct",
    "MDVP:Jitter(Abs)": "jitter_abs",
    "MDVP:RAP": "rap",
    "MDVP:PPQ": "ppq",
    "Jitter:DDP": "ddp",
    "MDVP:Shimmer": "shimmer",
    "MDVP:Shimmer(dB)": "shimmer_db",
    "MDVP:APQ3": "apq3",
    "MDVP:APQ5": "apq5",
    "MDVP:APQ": "apq",
    "Shimmer:DDA": "dda",
    "NHR": "nhr",
    "HNR": "hnr",
    "RPDE": "rpde",
    "DFA": "dfa",
    "D2": "d2",
    "PPE": "ppe",
}


def write_with_header(name, columns, lines):
    """Write lines to a CSV, prefixed with a header row."""
    path = os.path.join(STAGED, name)
    with open(path, "w", newline="") as f:
        f.write(",".join(columns) + "\n")
        for line in lines:
            f.write(line + "\n")
    print(f"  staged {name}  {len(lines)} rows")


def stage_pima():
    """Plotly's copy already carries the standard Pima header."""
    src = os.path.join(RAW, "pima_diabetes_local.csv")
    dst = os.path.join(STAGED, "pima_diabetes.csv")
    if os.path.exists(src):
        shutil.copyfile(src, dst)
        print(f"  staged pima_diabetes.csv")


def stage_heart():
    """Cleveland heart data: no header, 14 columns, '?' means missing."""
    src = os.path.join(RAW, "heart_disease_processed.csv")
    if not os.path.exists(src):
        print("  skip  heart_disease (run fetch first)")
        return
    with open(src) as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    write_with_header("heart_disease.csv", HEART_COLUMNS, lines)


def stage_masses():
    """Mammographic masses: no header, '?' marks missing values."""
    src = os.path.join(RAW, "mammographic_masses.csv")
    if not os.path.exists(src):
        print("  skip  mammographic_masses (run fetch first)")
        return
    with open(src) as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    write_with_header("mammographic_masses.csv", MASS_COLUMNS, lines)


def stage_parkinsons():
    """Parkinsons already ships a header row; just tidy the column names."""
    src = os.path.join(RAW, "parkinsons.csv")
    if not os.path.exists(src):
        print("  skip  parkinsons (run fetch first)")
        return

    with open(src) as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    original_header = lines[0].split(",")
    columns = [PARKINSONS_RENAME.get(c, c) for c in original_header]
    write_with_header("parkinsons.csv", columns, lines[1:])


def main():
    if not os.path.exists(STAGED):
        os.makedirs(STAGED)

    print(f"Staging into {STAGED}")
    stage_pima()
    stage_heart()
    stage_masses()
    stage_parkinsons()


if __name__ == "__main__":
    main()