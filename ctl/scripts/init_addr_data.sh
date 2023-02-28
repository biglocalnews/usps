#!/usr/bin/env bash
set -ex

# Import common tools.
. "$(dirname "$0")/common.sh" "$1"

ADDR_TABLE="oa"

# Create an index of which batch download from OA contains which states.
collection_ne="collection-us-northeast"
collection_w="collection-us-west"
collection_mw="collection-us-midwest"
collection_s="collection-us-south"

declare -A statelookup=(
    [al]="$collection_s"
    [ak]="$collection_w"
    [az]="$collection_w"
    [ar]="$collection_s"
    [ca]="$collection_w"
    [co]="$collection_w"
    [ct]="$collection_ne"
    [de]="$collection_s"
    [dc]="$collection_s"
    [fl]="$collection_s"
    [ga]="$collection_s"
    [hi]="$collection_w"
    [id]="$collection_w"
    [il]="$collection_mw"
    [in]="$collection_mw"
    [ia]="$collection_mw"
    [ks]="$collection_mw"
    [ky]="$collection_s"
    [la]="$collection_s"
    [me]="$collection_ne"
    [md]="$collection_mw"
    [ma]="$collection_ne"
    [mi]="$collection_mw"
    [mn]="$collection_mw"
    [ms]="$collection_s"
    [mo]="$collection_mw"
    [mt]="$collection_w"
    [ne]="$collection_mw"
    [nv]="$collection_w"
    [nh]="$collection_ne"
    [nj]="$collection_ne"
    [nm]="$collection_w"
    [ny]="$collection_ne"
    [nc]="$collection_s"
    [nd]="$collection_mw"
    [oh]="$collection_mw"
    [ok]="$collection_s"
    [or]="$collection_w"
    [pa]="$collection_ne"
    [ri]="$collection_ne"
    [sc]="$collection_s"
    [sd]="$collection_mw"
    [tn]="$collection_s"
    [tx]="$collection_s"
    [ut]="$collection_w"
    [vt]="$collection_ne"
    [va]="$collection_s"
    [wa]="$collection_w"
    [wv]="$collection_s"
    [wi]="$collection_mw"
    [wy]="$collection_w"
)

declare -A statefipslookup=(
    [al]="01"
    [ak]="02"
    [az]="04"
    [ar]="05"
    [ca]="06"
    [co]="08"
    [ct]="09"
    [de]="10"
    [dc]="11"
    [fl]="12"
    [ga]="13"
    [hi]="15"
    [id]="16"
    [il]="17"
    [in]="18"
    [ia]="19"
    [ks]="20"
    [ky]="21"
    [la]="22"
    [me]="23"
    [md]="24"
    [ma]="25"
    [mi]="26"
    [mn]="27"
    [ms]="28"
    [mo]="29"
    [mt]="30"
    [ne]="31"
    [nv]="32"
    [nh]="33"
    [nj]="34"
    [nm]="35"
    [ny]="36"
    [nc]="37"
    [nd]="38"
    [oh]="39"
    [ok]="40"
    [or]="41"
    [pa]="42"
    [ri]="44"
    [sc]="45"
    [sd]="46"
    [tn]="47"
    [tx]="48"
    [ut]="49"
    [vt]="50"
    [va]="51"
    [wa]="53"
    [wv]="54"
    [wi]="55"
    [wy]="56"
)

# Create address standardizer extension if it's not installed already.
psql -c "CREATE EXTENSION IF NOT EXISTS address_standardizer" -tA

# Ingest all the geojson files into the DB.
for state in $(echo "$states" | awk '{ print tolower($0) }' | tr "," "\n"); do
    cd /addrdata

    tbl="$ADDR_TABLE"_"$state"
    staging="$tbl"_staging
    exists=$(psql -c "SELECT exists (SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name='$tbl')" --csv | tail -1)
    if [[ "$exists" == "t" ]]; then
        echo "$tbl exists already! skipping."
        continue
    fi

    psql -c "DROP TABLE IF EXISTS $staging" -tA

    # Find the collection for this state
    col="${statelookup[$state]}"
    # Make sure we have the collection downloaded.
    # NOTE: sometimes we may actually want to update the OA data! Using the
    # --no-clobber option will avoid ever refetching the new addresses.
    # Ideally we just use the `--mirror` option, but currently that results
    # in a new batch being downloaded every single time it runs :(
    wget --no-clobber -r "https://v2.openaddresses.io/batch-prod/$col.zip"

    # Unzip only the geojson addresses file for this state
    unzip -o "v2.openaddresses.io/batch-prod/$col.zip" 'us/'"$state"'/*-addresses*.geojson' ; r=$? ; [ "$r" == "11" ] || [ "$r" == "0" ]
    for f in us/"$state"/*.geojson; do
        ogr2ogr -f "PostgreSQL" PG:"dbname=$PGDATABASE user=$PGUSER" "$f" -nln "$staging" -append
    done

    # Make sure state is filled out for every address
    psql -c "UPDATE $staging SET region='$state' WHERE region = '' OR region IS NULL" -tA

    cd /

    # Fill in other missing columns using reverse geocoding.
    cat oa-fill-missing.sql | sed 's^MY_STATE^'"$state"'^g' | psql

    # Throw out invalid addresses. Keep the hash in a log so that we can
    # investigate / fix them later.
    mkdir -p /addrdata/err
    psql -c "SELECT hash FROM $staging WHERE nullif(city, '') IS NULL OR point IS NULL OR nullif(hash, '') IS NULL OR tract_id IS NULL" --csv > "/addrdata/err/invalid-addr-$tbl.csv"
    psql -c "DELETE FROM $staging WHERE nullif(city, '') IS NULL OR point IS NULL OR nullif(hash, '') IS NULL OR tract_id IS NULL" -tA

    # Ingest staging data to final table
    cat ingest-oa.sql | sed 's^__TBL__^'"$tbl"'^g' | sed 's^__STAGE__^'"$staging"'^g' | psql
    fips="${statefipslookup[$state]}"

    # Partition the tables by tracts
    psql -c "ALTER TABLE oa_"$state" ADD CONSTRAINT oa_"$state"_tract_cx CHECK (tract_id >= '"$fips"000000000' AND tract_id <= '"$fips"999999999');" -tA

    # Clean up staging table / data
    psql -c "DROP TABLE IF EXISTS $staging" -tA
    psql -c "VACUUM ANALYZE oa_$state" -tA
    rm -r "/addrdata/us/$state"
done

echo 'done'
