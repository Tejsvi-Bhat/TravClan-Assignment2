# Requirement Status

Checklist mirroring `requirementsSpec.md`. Each box is ticked when the requirement is
met, with a short note on *how* / *where* it is satisfied. All numbers are produced live
by the scripts in `code/` and `project/` — nothing is hard-coded.

---

## Footnotes handled (baseline for everything)

- [x] **F1 — invalid stays** (checkout ≤ check-in): flagged `bad_stay`, excluded from analysis.
  → `code/clean.py::add_flags/analysable`; 120 rows; also enforced by `CHECK(checkout_date > checkin_date)`.
- [x] **F2 — booking before signup**: flagged `booking_before_signup` (163 rows). → `clean.py`.
- [x] **F3 — zero rooms**: flagged `zero_rooms` (60 rows), excluded from analysis + `CHECK(num_rooms > 0)`.
- [x] **F4 — property names repeat across cities**: never group on name; use `property_id`.
  → S1-B1 output; `UNIQUE(property_name, property_city)` in `schema.sql`.
- [x] **F5 — reviews on Cancelled**: flagged `review_on_cancelled` (50 rows), not loaded into `reviews`.
- [x] **F6 — review scale mismatch**: `review_rating_norm` halves Corporate (1-10) to 1-5. → `clean.py`.
- [x] **F7 — loyalty tier 'None' parse trap**: `read_csv(keep_default_na=False)` keeps the literal
  `'None'` (5,571 rows / 46%). → `clean.py::load_raw`.
- [x] **F8 — realized vs booked revenue**: all revenue uses `booking_status = 'Completed'` only.

---

## Section 1 — Data Quality

- [x] **B1 — property names in >1 city (different ids), listed.**
  → 4 found: The Grand Plaza (Bangalore 2 / Kochi 1), Sea Breeze Resort (Chennai 3 / Goa 4),
  Hilltop Inn (Chennai 5 / Udaipur 6), Royal Orchid (Chennai 7 / Goa 8). `code/analysis.py::section1`.
- [x] **B2 — two 'no coupon' encodings + real-coupon %.**
  → `'NONE'` (3,978) and empty string `''` (3,894); real coupons = 4,128/12,000 = **34.4%**.
- [x] **B3 — count reviews on Cancelled + why impossible + one rule.**
  → **50**; a cancelled stay was never fulfilled so nothing can be rated; rule = null the
  review fields and exclude from rating aggregates (done in `run_sql.py` before loading `reviews`).

---

## Section 2 — Case Study: Discount Erosion

- [x] **B1 — discount intensity per channel + labelled chart + platform intensity + most-above channel & gap.**
  → Chart `answers/figures/q1_discount_intensity.png`; platform = **5.31%**;
  **OTA = 7.29%, +1.98 pp** above average (next channels all below avg).
- [x] **B2 — customer mix of focus channel vs platform (segment, tier w/ F7, source-city); who vs channel.**
  → Mix tables in `answers.pdf`; tier mix ~identical (±2 pp), travel pattern identical, only a mild
  Individual tilt → concluded it's the **channel's pricing**, not a different customer base.
- [x] **B3 — coupon vs no-coupon on focus channel: cancel rate + per-room + labelled chart + verdict.**
  → Chart `figures/q3_coupon_behaviour.png`; cancel 21.82% vs 22.04% (flat), per-room ₹20,093 vs
  ₹23,125 (worse). Verdict: **identical-to-worse behaviour → margin leakage.**
- [x] **B4 — specific pullback strategy + ₹ margin recovery + one leading indicator + abort threshold.**
  → Retire `APPDEAL`/`FEST15`/`SAVE10` on OTA, keep `WELCOME` for new accounts; recover ≈ **₹6.06 M**
  (of ₹7.72 M realized OTA coupon discount); indicator = **OTA weekly Completed volume**;
  abort if it drops **>8% vs 4-week baseline for 2 consecutive weeks**.
- [x] **≥2 labelled visualizations (Q1 + Q3).** → both embedded in `answers.pdf`.
- [x] **Every conclusion backed by specific numbers.** → yes throughout.

---

## Section 3 — SQL Challenge

- [x] **≥3 tables via CREATE TABLE (customers, properties, bookings, +reviews).** → `code/schema.sql` (4 tables).
- [x] **Per column: SQL type (money precision, text length), PK/FK/neither + NOT NULL.**
  → money `DECIMAL(12,2)`, bounded `VARCHAR(n)`, `DATE`; PKs/FKs and NOT NULLs specified.
- [x] **One non-trivial CHECK/UNIQUE addressing a footnote.**
  → `UNIQUE(property_name, property_city)` (F4), `CHECK(checkout_date > checkin_date)` (F1),
  `CHECK(num_rooms > 0)` (F3), tier `CHECK IN (...)` (F7).
- [x] **One indexed column + 1-2 line justification.**
  → `ix_bookings_status_prop_checkin (booking_status, property_id, checkin_date)`; both queries filter
  `Completed` then join by property / bucket by check-in month, so the composite index avoids a full scan.
- [x] **State schema vs flat CSV.** → queries run against the **normalized schema** (`run_sql.py` loads it).
- [x] **B-Q1 — room type with most Completed bookings per property type via DENSE_RANK + why DENSE_RANK.**
  → `queries.sql`; result: Standard tops every type; DENSE_RANK keeps ties at rank 1 with no gap
  (unlike ROW_NUMBER which drops ties, or RANK which leaves gaps).
- [x] **B-Q2 — monthly 2024 realized revenue + running cumulative via SUM() OVER + report full-year total.**
  → `queries.sql`; **full-year cumulative = ₹292,196,106.23**.
- [x] **Queries verified to run.** → `code/run_sql.py` executes both against SQLite.

---

## Section 4 — Mini-Project (Set B: Holiday-Proximity Demand Tagger)

- [x] **Real call to the assigned free API with error handling (timeouts/missing data don't crash).**
  → `project/holiday_tagger.py::fetch_holidays`: `requests.get(..., timeout=10)`, handles the real
  **HTTP 204** (Nager has no India data), timeouts, and network errors → bundled-calendar fallback.
- [x] **Correct merge of API data onto bookings (join keys/dates).**
  → `merge_asof(direction="nearest", tolerance=±2 days)` on `checkin_date` → holiday `date`.
- [x] **Tag ±2 days of a public holiday; compare value, length of stay, cancellation rate; quantify lift.**
  → 20.3% tagged holiday-adjacent; value **−4.2%** (₹30,704 vs ₹32,033), nights flat (2.87 vs 2.85),
  cancel **+1.71 pp** (20.5% vs 18.8%).
- [x] **One non-obvious quantified insight (3-4 sentences).** → in `project/README.md` (no long-weekend premium).
- [x] **6-line README (what/run/design decision/limitation).** → `project/README.md`.
- [x] **AI-usage note (≤8 lines, specific fixes).** → `project/README.md` "Where I used AI (and what I fixed)".

---

## Deliverables & Packaging

- [x] **Single ZIP.** → `submission.zip`.
- [x] **answers.pdf — CREATE TABLEs + index justification, SQL as text, case study + embedded visuals.**
  → `answers/answers.pdf` (5 pages, both charts embedded).
- [x] **code/ folder — analysis script + SQL files.** → `clean.py`, `analysis.py`, `schema.sql`, `queries.sql`, `run_sql.py`.
- [x] **project/ folder — mini-project code + README + insight + AI note.** → `project/`.
