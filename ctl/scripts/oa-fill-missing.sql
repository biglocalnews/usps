-- The following queries update missing information in the staging table.

BEGIN;

-- Transform point geometry to the projection used by TIGER.
ALTER TABLE oa_MY_STATE_staging ADD COLUMN point geometry;
UPDATE oa_MY_STATE_staging
SET
point = ST_Transform(wkb_geometry, 4269)
;

-- Fill in missing cities from places
CREATE TABLE oa_MY_STATE_staging_tmp1 AS (
    SELECT
        t.id,
        t.unit,
        t.number,
        t.street,
        g.name as city,
        t.district,
        t.region,
        t.postcode,
        t.hash,
        t.point
    FROM (
        SELECT *
        FROM oa_MY_STATE_staging
        WHERE nullif(city, '') IS NULL
    ) t
    LEFT JOIN
    tiger_data.MY_STATE_place g
    ON ST_Contains(g.the_geom, t.point)

    UNION ALL (
        SELECT
            id,
            unit,
            number,
            street,
            city,
            district,
            region,
            postcode,
            hash,
            point
        FROM oa_MY_STATE_staging
        WHERE nullif(city, '') IS NOT NULL
    )
)
;

-- Where cities are still missing, fill in from cousub.
CREATE TABLE oa_MY_STATE_staging_tmp2 AS (
    SELECT
        t.id,
        t.unit,
        t.number,
        t.street,
        g.name as city,
        t.district,
        t.region,
        t.postcode,
        t.hash,
        t.point
    FROM (
        SELECT *
        FROM oa_MY_STATE_staging_tmp1
        WHERE nullif(city, '') IS NULL
    ) t
    LEFT JOIN
    tiger_data.MY_STATE_cousub g
    ON ST_Contains(g.the_geom, t.point)

    UNION ALL (
        SELECT
            id,
            unit,
            number,
            street,
            city,
            district,
            region,
            postcode,
            hash,
            point
        FROM oa_MY_STATE_staging_tmp1
        WHERE nullif(city, '') IS NOT NULL
    )
)
;

-- Fill in postcode from ZCTA table.
CREATE TABLE oa_MY_STATE_staging_tmp3 AS (
    SELECT
        t.id,
        t.unit,
        t.number,
        t.street,
        t.city,
        t.district,
        t.region,
        g.zcta5ce AS postcode,
        t.hash,
        t.point
    FROM (
        SELECT *
        FROM oa_MY_STATE_staging_tmp2
        WHERE nullif(postcode, '') IS NULL
    ) t
    LEFT JOIN
    tiger.zcta5 g
    ON ST_Contains(g.the_geom, t.point)

    UNION ALL (
        SELECT
            id,
            unit,
            number,
            street,
            city,
            district,
            region,
            postcode,
            hash,
            point
        FROM oa_MY_STATE_staging_tmp2
        WHERE nullif(postcode, '') IS NOT NULL
    )
)
;

-- Deduplicate any points that fell in multiple zips.
-- Doesn't really matter which one we choose because they each have an equal
-- chance of being correct, I'd assume.
CREATE TABLE oa_MY_STATE_staging_tmp4 AS (
    SELECT DISTINCT ON (hash) *
    FROM oa_MY_STATE_staging_tmp3
)
;

-- Finally, join in blockgroup information.
CREATE TABLE oa_MY_STATE_staging_tmp5 AS (
    SELECT
        t.*,
        g.statefp,
        g.countyfp,
        g.tractce,
        g.blkgrpce
    FROM oa_MY_STATE_staging_tmp4 t
    LEFT JOIN
    tiger_data.MY_STATE_bg g
    ON ST_Contains(g.the_geom, t.point)
)
;

-- Now tidy everything up and leave the original staging table.
DROP TABLE oa_MY_STATE_staging;

CREATE TABLE oa_MY_STATE_staging AS (
    SELECT DISTINCT ON (hash) *
    FROM oa_MY_STATE_staging_tmp5
)
;

DROP TABLE oa_MY_STATE_staging_tmp1;
DROP TABLE oa_MY_STATE_staging_tmp2;
DROP TABLE oa_MY_STATE_staging_tmp3;
DROP TABLE oa_MY_STATE_staging_tmp4;
DROP TABLE oa_MY_STATE_staging_tmp5;

COMMIT;
