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
-- Create tract index.
CREATE INDEX IF NOT EXISTS addr_tract_idx ON address (tractce);
-- Add a spatial index on all the points.
CREATE INDEX IF NOT EXISTS addr_pt_idx ON address USING SPGIST (point);

-- Set up the final table.
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
CREATE INDEX IF NOT EXISTS __TBL___tract_idx ON __TBL__ (tractce);
CREATE INDEX IF NOT EXISTS __TBL___idx ON __TBL__ USING SPGIST (point);
