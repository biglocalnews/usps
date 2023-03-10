-- Create a table to store all the final addresses.
CREATE TABLE IF NOT EXISTS address (
    hash varchar PRIMARY KEY not null,
    point geometry not null,
    statefp varchar(2),
    countyfp varchar(3),
    tract_id varchar(11),
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
CREATE INDEX IF NOT EXISTS addr_tractid_idx ON address (tract_id);
-- Add a spatial index on all the points.
CREATE INDEX IF NOT EXISTS addr_gist_idx ON address USING GIST (point);

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
ALTER TABLE __TBL__ ALTER COLUMN tract_id SET NOT NULL;
ALTER TABLE __TBL__ INHERIT address;

COMMIT;

-- Create indexes based on the parent table's indexes.
CREATE INDEX IF NOT EXISTS __TBL___tractid_idx ON __TBL__ (tract_id);
CREATE INDEX IF NOT EXISTS __TBL___gist_idx ON __TBL__ USING GIST (point);

-- Sort the physical rows of the table to make the index more effective.
CLUSTER __TBL__ USING __TBL___gist_idx;
