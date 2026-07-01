"""
Holiday-Proximity Demand Tagger  (Section 4, Set B)
===================================================

Pulls the 2024 India public-holiday calendar from the free, no-key Nager.Date
API and tags every booking as "holiday-adjacent" when its check-in date falls
within +/-2 days of a public holiday. It then compares booking value, length of
stay and cancellation rate for holiday-adjacent vs ordinary bookings.

Run:  python project/holiday_tagger.py
Deps: pandas, requests   (matplotlib optional, for the chart)

Note on the data source: the assigned endpoint (.../2024/IN) currently returns
HTTP 204 No Content — Nager.Date has no India calendar. The client handles that
(and timeouts / network errors) gracefully and falls back to a bundled list of
India's 2024 gazetted national holidays so the run never crashes. See README.
"""
from __future__ import annotations
import sys
from pathlib import Path
import requests
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))
import clean  # noqa: E402

API_URL = "https://date.nager.at/api/v3/PublicHolidays/2024/IN"
WINDOW_DAYS = 2

# Fallback: India's 2024 gazetted national public holidays (used only if the
# live API returns no usable data). Sourced from the standard GoI holiday list.
FALLBACK_HOLIDAYS_2024 = [
    ("2024-01-26", "Republic Day"),
    ("2024-03-08", "Maha Shivaratri"),
    ("2024-03-25", "Holi"),
    ("2024-03-29", "Good Friday"),
    ("2024-04-11", "Eid ul-Fitr"),
    ("2024-04-17", "Ram Navami"),
    ("2024-05-23", "Buddha Purnima"),
    ("2024-06-17", "Eid ul-Adha"),
    ("2024-08-15", "Independence Day"),
    ("2024-08-26", "Janmashtami"),
    ("2024-10-02", "Gandhi Jayanti"),
    ("2024-10-12", "Dussehra"),
    ("2024-10-31", "Diwali"),
    ("2024-11-15", "Guru Nanak Jayanti"),
    ("2024-12-25", "Christmas Day"),
]


def fetch_holidays(url: str = API_URL) -> tuple[pd.DataFrame, str]:
    """Return (holidays_df, source). Never raises for network/timeout/empty:
    on any failure it falls back to the bundled calendar."""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 204 or not resp.text.strip():
            print(f"[warn] API returned no content ({resp.status_code}); "
                  f"using bundled India 2024 calendar.")
            raise ValueError("empty")
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError("empty payload")
        hol = pd.DataFrame(data)[["date", "localName"]].rename(
            columns={"localName": "holiday_name"})
        source = "live Nager.Date API"
    except (requests.RequestException, ValueError, KeyError) as exc:
        print(f"[info] live fetch unusable ({exc!r}); falling back to bundled list.")
        hol = pd.DataFrame(FALLBACK_HOLIDAYS_2024, columns=["date", "holiday_name"])
        source = "bundled fallback (India 2024 gazetted holidays)"
    hol["date"] = pd.to_datetime(hol["date"])
    return hol, source


def tag_bookings(bookings: pd.DataFrame, holidays: pd.DataFrame) -> pd.DataFrame:
    """Flag each booking whose check-in is within +/-WINDOW_DAYS of a holiday.

    Implemented as a tolerance merge_asof (nearest holiday to each check-in),
    then keep matches inside the window. This is O(n log n), not a cross join.
    """
    b = bookings.dropna(subset=["checkin_date"]).sort_values("checkin_date").copy()
    h = holidays.sort_values("date")
    merged = pd.merge_asof(
        b, h, left_on="checkin_date", right_on="date",
        direction="nearest", tolerance=pd.Timedelta(days=WINDOW_DAYS),
    )
    merged["holiday_adjacent"] = merged["date"].notna()
    return merged


def compare(tagged: pd.DataFrame) -> pd.DataFrame:
    """Booking value, length of stay, cancellation rate by adjacency."""
    def stats(sub: pd.DataFrame) -> dict:
        completed = sub[sub["booking_status"] == "Completed"]
        return {
            "bookings": len(sub),
            "avg_total_amount": completed["total_amount"].mean(),
            "avg_nights": sub["nights"].mean(),
            "cancel_rate_%": 100 * (sub["booking_status"] == "Cancelled").mean(),
        }

    out = pd.DataFrame({
        "holiday_adjacent": stats(tagged[tagged["holiday_adjacent"]]),
        "ordinary": stats(tagged[~tagged["holiday_adjacent"]]),
    }).T
    return out


def main():
    holidays, source = fetch_holidays()
    print(f"Loaded {len(holidays)} holidays from: {source}")

    df = clean.load()
    valid = clean.analysable(df)                 # honour Footnotes 1 & 3
    tagged = tag_bookings(valid, holidays)

    n_adj = int(tagged["holiday_adjacent"].sum())
    print(f"Tagged {n_adj:,}/{len(tagged):,} bookings as holiday-adjacent "
          f"({100*n_adj/len(tagged):.1f}%).")

    table = compare(tagged)
    pd.options.display.float_format = lambda v: f"{v:,.2f}"
    print("\n=== Holiday-adjacent vs ordinary ===")
    print(table.to_string())

    adj, ordn = table.loc["holiday_adjacent"], table.loc["ordinary"]
    val_lift = 100 * (adj["avg_total_amount"] / ordn["avg_total_amount"] - 1)
    print(f"\nValue lift (avg completed total): {val_lift:+.1f}%")
    print(f"Cancel-rate gap: {adj['cancel_rate_%'] - ordn['cancel_rate_%']:+.2f}pp")

    # optional chart
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        table["avg_total_amount"].plot.bar(ax=ax, color=["#c0392b", "#7f8c8d"])
        ax.set_ylabel("Avg completed booking value (Rs)")
        ax.set_title("Booking value: holiday-adjacent vs ordinary")
        ax.set_xticklabels(table.index, rotation=0)
        plt.tight_layout()
        out = Path(__file__).resolve().parent / "holiday_value.png"
        fig.savefig(out, dpi=130)
        print(f"[chart] wrote {out.name}")
    except Exception as exc:  # chart is a nice-to-have, never fatal
        print(f"[info] chart skipped: {exc!r}")


if __name__ == "__main__":
    main()
