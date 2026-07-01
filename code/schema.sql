-- =============================================================
-- Section 3 — Normalized schema for the hotel-booking dataset.
-- The flat CSV denormalizes customer + property attributes into
-- every row; we split them into their own tables keyed by id.
-- Money -> DECIMAL(12,2); free text -> bounded VARCHAR; dates -> DATE.
-- =============================================================

CREATE TABLE customers (
    customer_id        INTEGER      PRIMARY KEY,
    customer_name      VARCHAR(100) NOT NULL,
    customer_segment   VARCHAR(20)  NOT NULL,          -- Individual / Corporate / Group
    signup_date        DATE         NOT NULL,
    home_city          VARCHAR(60)  NOT NULL,
    -- Footnote 7: 'None' is a real tier value, not NULL. NOT NULL enforces that
    -- and the CHECK pins the domain to the 4 legal strings.
    loyalty_tier       VARCHAR(10)  NOT NULL,
    CHECK (loyalty_tier IN ('None', 'Silver', 'Gold', 'Platinum'))
);

CREATE TABLE properties (
    property_id        INTEGER      PRIMARY KEY,
    property_name      VARCHAR(120) NOT NULL,
    property_city      VARCHAR(60)  NOT NULL,
    star_rating        SMALLINT     NOT NULL CHECK (star_rating BETWEEN 1 AND 5),
    property_type      VARCHAR(20)  NOT NULL,          -- Budget / Mid-Range / Premium / Luxury
    total_rooms        INTEGER      NOT NULL CHECK (total_rooms > 0),
    -- Footnote 4: the same property_name legitimately repeats across cities with
    -- different ids, so name alone is NOT unique — but (name, city) is. This
    -- constraint documents that names must never be used as a grouping key.
    UNIQUE (property_name, property_city)
);

CREATE TABLE bookings (
    booking_id         INTEGER      PRIMARY KEY,
    customer_id        INTEGER      NOT NULL REFERENCES customers(customer_id),
    property_id        INTEGER      NOT NULL REFERENCES properties(property_id),
    booking_date       DATE         NOT NULL,
    checkin_date       DATE         NOT NULL,
    checkout_date      DATE         NOT NULL,
    room_type          VARCHAR(20)  NOT NULL,          -- Standard / Deluxe / Suite
    num_rooms          INTEGER      NOT NULL,
    nights             INTEGER      NOT NULL,
    booking_channel    VARCHAR(20)  NOT NULL,
    adr                DECIMAL(10,2) NOT NULL,          -- average daily rate
    discount_amount    DECIMAL(12,2) NOT NULL DEFAULT 0,
    coupon_code        VARCHAR(20),                     -- NULL / 'NONE' both mean no coupon
    total_amount       DECIMAL(12,2) NOT NULL,
    payment_method     VARCHAR(20)  NOT NULL,
    booking_status     VARCHAR(12)  NOT NULL
                       CHECK (booking_status IN ('Completed','Cancelled','No-Show')),
    -- Footnote 1: an invalid stay (checkout on/before check-in) is a data error.
    CHECK (checkout_date > checkin_date),
    -- Footnote 3: zero-room bookings are erroneous.
    CHECK (num_rooms > 0)
);

CREATE TABLE reviews (
    booking_id         INTEGER      PRIMARY KEY REFERENCES bookings(booking_id),
    review_rating      DECIMAL(3,1) NOT NULL,           -- raw scale (5 or 10 by segment, Footnote 6)
    review_date        DATE
);

-- -------------------------------------------------------------
-- Index to speed up the queries below.
-- B-Q1 filters status='Completed' then groups by property_type/room_type
-- (property_type lives on properties, reached via bookings.property_id);
-- B-Q2 filters status='Completed' and buckets by checkin month. Both scans
-- start from "Completed" bookings, so a composite index on the status +
-- the join/date keys lets the engine seek instead of full-scanning bookings.
-- -------------------------------------------------------------
CREATE INDEX ix_bookings_status_prop_checkin
    ON bookings (booking_status, property_id, checkin_date);
