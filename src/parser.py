"""
Parse the raw Discussion Room Booking PDF into a structured CSV.

Usage:
    python src/parser.py data/raw/"Discussion Room Booking.pdf" data/processed/parsed_bookings.csv

Requires: pdfplumber (pip install pdfplumber)
"""
import re
import sys
from pathlib import Path
import pandas as pd

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required. Run: pip install pdfplumber")

ROOM_PATTERN = re.compile(r"Room\s*(?:No\.?)?\s*(\d+)", re.IGNORECASE)
TIME_PATTERN = re.compile(r"\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)", re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}")


def parse_pdf(pdf_path: Path) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                if not TIMESTAMP_PATTERN.search(line):
                    continue
                rows.append(parse_line(line))
    return pd.DataFrame(rows)


def parse_line(line: str) -> dict:
    """Best-effort parse of one booking line. Every field is optional."""
    record = {
        "raw_line": line,
        "timestamp": None,
        "name": None,
        "student_id": None,
        "mobile_no": None,
        "room_no": None,
        "purpose": None,
        "check_in": None,
        "check_out": None,
    }

    ts = TIMESTAMP_PATTERN.search(line)
    if ts:
        record["timestamp"] = ts.group(0)

    room = ROOM_PATTERN.search(line)
    if room:
        record["room_no"] = room.group(1)

    times = TIME_PATTERN.findall(line)
    if len(times) >= 2:
        record["check_in"], record["check_out"] = times[0], times[1]

    for purpose in ["Group Discussion", "Self - study", "Assignments",
                    "Micro-teaching", "Project works", "Mentoring"]:
        if purpose.lower() in line.lower():
            record["purpose"] = purpose
            break

    # IDs and names — audit-only fields, retained in raw parse for traceability
    ids = re.findall(r"\b0?\d{7,8}\b", line)
    if ids:
        record["student_id"] = ids[0]
    mobiles = re.findall(r"\b\d{8}\b", line)
    if mobiles:
        record["mobile_no"] = mobiles[-1]

    return record


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: python src/parser.py <input.pdf> <output.csv>")

    pdf_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        sys.exit(f"PDF not found: {pdf_path}")

    df = parse_pdf(pdf_path)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} records to {out_path}")


if __name__ == "__main__":
    main()