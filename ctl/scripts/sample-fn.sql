-- Function optimized to draw samples.
CREATE OR REPLACE FUNCTION public.usps_sample(g geometry, lim int, pct float)
RETURNS TABLE (
    hash varchar,
    unit varchar,
    number varchar,
    street varchar,
    city varchar,
    district varchar,
    region varchar,
    postcode varchar,
    lon float,
    lat float,
    tract_id varchar(11),
    blkgrpce varchar(1)
)
LANGUAGE 'plpgsql'
AS
$$
DECLARE
    fps record;
    local_addrs_sql text;
BEGIN
    DROP TABLE IF EXISTS local_tracts;

    CREATE TEMP TABLE local_tracts AS
    SELECT t.tract_id
    FROM tract t
    WHERE t.the_geom && g;

    drop table if exists local_addrs;
    create temp table local_addrs (
        r float,
        hash varchar,
        point geometry,
        unit varchar,
        number varchar,
        street varchar,
        city varchar,
        district varchar,
        region varchar,
        postcode varchar,
        tract_id varchar(11),
        blkgrpce varchar(1)
    );

    for fps in SELECT t.statefp, LOWER(s.stusps) as abbr
                FROM (
                    SELECT distinct substring(x.tract_id for 2) as statefp
                    FROM local_tracts x
                ) t LEFT JOIN state s
                ON t.statefp = s.statefp
    loop
        local_addrs_sql = 'INSERT INTO local_addrs(r, hash, point, unit, number, street, city, district, region, postcode, tract_id, blkgrpce)'
            ' SELECT random(), a.hash, a.point, a.unit, a.number, a.street, a.city, a.district, a.region, a.postcode, a.tract_id, a.blkgrpce'
            ' FROM oa_%I a '
            ' WHERE a.tract_id IN (SELECT t.tract_id FROM local_tracts t)';
        EXECUTE format(local_addrs_sql, fps.abbr);
        DELETE FROM local_addrs WHERE NOT ST_Contains(g, local_addrs.point);
    end loop;

    return query SELECT
        a.hash,
        a.unit,
        a.number,
        a.street,
        a.city,
        a.district,
        a.region,
        a.postcode,
        St_X(a.point) as lon,
        St_Y(a.point) as lat,
        a.tract_id,
        a.blkgrpce
        FROM local_addrs a
        WHERE pct < 0 OR a.r < pct  -- Only applies when pct > 0
        ORDER BY a.r
        LIMIT lim;
END;
$$
;
