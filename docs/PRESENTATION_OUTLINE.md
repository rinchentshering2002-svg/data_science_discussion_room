# Final Presentation Outline
## Discussion Room Booking Analytics — PRG405

Target length: **12–15 slides / 12–15 minutes**.

---

### Slide 1 — Title
- **On slide:** Title, module, team, dataset period, 1,747 records, 7 rooms, 6 purposes.
- **Speak:** "We analysed 1,747 discussion-room booking records spanning 20 months and delivered an interactive dashboard."

### Slide 2 — Problem, aim, objectives
- **On slide:** PDF source, inconsistent fields, AM/PM errors, no capacity data.
- **Speak:** "The source was a PDF export. Our job was to turn it into a reproducible, privacy-safe analysis and dashboard."

### Slide 3 — Data and cleaning
- **On slide:** Source field → analytical use; privacy column showing identifiers dropped.
- **Demo:** Show `data/raw/` PDF next to `data/processed/` CSV.
- **Speak:** "Personal identifiers — name, ID, mobile — are dropped at load time."

### Slide 4 — Data quality
- **On slide:** Completeness bars (100% / 99.9% / 98.7% / 83.5%), flagged counts, 1,457 vs 1,458 note.
- **Demo:** Data quality tab.
- **Speak:** "Counts are reliable; durations are less so. We flag, not correct."

### Slide 5 — Overview: rooms and purposes
- **On slide:** Room bar chart with equal-share line (249); purpose bar chart; 72% callout.
- **Demo:** Overview tab.
- **Speak:** "Room 7 leads; Rooms 1 and 2 trail. 72% is group + self-study."

### Slide 6 — H1 result
- **On slide:** χ² = 43.87, df = 6, p < 0.001, Cohen's w ≈ 0.16, reject H₀.
- **Demo:** Hypothesis tab; change a filter to show recompute.
- **Speak:** "Significant, small effect. Equal share is a benchmark."

### Slide 7 — H2 result
- **On slide:** χ² = 225.08, Cramér's V = 0.15, 42.9% expected cells < 5.
- **Demo:** Rooms × purposes heatmap.
- **Speak:** "Significant but very weak; fragile p-value."

### Slide 8 — Time patterns
- **On slide:** Monthly peaks/quiet months; weekdays even; 1 pm submission peak.
- **Demo:** Time patterns tab.
- **Speak:** "Bursty by month; weekdays even; submission peak is not use peak."

### Slide 9 — Duration validity
- **On slide:** 1,458 / 257 / 30; mean 154, median 120, range 10–718.
- **Demo:** Amber info banner on filtered view.
- **Speak:** "AM/PM errors — reported, not corrected."

### Slide 10 — Dashboard walkthrough
- **Demo:** Click all six tabs, change two filters, show CSV download.
- **Speak:** "Privacy-safe, filters live, recomputes tests, exports de-identified CSV."

### Slide 11 — Limitations and recommendations
- **On slide:** 6 limitations; recommendations grouped as data collection and operations.
- **Speak:** "Structured collection + consider quiet individual study."

### Slide 12 — Conclusion and Q&A
- **On slide:** 3 one-line conclusions.
- **Speak:** "Thank you — questions welcome."

---

## Q&A — prepared answers

**Q: Why 1,458 and not 1,457?** A: Rule inclusive on both ends; CSV yields 1,458.
**Q: Couldn't you fix AM/PM?** A: That would be guessing. We flag.
**Q: Is unequal demand a problem?** A: Only if it reflects one. Equal share is a statistical benchmark.
**Q: Why reject H₀ if V = 0.15?** A: p answers "is there an association?", V answers "how big?". Large n makes small effects significant.
**Q: Where is NumPy used?** A: Expected-count vector, Cohen's w, Cramér's V, duration summaries.