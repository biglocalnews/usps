-- The following queries update missing information in the `oa_staging` table
-- using reverse geocoding from TIGER.

CREATE INDEX IF NOT EXISTS __TBL___hash_idx ON __TBL__(hash);

-- Fill in missing state / zip using reverse geocoding.
UPDATE __TBL__
SET
region = b.state,
postcode = b.zip,
city = b.location
FROM (
    SELECT
        o.hash,
        (addy)[1].zip as zip,
        (addy)[1].stateAbbrev as state,
        (addy)[1].location as location
    FROM (
        SELECT hash, wkb_geometry
        FROM __TBL__
        WHERE region = '' OR postcode = '' OR city = ''
    ) o
    LEFT JOIN LATERAL
    reverse_geocode(o.wkb_geometry, false) g
    ON true
) b
WHERE b.hash = __TBL__.hash
;

COMMIT;
