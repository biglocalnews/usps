-- Create a table to store all the final addresses.
CREATE TABLE IF NOT EXISTS oa (
    hash varchar(255) PRIMARY KEY not null,
    addr varchar(1023) not null,
    point geometry not null
);

-- Add a spatial index on the table.
CREATE INDEX IF NOT EXISTS oa_point_idx ON oa USING GIST(point);

-- Ingest data from the staging table to the final table.
INSERT INTO oa (hash, addr, point)
SELECT oas.hash, pprint_addy(a), oas.wkb_geometry
FROM oa_staging oas
LEFT JOIN LATERAL
pagc_normalize_address(
    oas.number || ','
    || oas.street || ','
    || oas.unit || ','
    || oas.city || ','
    || oas.region || ','
    || coalesce(oas.postcode, '')
) a
ON true
WHERE oas.hash NOT IN (SELECT hash from oa)
;

COMMIT;
