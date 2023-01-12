-- The following queries update missing information in the `oa_staging` table
-- using reverse geocoding from TIGER.

CREATE UNIQUE INDEX oa_s_hash_idx ON oa_staging(hash);

-- Fill in missing state / zip using reverse geocoding.
UPDATE oa_staging
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
        FROM oa_staging
        WHERE region = '' OR postcode = '' OR city = ''
    ) o
    LEFT JOIN LATERAL
    reverse_geocode(o.wkb_geometry) g
    ON true
) b
WHERE b.hash = oa_staging.hash
;

COMMIT;
