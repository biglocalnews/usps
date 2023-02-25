-- Create a table to store all the final addresses.
CREATE TABLE IF NOT EXISTS address (
    hash varchar PRIMARY KEY not null,
    point geometry not null,
    statefp varchar(2),
    countyfp varchar(3),
    tractce varchar(6),
    blkgrpce varchar(1),
    unit varchar,
    number varchar,
    street varchar,
    city varchar,
    district varchar,
    region varchar,
    postcode varchar
);

-- Create indexes for fast querying.
-- FIPS indexes can narrow down the search space faster than spatial indexes.
CREATE INDEX IF NOT EXISTS addr_fps_idx ON address (statefp, countyfp);
-- Add a spatial index on all the points.
CREATE INDEX IF NOT EXISTS addr_pt_idx ON address USING SPGIST (point);

-- Ingest data from the staging table to the final table.
-- NOTE(s):
--  1. The pagc_normalize_address function has performance problems, so we are
--     using the workaround described here:
--     http://postgis.net/docs/manual-dev/Pagc_Normalize_Address.html
--  2. We join blockgroup info to enrich the downloads
--  3. Tables are inherited from the main `address` table so that it's easier
--     to modularize the database.
BEGIN;
DROP TABLE IF EXISTS __TBL__;
-- Note that we're not currently standardizing the addresses. This tends to
-- mess up the address more than just presenting the OA address does. Since
-- we've already filled in missing cities/zipcodes, the addresses should be
-- in fairly good shape by this point anyway!
-- (The address standardizer is also unbelievably slow!)
ALTER TABLE __STAGE__ RENAME TO __TBL__;
ALTER TABLE __TBL__ ALTER COLUMN hash SET NOT NULL;
ALTER TABLE __TBL__ ALTER COLUMN point SET NOT NULL;
ALTER TABLE __TBL__ INHERIT address;

COMMIT;

-- Create indexes based on the parent table's indexes.
CREATE INDEX IF NOT EXISTS __TBL___fps_idx ON __TBL__ (statefp, countyfp);
CREATE INDEX IF NOT EXISTS __TBL___idx ON __TBL__ USING SPGIST (point);
