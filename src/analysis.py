"""
Reusable analysis functions consumed by app.py and the notebook.

Privacy: any function that returns a DataFrame drops personal identifiers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chisquare, chi2_contingency

PRIVATE_COLS = ["name", "student_id", "mobile_no", "raw_line"]


def deidentify(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=[c for c in PRIVATE_COLS if c in df.columns])


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = deidentify(df.copy())
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["year"]  = df["timestamp"].dt.year.astype("Int64")
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["weekday"] = df["timestamp"].dt.day_name()

    df["room_label"] = (
        df["room_no"].astype("string").str.strip().replace("", pd.NA)
        .fillna("Missing / unclear")
        .apply(lambda x: f"Room {int(float(x))}" if x[0].isdigit() else x)
    )
    df["purpose_clean"] = (
        df["purpose"].astype("string").str.strip().replace("", pd.NA)
        .fillna("Missing / unclear")
    )

    df["duration_minutes_calculated"] = (
        (pd.to_datetime(df["check_out"], errors="coerce")
         - pd.to_datetime(df["check_in"],  errors="coerce")).dt.total_seconds() / 60
    )
    df["duration_valid"] = df["duration_minutes_calculated"].between(0, 720, inclusive="both")
    return df


# ----------------------------------------------------------------------
# Hypothesis tests
# ----------------------------------------------------------------------
def chi_square_room_equality(df: pd.DataFrame) -> dict:
    """H1: are room booking counts equally distributed?"""
    rc = df["room_label"].value_counts()
    rc = rc[rc.index != "Missing / unclear"]
    if len(rc) < 2:
        return {"ok": False, "reason": "fewer than 2 non-missing rooms"}

    obs = rc.to_numpy(dtype=float)
    exp = np.full_like(obs, obs.mean())
    chi2, p = chisquare(obs, exp)
    dof = len(obs) - 1
    n = obs.sum()
    cohens_w = np.sqrt(chi2 / (n * (len(obs) - 1)))
    return {
        "ok": True,
        "observed": obs.astype(int),
        "expected": exp,
        "labels": rc.index.tolist(),
        "chi2": float(chi2),
        "df": dof,
        "p": float(p),
        "cohens_w": float(cohens_w),
        "reject_h0": bool(p < 0.05),
    }


def chi_square_room_purpose(df: pd.DataFrame) -> dict:
    """H2: is room selection associated with booking purpose?"""
    ct = pd.crosstab(df["room_label"], df["purpose_clean"])
    ct = ct.drop(index="Missing / unclear", errors="ignore")
    ct = ct.drop(columns="Missing / unclear", errors="ignore")
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return {"ok": False, "reason": "fewer than 2×2 usable cells"}

    chi2, p, dof, exp = chi2_contingency(ct)
    n = ct.to_numpy().sum()
    cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    small_pct = float((exp < 5).sum() / exp.size * 100)
    return {
        "ok": True,
        "contingency": ct,
        "expected": exp,
        "chi2": float(chi2),
        "df": int(dof),
        "p": float(p),
        "cramers_v": float(cramers_v),
        "small_cell_pct": small_pct,
        "reject_h0": bool(p < 0.05),
    }


# ----------------------------------------------------------------------
# Descriptive helpers
# ----------------------------------------------------------------------
def duration_summary(df: pd.DataFrame) -> dict:
    valid = df.loc[df["duration_valid"], "duration_minutes_calculated"].dropna()
    return {
        "valid_count": int(valid.count()),
        "mean_minutes": float(valid.mean()) if len(valid) else None,
        "median_minutes": float(valid.median()) if len(valid) else None,
        "min_minutes": float(valid.min()) if len(valid) else None,
        "max_minutes": float(valid.max()) if len(valid) else None,
    }