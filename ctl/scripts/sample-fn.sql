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
VOLATILE
PARALLEL RESTRICTED
LEAKPROOF
AS
$$
DECLARE
    local_addrs_sql text;
    abbr text;
    gpart record;
    tcand record;
BEGIN
    CREATE TEMP TABLE local_addrs (
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
    ) ON COMMIT DROP;

    FOR gpart IN SELECT p FROM St_SubDivide(g) p
    LOOP
        FOR tcand IN SELECT t.tract_id FROM tract t WHERE t.the_geom && gpart.p
        LOOP
            SELECT LOWER(s.stusps) INTO abbr FROM state s WHERE s.statefp = substring(tcand.tract_id for 2);
            local_addrs_sql = ''
                'WITH sample AS ('
                ' SELECT random(), a.hash, a.point, a.unit, a.number, a.street, a.city, a.district, a.region, a.postcode, a.tract_id, a.blkgrpce'
                ' FROM oa_%I a '
                ' WHERE a.tract_id = $1'
                ')'
                ' INSERT INTO local_addrs(r, hash, point, unit, number, street, city, district, region, postcode, tract_id, blkgrpce)'
                ' SELECT s.* FROM sample s WHERE ST_Contains($2, s.point)';
            EXECUTE format(local_addrs_sql, abbr) USING tcand.tract_id, gpart.p;
        END LOOP;
    END LOOP;

    RETURN QUERY SELECT
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
