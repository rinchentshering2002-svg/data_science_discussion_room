# Cleaning Rules

Applied in `src/clean.py` in this order.

## 1. Room labels
- Extract digits from `Room No. X` pattern.
- Keep only integers 1–7.
- Values outside that range, or missing, become NaN.

## 2. Purpose labels
- Normalise case and whitespace.
- Map known variants to canonical categories:
  - Group Discussion, Self-study, Assignments, Micro-teaching, Project works, Mentoring
- Unknown or missing values become NaN.

## 3. Timestamps
- Parse with `errors="coerce"` — unparseable → NaT.
- Derive year, month, weekday, submission hour.

## 4. Duration
- `duration_minutes_calculated = (check_out - check_in) in minutes`.
- `duration_valid = 0 ≤ minutes ≤ 720`.
- **Never** modify AM/PM values.
- Records with negative or > 12 h durations are counted as flagged.

## 5. Duplicates
- Exact duplicate rows are counted but not automatically removed — a repeated
  booking may be legitimate.

## 6. Privacy
- `name`, `student_id`, `mobile_no`, `raw_line` are dropped at load time
  in `app.py` and in `src/analysis.deidentify()`.
- These fields never appear in any chart, table or export.

## 7. Booking ID
- Inserted as `booking_id` = 1..N after cleaning.