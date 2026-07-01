"""
Shared loading + cleaning for the hotel_bookings dataset.

Every footnote in the spec is handled here in one place so Sections 1-4 all
operate on a consistently-flagged frame. Nothing is silently dropped: rows are
*flagged* and helper views expose the valid subset, so the data-quality section
can still count the bad rows.
"""
from pathlib import Path
import pandas as pd

CSV_PATH = Path(__file__).resolve().parent.parent / "hotel_bookings.csv"

# The two literal strings that both mean "no coupon" (Footnote 2 / Section 1 B2).
NO_COUPON = {"NONE", ""}

DATE_COLS = [
    "customer_signup_date", "booking_date",
    "checkin_date", "checkout_date", "review_date",
]


def load_raw() -> pd.DataFrame:
    """Load the CSV without letting the reader mangle the data.

    Footnote 7: keep_default_na=False stops pandas turning the literal loyalty
    tier 'None' into NaN (that alone hides ~46% of the tier column). We then
    re-introduce NaN only for the columns where empty genuinely means missing.
    """
    df = pd.read_csv(CSV_PATH, keep_default_na=False, dtype=str)

    # numeric columns
    for col in ["property_star_rating", "property_total_rooms", "num_rooms", "nights"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["adr", "discount_amount", "total_amount", "review_rating"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # dates (empty string -> NaT)
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col].replace("", pd.NA), errors="coerce")

    return df


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add boolean data-quality flags, one per footnote."""
    df = df.copy()

    # Footnote 1: checkout on/before check-in.
    df["bad_stay"] = df["checkout_date"] <= df["checkin_date"]

    # Footnote 2: booking recorded before the account existed.
    df["booking_before_signup"] = df["booking_date"] < df["customer_signup_date"]

    # Footnote 3: zero-room bookings (carry total_amount = 0).
    df["zero_rooms"] = df["num_rooms"] == 0

    # Footnote 5: a review on a Cancelled booking is impossible.
    df["review_on_cancelled"] = (
        (df["booking_status"] == "Cancelled") & df["review_rating"].notna()
    )

    # coupon usage (Footnote for Section 1 B2)
    df["has_coupon"] = ~df["coupon_code"].isin(NO_COUPON)

    # gross revenue = what was charged before the discount was applied.
    df["gross_amount"] = df["total_amount"] + df["discount_amount"]

    # Footnote 6: normalise review rating to a 1-5 scale. Corporate customers
    # are rated 1-10, everyone else 1-5, so halve the corporate ratings.
    df["review_rating_norm"] = df["review_rating"].where(
        df["customer_segment"] != "Corporate", df["review_rating"] / 2.0
    )

    return df


def analysable(df: pd.DataFrame) -> pd.DataFrame:
    """Rows safe for behavioural / revenue analysis: drop structural errors
    (bad stays, zero-room rows). Status filtering is left to the caller because
    'realized revenue' (Footnote 8) only applies to some questions."""
    return df[~df["bad_stay"] & ~df["zero_rooms"]].copy()


def load() -> pd.DataFrame:
    return add_flags(load_raw())


if __name__ == "__main__":
    d = load()
    print(d.shape)
    print(d[["bad_stay", "booking_before_signup", "zero_rooms",
             "review_on_cancelled", "has_coupon"]].sum())
