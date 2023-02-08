-- This script creates a view that can be used for searching the geometries.
-- All of the records returned in the table should have a geometry stored in
-- their own original table.
--
-- The application can display `name` for the user to evaluate, and then
-- fetch the geometry from the original record with (kind, gid).

-- Drop any outdated search view.
DROP MATERIALIZED VIEW IF EXISTS haystack;

-- The search view has the columns:
--  gid      the primary key in the original table
--  kind     token to indicate which original table the record comes from
--  name     the human-readable name (label) for the record
--  tsv      the search vector
--
-- The search vector is probably usually very similar to the name, but might
-- contain slightly different information to make searching more intuitive.
CREATE MATERIALIZED VIEW haystack AS (

    -- States
    SELECT
        gid,
        'state' AS kind,
        name,
        'USA' AS secondary,
        to_tsvector('english', name) AS tsv
    FROM tiger.state

    UNION ALL

    -- Counties
    SELECT
        c.gid,
        'county' AS kind,
        c.namelsad AS name,
        s.name AS secondary,
        to_tsvector('english', concat_ws(' ', c.namelsad, s.name)) AS tsv
    FROM tiger.county c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- County subdivisions (e.g., "town")
    SELECT
        c.gid,
        'cousub' AS kind,
        c.name AS name,
        s.name AS secondary,
        to_tsvector('english', concat_ws(' ', c.namelsad, s.name)) AS tsv
    FROM tiger.cousub c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- Places (e.g., "village")
    SELECT
        c.gid,
        'place' AS kind,
        c.namelsad AS name,
        s.name AS secondary,
        to_tsvector('english', concat_ws(' ', c.namelsad, s.name)) AS tsv
    FROM tiger.place c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- Tracts
    SELECT
        t.gid,
        'tract' AS kind,
        t.namelsad AS name,
        c.namelsad || ', ' || s.name AS secondary,
        to_tsvector('english', concat_ws(' ', t.namelsad, c.namelsad, s.name)) AS tsv
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
        b.namelsad AS name,
        t.namelsad || ', ' || c.namelsad || ', ' || s.name AS secondary,
        to_tsvector('english', concat_ws(' ', b.namelsad, t.namelsad, c.namelsad, s.name)) AS tsv
        FROM tiger.bg b
        LEFT JOIN tiger.tract t
        ON b.statefp = t.statefp AND b.countyfp = t.countyfp AND b.tractce = t.tractce
        LEFT JOIN tiger.county c
        ON b.statefp = c.statefp AND b.countyfp = c.countyfp
        LEFT JOIN tiger.state s
        ON b.statefp = s.statefp


    -- TODO add more possible search features:
    --   Zip. This would require enabling zip geometries, which are expensive.
    --   Leg district. Requires downloading more data.
);

-- Create a search index on the tsv column.
CREATE INDEX htsv_idx ON haystack USING GIN (tsv);

-- Create another index on the type column.
CREATE INDEX hkind_idx ON haystack (kind);
