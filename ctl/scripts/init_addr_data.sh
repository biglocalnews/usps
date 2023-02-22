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
    "[AL]"="$collection_s"
    "[AK]"="$collection_w"
    "[AZ]"="$collection_w"
    "[AR]"="$collection_s"
    "[CA]"="$collection_w"
    "[CO]"="$collection_w"
    "[CT]"="$collection_ne"
    "[DE]"="$collection_s"
    "[DC]"="$collection_s"
    "[FL]"="$collection_s"
    "[GA]"="$collection_s"
    "[HI]"="$collection_w"
    "[ID]"="$collection_w"
    "[IL]"="$collection_mw"
    "[IN]"="$collection_mw"
    "[IA]"="$collection_mw"
    "[KS]"="$collection_mw"
    "[KY]"="$collection_s"
    "[LA]"="$collection_s"
    "[ME]"="$collection_ne"
    "[MD]"="$collection_mw"
    "[MA]"="$collection_ne"
    "[MI]"="$collection_mw"
    "[MN]"="$collection_mw"
    "[MS]"="$collection_s"
    "[MO]"="$collection_mw"
    "[MT]"="$collection_w"
    "[NE]"="$collection_mw"
    "[NV]"="$collection_w"
    "[NH]"="$collection_ne"
    "[NJ]"="$collection_ne"
    "[NM]"="$collection_w"
    "[NY]"="$collection_ne"
    "[NC]"="$collection_s"
    "[ND]"="$collection_mw"
    "[OH]"="$collection_mw"
    "[OK]"="$collection_s"
    "[OR]"="$collection_w"
    "[PA]"="$collection_ne"
    "[RI]"="$collection_ne"
    "[SC]"="$collection_s"
    "[SD]"="$collection_mw"
    "[TN]"="$collection_s"
    "[TX]"="$collection_s"
    "[UT]"="$collection_w"
    "[VT]"="$collection_ne"
    "[VA]"="$collection_s"
    "[WA]"="$collection_w"
    "[WV]"="$collection_s"
    "[WI]"="$collection_mw"
    "[WY]"="$collection_w"
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
