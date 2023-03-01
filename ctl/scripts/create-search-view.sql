CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- This script creates a table that can be used for searching the geometries.
-- All of the records returned in the table should have a geometry stored in
-- their own original table.
--
-- The application can display `name` for the user to evaluate, and then
-- fetch the geometry from the original record with (kind, gid).

-- Drop any outdated search table.
DROP TABLE IF EXISTS haystack;

-- The search table has the columns:
--  gid      the primary key in the original table
--  kind     token to indicate which original table the record comes from
--  name     the human-readable name (label) for the record
-- secondary additional context for where the area is
CREATE TABLE haystack AS (

    -- States
    SELECT
        gid,
        'state' AS kind,
        name,
        'USA' AS secondary
    FROM tiger.state

    UNION ALL

    -- Counties
    SELECT
        c.gid,
        'county' AS kind,
        c.namelsad AS name,
        s.name AS secondary
    FROM tiger.county c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- Zipcode tabulation areas
    SELECT
        z.gid,
        'zcta5' AS kind,
        z.zcta5ce,
        s.name AS secondary
    FROM tiger.zcta5 z
    LEFT JOIN tiger.state s
    ON z.statefp = s.statefp

    UNION ALL

    -- County subdivisions (e.g., "town")
    SELECT
        c.gid,
        'cousub' AS kind,
        c.name AS name,
        s.name AS secondary
    FROM tiger.cousub c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- Places (e.g., "village")
    SELECT
        c.gid,
        'place' AS kind,
        c.namelsad AS name,
        s.name AS secondary
    FROM tiger.place c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- Tracts
    SELECT
        t.gid,
        'tract' AS kind,
        t.tract_id AS name,
        c.namelsad || ', ' || s.name AS secondary
        FROM tiger.tract t
        LEFT JOIN tiger.county c
        ON t.statefp = c.statefp AND t.countyfp = c.countyfp
        LEFT JOIN tiger.state s
        ON t.statefp = s.statefp

    UNION ALL

    -- Blockgroups
    SELECT
        b.gid,
        'bg' AS kind,
        b.bg_id AS name,
        t.namelsad || ', ' || c.namelsad || ', ' || s.name AS secondary
        FROM tiger.bg b
        LEFT JOIN tiger.tract t
        ON b.statefp = t.statefp AND b.countyfp = t.countyfp AND b.tractce = t.tractce
        LEFT JOIN tiger.county c
        ON b.statefp = c.statefp AND b.countyfp = c.countyfp
        LEFT JOIN tiger.state s
        ON b.statefp = s.statefp


    -- TODO add more possible search features:
    --   Leg district. Requires downloading more data.
);

ALTER TABLE haystack ADD COLUMN search varchar
GENERATED ALWAYS AS (name || ' ' || secondary) STORED;

-- Create a search index on the search column.
CREATE INDEX hsearch_idx ON haystack USING gin (search gin_trgm_ops);

-- Create another index on the type column.
CREATE INDEX hkind_idx ON haystack (kind);
