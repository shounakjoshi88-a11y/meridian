"""Vercel entrypoint for Meridian.

Exposes backend/app.py's Flask application for serverless use. Vercel
detects the module-level ``app`` and serves it at the function's URL,
with every path rewired to this file by vercel.json.

The lambda bundle is read-only at run time, so the CSV registries are
copied into /tmp once per instance and the writable locations are handed
to store and analytics through environment variables. Writes therefore
work but are ephemeral: they live until the instance recycles. Local
runs are untouched because the copy is gated on the VERCEL variable,
which Vercel sets for every function and a local shell does not.
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(ROOT, "backend"))

if os.environ.get("VERCEL"):
    runtime = "/tmp/meridian"
    data_dir = os.path.join(runtime, "data")
    chart_dir = os.path.join(runtime, "charts")

    if not os.path.isdir(data_dir):
        shutil.copytree(os.path.join(ROOT, "data"), data_dir)
    os.makedirs(chart_dir, exist_ok=True)

    os.environ["MERIDIAN_DATA_DIR"] = data_dir
    os.environ["MERIDIAN_DATASET_DIR"] = os.path.join(data_dir, "datasets")
    os.environ["MERIDIAN_CHART_DIR"] = chart_dir

from app import app  # noqa: E402,F401
