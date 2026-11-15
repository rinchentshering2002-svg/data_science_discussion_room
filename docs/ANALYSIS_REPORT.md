# Discussion Room Booking Analytics
## Complete Analysis Report

**Module:** PRG405 — Introduction to Data Science
**Dataset:** Discussion Room Booking (16 Aug 2023 – 19 Apr 2025)
**Records analysed:** 1,747
**Tools:** Python, Pandas, NumPy, Matplotlib, SciPy, Streamlit, Plotly
**Team:** Rinchen Tshering, Dorji Wangmo, Karma Wangchuk, Nima Tashi, Pema Yangki
**Guided by:** Phurpa Dorji Tamang — Samtse College of Education

---

## 1. Project Overview

This project analyses the supplied Discussion Room Booking dataset to identify
patterns in room demand, booking purpose and time-based activity, and to evaluate
source-data quality. Results are delivered through an interactive Streamlit
dashboard and supported by this report.

A booking record represents a **reservation**, not verified physical room
occupancy. All findings are interpreted with that limitation in mind.

---

## 2. Problem Statement

Booking information was supplied as a **PDF export** rather than a clean
analytical table, making it difficult to compare rooms, purposes and time
patterns efficiently. The source also contains:

- inconsistent room labels,
- missing or unclear values,
- incomplete records,
- questionable AM/PM time entries,
- check-out times that can appear earlier than check-in times.

The project converts this source into a structured, reproducible, de-identified
dataset and an interactive dashboard.

---

## 3. Aim and Objectives

**Aim:** To analyse discussion-room booking records and develop an interactive
dashboard that communicates room-use patterns and data-quality issues.

**Objectives:**
1. Convert the PDF records into structured data.
2. Clean inconsistent room, purpose, date and time fields.
3. Use Pandas and NumPy for exploratory analysis.
4. Identify room, purpose, monthly, yearly and weekday patterns.
5. Assess booking-duration data quality.
6. Test two hypotheses using formal statistics.
7. Develop an interactive Streamlit/Plotly dashboard.
8. Document the complete workflow and limitations.

---

## 4. Dataset Description

The processed dataset contains **1,747 timestamped records** from **16 August 2023
to 19 April 2025**.

| Source field | Analytical use |
|---|---|
| Timestamp | Date/time trends |
| Name | Audit only — **excluded from analysis and dashboard** |
| Faculty EID / Student ID | Identification — **excluded** |
| Mobile No. | Identification — **excluded** |
| Room No. | Room analysis |
| Purpose | Purpose analysis |
| Check-in | Duration analysis |
| Check-out | Duration analysis |

**Privacy note:** personal identifiers are dropped at load time in the dashboard
and are excluded from every chart, table and export in this report.

---

## 5. Data Cleaning Methodology

- Standardise room labels to `Room 1 … Room 7`; preserve 2 missing values as `Missing / unclear`.
- Standardise known purpose labels; preserve 22 missing/unclear purposes.
- Parse timestamps and time fields where possible (`errors="coerce"`).
- Derive `year`, `month`, `weekday`, `submission hour`.
- Calculate same-day duration in minutes.
- **Validity rule:** a duration is valid if it falls within `0 – 720 minutes` (0–12 h inclusive).
- **Flag, do not silently fix** records with negative durations or durations > 12 h,
  since the source does not provide enough evidence to correct AM/PM reliably.
- Keep raw and processed data separate (`data/raw/` vs `data/processed/`).

---

## 6. Data Quality Summary

| Indicator | Count |
|---|---|
| Total records | **1,747** |
| Missing room | 2 |
| Missing / unclear purpose | 22 |
| Missing time | 2 |
| Exact duplicate rows | 0 |
| Negative duration | 257 |
| Duration > 12 h | 30 |
| Missing / unparseable duration | 2 |
| **Valid duration records** | **1,458** |

**Note on the count:** the mid-review deck quotes 1,457; the cleaned CSV gives
**1,458** under the 0–720-minute rule (0 is inclusive; 720 is inclusive). This
report uses **1,458** and records the discrepancy for transparency.

**Completeness:** timestamp 100%, room 99.9%, purpose 98.7%, duration 83.5%.

---

## 7. Analysis and Findings

### 7.1 Room Usage

| Room | Bookings |
|---|---|
| Room 1 | 188 |
| Room 2 | 192 |
| Room 3 | 283 |
| Room 4 | 274 |
| Room 5 | 273 |
| Room 6 | 246 |
| Room 7 | **289** |

Room 7 has the highest recorded booking count (289); Rooms 1 and 2 lag
(188 and 192), about a quarter below the equal-share benchmark of **249**.
Room 7 receives roughly **1.5×** the bookings of Room 1.

> This is **reservation volume**, not verified physical occupancy. Room capacity,
> availability and booking opportunity are not in the data.

### 7.2 Purpose Usage

| Purpose | Bookings | Share |
|---|---|---|
| Group Discussion | 711 | 40.7% |
| Self-study | 550 | 31.5% |
| Assignments | 273 | 15.6% |
| Micro-teaching | 130 | 7.4% |
| Project works | 34 | 1.9% |
| Mentoring | 27 | 1.5% |
| Missing / unclear | 22 | 1.3% |

Group Discussion and Self-study together account for **72%** of bookings. Nearly
a third of bookings are for **working alone** — quiet individual study space
could free discussion rooms for groups.

### 7.3 Yearly Activity

| Year | Bookings |
|---|---|
| 2023 | 275 |
| 2024 | 990 |
| 2025 | 482 |

2023 and 2025 are **partial years**; year totals are not directly comparable
without calendar context.

### 7.4 Monthly Activity

Peaks in **May 2024 (256)** and **March 2025 (288)**; near-zero months
(Dec, Jan, Feb, Jul) coincide with academic breaks. The trend is best read
alongside the academic calendar (not in the data).

### 7.5 Weekday Activity

| Weekday | Bookings |
|---|---|
| Monday | 309 |
| Tuesday | 328 |
| Wednesday | 308 |
| Thursday | 351 |
| Friday | 356 |
| Saturday | 95 |
| Sunday | 0 |

Weekdays are broadly even; Saturday is quiet (5.4%); Sunday has no bookings.

### 7.6 Duration Analysis

- Valid records: **1,458** (83.5%).
- Average valid duration: **153.85 minutes (2.56 h)**.
- Median: **120 minutes**. The mean is pulled up by a small number of long bookings.
- Shortest valid: **10 minutes**; longest valid: **718 minutes (11 h 58 min)**.

Flagged (not corrected): 257 negative durations and 30 durations > 12 h —
consistent with AM/PM entry errors.

### 7.7 Hypothesis Testing (α = 0.05)

**H1 — Equal room distribution**
- H₀: bookings are equally distributed across the 7 rooms.
- H₁: bookings are not equally distributed.
- Test: Chi-square goodness-of-fit.
- Result: χ² = **43.87**, df = 6, p ≈ **7.9 × 10⁻⁸**.
- **Decision: reject H₀.** Effect size (Cohen's w) ≈ **0.16** — small but clear.
- Caveat: equal share is a *benchmark*, not necessarily a fair operational target.

**H2 — Room × purpose association**
- H₀: room and purpose are independent.
- H₁: they are associated.
- Test: Chi-square test of independence.
- Result: χ² = **225.08**, df = 42, p ≈ **7.1 × 10⁻²⁷**, **Cramér's V = 0.15**.
- **Decision: reject H₀.** Association is statistically significant but **very weak**.
- Caveat: 42.9% of expected cells < 5 — the p-value is fragile with rare purposes.
  Combine rare purposes or collect more data before relying on this p-value.

**Interpretation:** tests show *differences and associations*, not causes. A
significant association between room and purpose does not mean the room *causes*
the purpose — a plausible alternative is scheduling or room-characteristics
matching.

---

## 8. Dashboard Design

Built with **Streamlit + Plotly**, privacy-safe by design.

**Structure (tabs):**
1. **Overview** — 5 KPI cards, room bar chart with equal-share line, purpose bar chart, "72% group/self-study" insight.
2. **Time patterns** — monthly line chart, weekday bar, submission-hour bar.
3. **Rooms × purposes** — heatmap + row-percentage table.
4. **Data quality** — completeness progress bars, flagged-record table, recommendations for future data collection.
5. **Hypothesis tests** — H1 and H2 recomputed live on filtered data with warnings when expected counts are low.
6. **Data & download** — de-identified filtered records + CSV export.

**Global features:**
- Sidebar filters for **year, month, room, purpose, weekday** (multi-select, live).
- Empty-state guard when filters return zero records.
- Privacy banner: personal identifiers dropped at load.
- Information banner when duration-flagged records are in view.

---

## 9. Technology Stack

| Technology | Role |
|---|---|
| Python | Programming language |
| Pandas | Cleaning, feature engineering, analysis |
| NumPy | Expected-count vector, effect-size calculation |
| SciPy | Chi-square goodness-of-fit and independence |
| Streamlit | Dashboard interface |
| Plotly | Interactive visualisations |
| CSV | Processed data storage |

---

## 10. Project Structure
