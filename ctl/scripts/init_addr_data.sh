#!/usr/bin/env bash
set -ex

# Import common tools.
. "$(dirname "$0")/common.sh" "$1"

cd /addrdata

ADDR_TABLE="oa"
ADDR_STAGING_TABLE="oa_staging"

# TODO - check if address standardizer exists and if not run CREATE EXTENSION address_standardizer
# TODO - download .zip files from OA server.
# TODO - index the states in each zip so we can limit downloads

# Ingest all the geojson files into the DB.
for state in $(echo "$states" | awk '{ print tolower($0) }' | tr "," "\n"); do
    psql -c "DROP TABLE IF EXISTS $ADDR_STAGING_TABLE" -tA

    # Unzip only the geojson addresses file for this state
    # TODO - support other regions!
    unzip 'collection-us-northeast.zip' 'us/'"$state"'/*-addresses*.geojson' ; r=$? ; [ "$r" == "11" ] || [ "$r" == "0" ]
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
