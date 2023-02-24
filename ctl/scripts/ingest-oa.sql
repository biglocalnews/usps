-- Create a table to store all the final addresses.
CREATE TABLE IF NOT EXISTS address (
    hash varchar(255) PRIMARY KEY not null,
    addr varchar(1023) not null,
    point geometry not null,
    statefp varchar(2),
    countyfp varchar(3),
    tractce varchar(6),
    blkgrpce varchar(1)
);

-- Create indexes for fast querying.
-- FIPS indexes can narrow down the search space faster than spatial indexes.
CREATE INDEX IF NOT EXISTS addr_fps_idx ON address (statefp, countyfp);
-- Add a spatial index on all the points.
CREATE INDEX IF NOT EXISTS addr_pt_idx ON address USING SPGIST (point);

-- Ingest data from the staging table to the final table.
-- NOTE(s):
--  1. The point geometry is transformed to SRID 4269 to match TIGER data.
--  2. The pagc_normalize_address function has performance problems, so we are
--     using the workaround described here:
--     http://postgis.net/docs/manual-dev/Pagc_Normalize_Address.html
--  3. We join blockgroup info to enrich the downloads
--  4. Tables are inherited from the main `address` table so that it's easier
--     to modularize the database.
DROP TABLE IF EXISTS __TBL__;
CREATE TABLE __TBL__() INHERITS (address);

-- Try to stay true to the implementation of the pagc_normalizer:
-- https://github.com/postgis/postgis/blob/f6def67654c25d812446239036cee44812613748/extras/tiger_geocoder/pagc_normalize/pagc_normalize_address.sql#L34
-- Note that the example given in the TIGER documentation about how to improve
-- performance doesn't currently work!
WITH oas AS (
    SELECT
        hash,
        point,
        ROW(
            to_number(substring((sa).house_num, '[0-9]+'), '99999999'),
            (sa).predir,
            (sa).name,
            (sa).suftype,
            (sa).sufdir,
            (sa).unit,
            (sa).city,
            (sa).state,
            (sa).postcode,
            true,
            NULL,
            (sa).house_num
        )::norm_addy AS na
    FROM (
        SELECT
            hash,
            St_Transform(wkb_geometry, 4269) AS point,
            standardize_address(
                'tiger.pagc_lex',
                'tiger.pagc_gaz',
                'tiger.pagc_rules',
                number || ','
                || street || ','
                || unit || ','
                || city || ','
                || region || ','
                || coalesce(postcode, '')
            ) AS sa
            FROM __STAGE__
        ) g
    )
INSERT INTO __TBL__ (hash, addr, point, statefp, countyfp, tractce, blkgrpce)
SELECT
    a.hash,
    pprint_addy(a.na) AS addr,
    a.point,
    b.statefp,
    b.countyfp,
    b.tractce,
    b.blkgrpce
FROM oas a
LEFT JOIN bg b
ON ST_Contains(b.the_geom, a.point)
;

COMMIT;

-- Create indexes based on the parent table's indexes.
CREATE INDEX IF NOT EXISTS __TBL___fps_idx ON address (statefp, countyfp);
CREATE INDEX IF NOT EXISTS __TBL___idx ON address USING SPGIST (point);
