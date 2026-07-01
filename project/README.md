# Holiday-Proximity Demand Tagger

**What it does:** Pulls the 2024 India public-holiday calendar from the free Nager.Date API and tags every booking whose check-in date is within ±2 days of a holiday, then compares value, length of stay and cancellation rate against ordinary bookings.
**How to run:** `python project/holiday_tagger.py` (needs `pandas`, `requests`; writes `holiday_value.png`). Reuses the footnote-aware cleaning in `code/clean.py`.
**Design decision:** Tagging uses `pandas.merge_asof(direction="nearest", tolerance=2 days)` — an O(n log n) tolerance join to the closest holiday, instead of an n×15 cross join.
**Limitation:** The assigned endpoint (`/2024/IN`) returns HTTP 204 (Nager has no India data), so the ±2-day window relies on a bundled 15-holiday national calendar; regional/state holidays that also drive travel are not captured.

## Quantified insight
Holiday-adjacent bookings are **not** the premium long-weekend demand you'd assume. Of 11,821 valid bookings, 20.3% (2,398) fall within ±2 days of a national holiday, yet their average completed value is ₹30,704 vs ₹32,033 for ordinary bookings — a **4.2% discount, not a premium** — while length of stay is flat (2.87 vs 2.85 nights). Worse, their cancellation rate is **1.71pp higher** (20.5% vs 18.8%). The dataset alone can't say this without the external holiday calendar; the actionable read is that holiday windows bring slightly cheaper, flakier bookings, so surge-pricing or tighter cancellation terms around holidays are unjustified here.

## Where I used AI (and what I fixed)
- AI scaffolded the `requests` fetch and the `merge_asof` tagging; I kept the structure.
- AI's first version assumed `/2024/IN` returned JSON and crashed on the real **HTTP 204** — I added the 204/empty-body branch and the bundled-calendar fallback so the run never dies.
- AI initially did a cross join + date-diff filter; I replaced it with a tolerance `merge_asof` for speed and correctness at ±2 days.
- AI computed avg value over all rows; I restricted it to `Completed` bookings (Footnote 8) so cancelled would-have-been amounts don't inflate the number.
