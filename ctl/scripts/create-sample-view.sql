-- Create a view that combines addresses with TIGER data.
CREATE MATERIALIZED VIEW address AS (
    SELECT
        a.location_id,
        a.addr,
        a.point,
        a.building_type_code,
        a.unit_count,
        b.statefp,
        b.countyfp,
        b.tractce,
        b.blkgrpce
    FROM fabric_address a
    LEFT JOIN bg b
    ON ST_Contains(b.the_geom, a.point)
);
