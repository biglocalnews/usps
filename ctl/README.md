# Controller container

This module provides a docker image with administrative utilities.

# Volumes

This image should have two volume mounts:

- `/run/secrets` to contain database credentials and other secrets; and
- `/gisdata` to contain data mirrored from TIGER.

# Scripts

## `./init_tiger_data.sh`

This script generates and runs the [shell scripts](https://postgis.net/docs/Extras.html#Tiger_Geocoder),
used to load TIGER data into PostGIS.

Run this script to download and ingest TIGER data into a new database.
