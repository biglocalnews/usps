#!/usr/bin/env bash
set -ex

# Import common tools.
. "$(dirname "$0")/common.sh" "$1"

cd /addrdata

ADDR_TABLE="oa"
ADDR_STAGING_TABLE="oa_staging"

# Create an index of which batch download from OA contains which states.
collection_ne="collection-us-northeast"
collection_w="collection-us-west"
collection_mw="collection-us-midwest"
collection_s="collection-us-south"

declare -A statelookup=(
    "[al]"="$collection_s"
    "[ak]"="$collection_w"
    "[az]"="$collection_w"
    "[ar]"="$collection_s"
    "[ca]"="$collection_w"
    "[co]"="$collection_w"
    "[ct]"="$collection_ne"
    "[de]"="$collection_s"
    "[dc]"="$collection_s"
    "[fl]"="$collection_s"
    "[ga]"="$collection_s"
    "[hi]"="$collection_w"
    "[id]"="$collection_w"
    "[il]"="$collection_mw"
    "[in]"="$collection_mw"
    "[ia]"="$collection_mw"
    "[ks]"="$collection_mw"
    "[ky]"="$collection_s"
    "[la]"="$collection_s"
    "[me]"="$collection_ne"
    "[md]"="$collection_mw"
    "[ma]"="$collection_ne"
    "[mi]"="$collection_mw"
    "[mn]"="$collection_mw"
    "[ms]"="$collection_s"
    "[mo]"="$collection_mw"
    "[mt]"="$collection_w"
    "[ne]"="$collection_mw"
    "[nv]"="$collection_w"
    "[nh]"="$collection_ne"
    "[nj]"="$collection_ne"
    "[nm]"="$collection_w"
    "[ny]"="$collection_ne"
    "[nc]"="$collection_s"
    "[nd]"="$collection_mw"
    "[oh]"="$collection_mw"
    "[ok]"="$collection_s"
    "[or]"="$collection_w"
    "[pa]"="$collection_ne"
    "[ri]"="$collection_ne"
    "[sc]"="$collection_s"
    "[sd]"="$collection_mw"
    "[tn]"="$collection_s"
    "[tx]"="$collection_s"
    "[ut]"="$collection_w"
    "[vt]"="$collection_ne"
    "[va]"="$collection_s"
    "[wa]"="$collection_w"
    "[wv]"="$collection_s"
    "[wi]"="$collection_mw"
    "[wy]"="$collection_w"
)

# Create address standardizer extension if it's not installed already.
psql -c "CREATE EXTENSION IF NOT EXISTS address_standardizer" -tA

# Ingest all the geojson files into the DB.
for state in $(echo "$states" | awk '{ print tolower($0) }' | tr "," "\n"); do
    psql -c "DROP TABLE IF EXISTS $ADDR_STAGING_TABLE" -tA

    # Find the collection for this state
    col="${statelookup[$state]}"
    # Make sure we have the collection downloaded
    wget --mirror "https://v2.openaddresses.io/batch-prod/$col.zip"

    # Unzip only the geojson addresses file for this state
    unzip "v2.openaddresses.io/batch-prod/$col.zip" 'us/'"$state"'/*-addresses*.geojson' ; r=$? ; [ "$r" == "11" ] || [ "$r" == "0" ]
    for f in us/"$state"/*.geojson; do
        ogr2ogr -f "PostgreSQL" PG:"dbname=$PGDATABASE user=$PGUSER" "$f" -nln "$ADDR_STAGING_TABLE" -append
    done

    # Make sure state is filled out for every address
    psql -c "UPDATE $ADDR_STAGING_TABLE SET region='$state' WHERE region = '' OR region IS NULL" -tA

    # Fill in other missing information
    cat oa-fill-missing.sql | psql

    # Ingest staging data to final table
    cat ingest-oa.sql | psql
done

# Create the search view
cat create-oa-sample-view.sql | psql

echo 'done'
