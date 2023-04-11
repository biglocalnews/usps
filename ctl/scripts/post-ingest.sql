SELECT install_missing_indexes();

vacuum (analyze, verbose) tiger.addr;
vacuum (analyze, verbose) tiger.edges;
vacuum (analyze, verbose) tiger.faces;
vacuum (analyze, verbose) tiger.featnames;
vacuum (analyze, verbose) tiger.place;
vacuum (analyze, verbose) tiger.cousub;
vacuum (analyze, verbose) tiger.county;
vacuum (analyze, verbose) tiger.state;
vacuum (analyze, verbose) tiger.zcta5;
vacuum (analyze, verbose) tiger.tract;
vacuum (analyze, verbose) tiger.bg;
vacuum (analyze, verbose) tiger.zip_lookup_base;
vacuum (analyze, verbose) tiger.zip_state;
vacuum (analyze, verbose) tiger.zip_state_loc;

-- Fix invalid geometries. There are a small number of invalid geometries we
-- found in the 2022 TIGER data, e.g. these in the `place` table:
--
-- | plcidfp |       namelsad        |                 reason
-- +---------+-----------------------+----------------------------------------
-- | 0427820 | Glendale city         | Holes are nested[-112.40957 33.529845]
-- | 4740000 | Knoxville city        | Holes are nested[-84.082463 35.893129]
-- | 1738570 | Joliet city           | Holes are nested[-88.074056 41.510616]
-- | 3771940 | Wesley Chapel village | Holes are nested[-80.682658 34.989184]
--
-- There are also 120 invalid zcta5 geometries. We run the repair procedure on
-- all of the tables to be safe.
UPDATE tiger.place SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.cousub SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.county SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.state SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.zcta5 SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.tract SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
UPDATE tiger.bg SET the_geom = ST_MakeValid(the_geom) WHERE NOT ST_IsValid(the_geom);
