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
    # NOTE: some times we may actually want to update the OA data! Using the
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

    # Fill in other missing information
    cat oa-fill-missing.sql | sed 's^__TBL__^'"$staging"'^g' | psql

    # Ingest staging data to final table
    cat ingest-oa.sql | sed 's^__TBL__^'"$tbl"'^g' | sed 's^__STAGE__^'"$staging"'^g' | psql

    # Clean up staging table
    psql -c "DROP TABLE IF EXISTS $staging" -tA
done

echo 'done'
