# AI-Usage Note — Holiday-Proximity Demand Tagger

Where I used AI and what I had to fix in its output:

- AI scaffolded the `requests` fetch and the `merge_asof` tagging; I kept the structure.
- AI's first version assumed `/2024/IN` returned JSON and crashed on the real **HTTP 204** — I added the 204/empty-body branch and the bundled-calendar fallback so the run never dies.
- AI initially did a cross join + date-diff filter; I replaced it with a tolerance `merge_asof` for speed and correctness at ±2 days.
- AI computed avg value over all rows; I restricted it to `Completed` bookings (Footnote 8) so cancelled would-have-been amounts don't inflate the number.
