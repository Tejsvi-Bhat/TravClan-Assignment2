-- =============================================================
-- Section 3 — SQL queries, written against the normalized schema
-- in schema.sql. Verified on SQLite via run_sql.py.
-- =============================================================

-- -------------------------------------------------------------
-- B-Q1: For each property type, the room type with the most
-- Completed bookings, ranked with DENSE_RANK().
-- Why DENSE_RANK vs RANK / ROW_NUMBER:
--   ROW_NUMBER would pick an arbitrary single winner and hide a genuine tie;
--   RANK would leave gaps after a tie. DENSE_RANK keeps *all* tied top room
--   types (=1) with no gap, which is exactly "the most-booked room type(s)".
-- -------------------------------------------------------------
WITH counts AS (
    SELECT
        p.property_type,
        b.room_type,
        COUNT(*) AS booking_count
    FROM bookings b
    JOIN properties p ON p.property_id = b.property_id
    WHERE b.booking_status = 'Completed'
    GROUP BY p.property_type, b.room_type
),
ranked AS (
    SELECT
        property_type,
        room_type,
        booking_count,
        DENSE_RANK() OVER (
            PARTITION BY property_type
            ORDER BY booking_count DESC
        ) AS rnk
    FROM counts
)
SELECT property_type, room_type, booking_count
FROM ranked
WHERE rnk = 1
ORDER BY property_type;


-- -------------------------------------------------------------
-- B-Q2: Monthly realized revenue for 2024 (Completed only,
-- Footnote 8) with a running cumulative total.
-- Month is taken from checkin_date (all check-ins fall in 2024).
-- -------------------------------------------------------------
WITH monthly AS (
    SELECT
        strftime('%Y-%m', checkin_date) AS month,
        SUM(total_amount)               AS monthly_revenue
    FROM bookings
    WHERE booking_status = 'Completed'
      AND strftime('%Y', checkin_date) = '2024'
    GROUP BY strftime('%Y-%m', checkin_date)
)
SELECT
    month,
    monthly_revenue,
    SUM(monthly_revenue) OVER (ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM monthly
ORDER BY month;
