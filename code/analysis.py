"""
Sections 1 & 2 analysis. Prints every number used in answers.md and writes the
two required case-study charts to answers/figures/.

Run:  python code/analysis.py
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import clean

FIG_DIR = Path(__file__).resolve().parent.parent / "answers" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

df = clean.load()
ana = clean.analysable(df)                       # valid rows (no bad stays / zero rooms)
completed = ana[ana["booking_status"] == "Completed"]   # Footnote 8: realized only

line = lambda: print("-" * 60)


def section1():
    print("\n#### SECTION 1 — DATA QUALITY ####")
    # B1: property_name in >1 city (different property_id)
    g = df.groupby("property_name").agg(
        cities=("property_city", "nunique"),
        ids=("property_id", "nunique"),
    )
    multi = g[g["cities"] > 1]
    print("B1 property names in >1 city:", list(multi.index))
    for name in multi.index:
        sub = df[df["property_name"] == name]
        pairs = sub[["property_city", "property_id"]].drop_duplicates().values.tolist()
        print(f"    {name}: {pairs}")

    # B2: two 'no coupon' encodings + real-coupon %
    n = len(df)
    real = int(df["has_coupon"].sum())
    print(f"B2 no-coupon encodings = 'NONE' and '' (empty). "
          f"Real coupon = {real}/{n} = {100*real/n:.1f}%")

    # B3: reviews on Cancelled bookings
    print(f"B3 reviews on Cancelled bookings = {int(df['review_on_cancelled'].sum())}")


def section2():
    print("\n#### SECTION 2 — DISCOUNT EROSION ####")

    # --- B1: discount intensity by channel (Completed only) ---
    grp = completed.groupby("booking_channel").agg(
        discount=("discount_amount", "sum"),
        gross=("gross_amount", "sum"),
    )
    grp["intensity"] = grp["discount"] / grp["gross"]
    platform = completed["discount_amount"].sum() / completed["gross_amount"].sum()
    grp = grp.sort_values("intensity", ascending=False)
    grp["gap_pp"] = (grp["intensity"] - platform) * 100
    print(f"Platform-wide intensity = {platform*100:.2f}%")
    print(grp[["intensity", "gap_pp"]].round(4).to_string())
    focus = grp.index[0]
    print(f"Focus channel = {focus} ({grp.loc[focus,'intensity']*100:.2f}%, "
          f"+{grp.loc[focus,'gap_pp']:.2f}pp vs platform)")

    # chart 1: discount intensity by channel
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#c0392b" if c == focus else "#7f8c8d" for c in grp.index]
    bars = ax.bar(grp.index, grp["intensity"] * 100, color=colors)
    ax.axhline(platform * 100, ls="--", color="#2c3e50",
               label=f"platform avg {platform*100:.2f}%")
    ax.set_ylabel("Discount intensity (%)")
    ax.set_title("Discount intensity by booking channel (Completed bookings)")
    ax.bar_label(bars, fmt="%.2f%%", padding=2)
    ax.legend()
    plt.xticks(rotation=15)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "q1_discount_intensity.png", dpi=130)
    plt.close(fig)

    # --- B2: customer mix, focus channel vs platform ---
    focus_all = ana[ana["booking_channel"] == focus]

    def mix(pop, col):
        return (pop[col].value_counts(normalize=True) * 100).round(1)

    for col in ["customer_segment", "customer_loyalty_tier"]:
        tbl = pd.concat({"focus": mix(focus_all, col),
                         "platform": mix(ana, col)}, axis=1).fillna(0)
        print(f"\nMix by {col} (%):\n{tbl.to_string()}")

    # source-city pattern: booker travelling out of home city
    def travel_share(pop):
        return 100 * (pop["customer_home_city"] != pop["property_city"]).mean()
    print(f"\nBooked outside home city: focus {travel_share(focus_all):.1f}% "
          f"vs platform {travel_share(ana):.1f}%")

    # --- B3: coupon vs no-coupon behaviour on the focus channel ---
    print(f"\n-- B3 coupon vs no-coupon on {focus} --")
    rows = []
    for label, sub in [("coupon", focus_all[focus_all["has_coupon"]]),
                       ("no-coupon", focus_all[~focus_all["has_coupon"]])]:
        n = len(sub)
        cancel = 100 * (sub["booking_status"] == "Cancelled").mean()
        comp = sub[(sub["booking_status"] == "Completed") & (sub["num_rooms"] > 0)]
        per_room = (comp["total_amount"] / comp["num_rooms"]).mean()
        rows.append((label, n, cancel, per_room))
        print(f"  {label:9s} n={n:5d}  cancel_rate={cancel:5.2f}%  "
              f"per_room=Rs{per_room:,.0f}")
    b3 = pd.DataFrame(rows, columns=["group", "n", "cancel_rate", "per_room"])

    # chart 2: coupon vs no-coupon on focus channel (twin metrics)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4))
    a1.bar(b3["group"], b3["cancel_rate"], color=["#c0392b", "#7f8c8d"])
    a1.set_title(f"{focus}: cancellation rate")
    a1.set_ylabel("Cancel rate (%)")
    for i, v in enumerate(b3["cancel_rate"]):
        a1.text(i, v + 0.2, f"{v:.2f}%", ha="center")
    a2.bar(b3["group"], b3["per_room"], color=["#c0392b", "#7f8c8d"])
    a2.set_title(f"{focus}: per-room amount (Completed)")
    a2.set_ylabel("Rs per room")
    for i, v in enumerate(b3["per_room"]):
        a2.text(i, v + 200, f"Rs{v:,.0f}", ha="center")
    fig.suptitle(f"Coupon vs no-coupon behaviour on {focus}")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "q3_coupon_behaviour.png", dpi=130)
    plt.close(fig)

    # --- B4: recoverable margin (realized OTA coupon discount) ---
    ota_coupon_completed = completed[(completed["booking_channel"] == focus)
                                     & completed["has_coupon"]]
    recover = ota_coupon_completed["discount_amount"].sum()
    ota_rev = completed[completed["booking_channel"] == focus]["total_amount"].sum()
    print(f"\n-- B4 --\n  {focus} coupon+Completed bookings = {len(ota_coupon_completed)}")
    print(f"  Recoverable discount (realized) = Rs {recover:,.0f} "
          f"({100*recover/ota_rev:.2f}% of {focus} realized revenue Rs {ota_rev:,.0f})")
    codes = (completed[(completed["booking_channel"] == focus) & completed["has_coupon"]]
             .groupby("coupon_code")["discount_amount"].agg(["count", "sum"]))
    print("  by coupon code:\n" + codes.round(0).to_string())


if __name__ == "__main__":
    section1()
    section2()
