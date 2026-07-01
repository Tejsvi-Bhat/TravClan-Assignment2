"""
Loads the CSV into an in-memory SQLite DB using the normalized schema in
schema.sql, then runs queries.sql. This proves both files actually work and
prints the answers used in answers.md.

Rows that violate the structural footnote constraints (Footnote 1 invalid stay,
Footnote 3 zero rooms) are dropped before load so the CHECK constraints hold —
that is the whole point of the constraints. Reviews on Cancelled bookings
(Footnote 5) are not inserted into reviews.

Run:  python code/run_sql.py
"""
import sqlite3
from pathlib import Path
import clean

HERE = Path(__file__).resolve().parent


def build_db() -> sqlite3.Connection:
    df = clean.load()
    valid = clean.analysable(df)            # drops bad_stay + zero_rooms

    conn = sqlite3.connect(":memory:")
    conn.executescript((HERE / "schema.sql").read_text())

    # customers (deduplicated)
    cust = (valid[["customer_id", "customer_name", "customer_segment",
                   "customer_signup_date", "customer_home_city",
                   "customer_loyalty_tier"]]
            .drop_duplicates("customer_id"))
    conn.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?)",
        [(int(r.customer_id), r.customer_name, r.customer_segment,
          r.customer_signup_date.date().isoformat(), r.customer_home_city,
          r.customer_loyalty_tier) for r in cust.itertuples()],
    )

    # properties (deduplicated on id)
    prop = (valid[["property_id", "property_name", "property_city",
                   "property_star_rating", "property_type",
                   "property_total_rooms"]]
            .drop_duplicates("property_id"))
    conn.executemany(
        "INSERT INTO properties VALUES (?,?,?,?,?,?)",
        [(int(r.property_id), r.property_name, r.property_city,
          int(r.property_star_rating), r.property_type,
          int(r.property_total_rooms)) for r in prop.itertuples()],
    )

    # bookings
    conn.executemany(
        """INSERT INTO bookings VALUES
           (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [(int(r.booking_id), int(r.customer_id), int(r.property_id),
          r.booking_date.date().isoformat(), r.checkin_date.date().isoformat(),
          r.checkout_date.date().isoformat(), r.room_type, int(r.num_rooms),
          int(r.nights), r.booking_channel, float(r.adr),
          float(r.discount_amount),
          (None if r.coupon_code in clean.NO_COUPON else r.coupon_code),
          float(r.total_amount), r.payment_method, r.booking_status)
         for r in valid.itertuples()],
    )

    # reviews: only legitimate ones (not on Cancelled, Footnote 5)
    rev = valid[valid["review_rating"].notna() & ~valid["review_on_cancelled"]]
    conn.executemany(
        "INSERT INTO reviews VALUES (?,?,?)",
        [(int(r.booking_id), float(r.review_rating),
          (r.review_date.date().isoformat() if not clean.pd.isna(r.review_date) else None))
         for r in rev.itertuples()],
    )
    conn.commit()
    return conn


def split_statements(sql: str):
    stmts, buf = [], []
    for line in sql.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.rstrip().endswith(";"):
            stmts.append("\n".join(buf))
            buf = []
    return [s for s in stmts if s.strip()]


def main():
    conn = build_db()
    cur = conn.cursor()
    print("loaded:",
          dict(customers=cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
               properties=cur.execute("SELECT COUNT(*) FROM properties").fetchone()[0],
               bookings=cur.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
               reviews=cur.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]))

    stmts = split_statements((HERE / "queries.sql").read_text())
    labels = ["B-Q1: top room type per property type",
              "B-Q2: 2024 monthly realized revenue + running total"]
    for label, stmt in zip(labels, stmts):
        print("\n==== " + label + " ====")
        cur.execute(stmt)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        print(" | ".join(cols))
        for row in rows:
            print(" | ".join(f"{v:,.2f}" if isinstance(v, float) else str(v) for v in row))
        if label.startswith("B-Q2"):
            print(f"Full-year cumulative = Rs {rows[-1][2]:,.2f}")


if __name__ == "__main__":
    main()
