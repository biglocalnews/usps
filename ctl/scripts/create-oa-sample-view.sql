-- Create a view that combines addresses with TIGER data.
CREATE MATERIALIZED VIEW IF NOT EXISTS address AS (
    SELECT
        a.hash,
        a.addr,
        a.point,
        b.statefp,
        b.countyfp,
        b.tractce,
        b.blkgrpce
    FROM oa a
    LEFT JOIN bg b
    ON ST_Contains(b.the_geom, a.point)
);

-- Create indexes for fast querying.
-- FIPS indexes can narrow down the search space faster than spatial indexes.
CREATE INDEX ON address (statefp, countyfp);
-- Filters on building types are almost always used.
CREATE INDEX ON address (building_type_code);
-- Add a spatial index on all the points. This is a very large index and takes
-- quite a long time to compute!
CREATE INDEX ON address USING GIST (point);
