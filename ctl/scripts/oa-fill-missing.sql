-- The following queries update missing information in the staging table.
BEGIN;

-- Transform the point geometry to SRID 4269 to match TIGER data.
ALTER TABLE __TBL__ ADD COLUMN point geometry;

UPDATE __TBL__
SET
point = ST_Transform(wkb_geometry, 4269)
;

-- Use indexes to hopefully speed up the updates.
CREATE INDEX IF NOT EXISTS __TBL___point_idx ON __TBL__ USING SPGIST (point);

-- Fill in missing city/zipcode, and enrich with blockgroups.
CREATE TABLE __TBL___tmp AS (
    SELECT
        t.*,
        p.name as pname,
        c.name as csname,
        z.zcta5ce as zname,
        b.statefp,
        b.countyfp,
        b.tractce,
        b.blkgrpce
    FROM __TBL__ t
    LEFT JOIN
    bg b
    ON ST_Contains(b.the_geom, t.point)
    LEFT JOIN
    place p
    ON NULLIF(t.city, '') IS NULL AND ST_Contains(p.the_geom, t.point)
    LEFT JOIN
    cousub c
    ON NULLIF(t.city, '') IS NULL AND ST_Contains(c.the_geom, t.point)
    LEFT JOIN
    zcta5 z
    ON NULLIF(t.postcode, '') IS NULL AND ST_Contains(z.the_geom, t.point)
);


DROP TABLE __TBL__;
ALTER TABLE __TBL___tmp RENAME TO __TBL__;

COMMIT;
