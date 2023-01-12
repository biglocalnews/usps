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
        to_tsvector('english', name) AS tsv
    FROM tiger.state

    UNION ALL

    -- Counties
    SELECT
        c.gid,
        'county' AS kind,
        c.namelsad || ', ' || s.name AS name,
        to_tsvector('english', concat_ws(' ', c.namelsad, s.name)) AS tsv
    FROM tiger.county c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    UNION ALL

    -- County subdivisions (e.g., "town")
    SELECT
        c.gid,
        'cousub' as kind,
        c.name || ', ' || s.name AS name,
        to_tsvector('english', concat_ws(' ', c.namelsad, s.name)) AS tsv
    FROM tiger.cousub c
    LEFT JOIN tiger.state s
    ON c.statefp = s.statefp

    -- TODO add more possible search features:
    --   BlockGroup
    --   Tract
    --   Place. There is some overlap with cousub here, but they are meaningfully different.
    --   Zip. This would require enabling zip geometries, which are expensive.
);

-- Create a search index on the tsv column.
CREATE INDEX htsv_idx ON haystack USING GIN (tsv);
