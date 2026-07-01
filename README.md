# Hotel Bookings Assessment — Submission

Answers to all four sections plus the mini-project.

## Layout
```
answers/
  answers.pdf          # Sections 1-3: DDL, SQL, case study + embedded charts
  figures/             # generated charts (Q1, Q3)
code/
  clean.py             # footnote-aware loading/cleaning (shared)
  analysis.py          # Sections 1 & 2 numbers + charts
  schema.sql           # normalized CREATE TABLEs
  queries.sql          # B-Q1 / B-Q2
  run_sql.py           # loads CSV into SQLite w/ schema, runs the queries
project/
  holiday_tagger.py    # Section 4 mini-project (Nager.Date API)
  README.md            # what/run/insight/AI-usage note
  holiday_value.png    # generated chart
hotel_bookings.csv
requirements.txt
```

## Setup & run
```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt

python code/analysis.py      # Sections 1 & 2 + charts
python code/run_sql.py       # Section 3 queries (SQLite)
python project/holiday_tagger.py   # Section 4
```

Every printed number is reproduced live from `hotel_bookings.csv`; nothing is hard-coded.
