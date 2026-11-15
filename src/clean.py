"""
Clean parsed discussion-room bookings into an analysis-ready CSV.

Rules (see docs/ANALYSIS_REPORT.md §5):
    - Room labels standardised to numeric 1..7; missing kept as NaN.
    - Known purpose labels standardised; missing kept as NaN.
    - Duration valid if 0 <= minutes <= 720.
    - Uncertain AM/PM records are FLAGGED, never corrected.

Usage:
    python src/clean.py data/processed/parsed_bookings.csv \
                        data/processed/discussion_room_bookings_cleaned.csv
"""
import sys
from pathlib import Path
import pandas as pd

PURPOSE_MAP = {
    "group discussion": "Group Discussion",
    "self - study":     "Self - study",
    "self-study":       "Self - study",
    "self study":       "Self - study",
    "assignments":      "Assignments",
    "assignment":       "Assignments",
    "micro-teaching":   "Micro-teaching",
    "micro teaching":   "Micro-teaching",
    "project works":    "Project works",
    "project work":     "Project works",
    "mentoring":        "Mentoring",
}


def standardise_purpose(value):
    if pd.isna(value):
        return pd.NA
    key = str(value).strip().lower()
    return PURPOSE_MAP.get(key, pd.NA)


def clean(parsed_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(parsed_csv, dtype=str)

    # --- room ---
    df["room_no"] = pd.to_numeric(df["room_no"], errors="coerce")
    df.loc[~df["room_no"].between(1, 7), "room_no"] = pd.NA

    # --- purpose ---
    df["purpose"] = df["purpose"].apply(standardise_purpose)

    # --- timestamps ---
    df["timestamp"]  = pd.to_datetime(df["timestamp"],  errors="coerce")
    df["check_in"]   = pd.to_datetime(df["check_in"],   errors="coerce")
    df["check_out"]  = pd.to_datetime(df["check_out"],  errors="coerce")

    # --- date features ---
    df["year"]       = df["timestamp"].dt.year
    df["month"]      = df["timestamp"].dt.to_period("M").astype(str)
    df["weekday"]    = df["timestamp"].dt.day_name()
    df["hour"]       = df["timestamp"].dt.hour

    # --- duration (flagged, not corrected) ---
    df["duration_minutes_calculated"] = (
        (df["check_out"] - df["check_in"]).dt.total_seconds() / 60
    )
    df["duration_valid"] = df["duration_minutes_calculated"].between(0, 720, inclusive="both")

    # --- booking ID ---
    df.insert(0, "booking_id", range(1, len(df) + 1))

    return df


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python src/clean.py <parsed.csv> <cleaned.csv>")

    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        sys.exit(f"Input not found: {src}")

    cleaned = clean(src)
    cleaned.to_csv(dst, index=False)
    print(f"Wrote {len(cleaned):,} cleaned records to {dst}")
    print(f"Valid durations: {cleaned['duration_valid'].sum():,} / {len(cleaned):,}")


if __name__ == "__main__":
    main()