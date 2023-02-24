-- The following queries update missing information in the staging table.

-- Transform the point geometry to SRID 4269 to match TIGER data.
ALTER TABLE __TBL__ ADD COLUMN point geometry;

UPDATE __TBL__
SET
point = ST_Transform(wkb_geometry, 4269)
;

-- Use indexes to hopefully speed up the updates.
CREATE INDEX IF NOT EXISTS __TBL___hash_idx ON __TBL__ (hash);
CREATE INDEX IF NOT EXISTS __TBL___point_idx ON __TBL__ USING SPGIST (point);

-- Fill in missing city with a spatial join on place/cousub.
UPDATE __TBL__
SET
city = coalesce(b.place, b.cousub)
FROM (
    SELECT
        o.hash,
        p.name as place,
        c.name as cousub
    FROM (
        SELECT hash, point
        FROM __TBL__
        WHERE city = ''
    ) o
    LEFT JOIN
    place p
    ON ST_Intersects(p.the_geom, o.point)
    LEFT JOIN
    cousub c
    ON ST_Intersects(c.the_geom, o.point)
) b
WHERE b.hash = __TBL__.hash
;

-- Fill in missing zip code using the same technique.
UPDATE __TBL__
SET
postcode = z.zcta5ce
FROM (
    SELECT
        o.hash,
        p.name as place,
        c.name as cousub
    FROM (
        SELECT hash, point
        FROM __TBL__
        WHERE postcode = ''
    ) o
    LEFT JOIN
    zcta5 z
    ON ST_Intersects(z.the_geom, o.point)
) b
WHERE b.hash = __TBL__.hash
;

COMMIT;
