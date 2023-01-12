#!/usr/bin/env bash
set -ex

states="$1"

# Check if argument was missing
if [ -z "$states" ]; then
    echo "Pass in a comma separated list of states to load, e.g. 'CA,NV'. Pass 'all' to load everything."
    exit 1
fi

# Expand 'all'
if [ "$states" = "all" ]; then
    echo "Loading EVERY state!! This will take a very, very long time!"
    states="AL,AK,AZ,AR,CA,CO,CT,DE,DC,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,NH,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY"
fi

# Set up directories
SCRIPT_DIR=${SCRIPT_DIR:-/tiger_loader}
mkdir -p "$SCRIPT_DIR"

# Get the value of a secret, potentially with a default value.
# Secrets are files in `/run/secrets`.
get_secret () {
    local ret="$2"
    local secretf="/run/secrets/$1"
    if test -f "$secretf"; then
        ret=$(cat "$secretf" | tr -d '\n')
    fi
    echo "$ret"
}

# Postgres credentials. These should come from secrets, though some defaults
# are provided here.
export PGBIN=$(dirname $(which psql))
export PGPORT=$(get_secret db_port 5432)
export PGHOST=$(get_secret db_host localhost)
export PGUSER=$(get_secret db_user postgres)
export PGDATABASE=$(get_secret db_name addresses)
export PGPASSWORD=$(get_secret db_pass)

# Function to patch the PostGIS/TIGER loader scripts.
# We do a few things:
#  1) Set the script to run with bash;
#  2) Set the script to abort execution on failures rather than ignore them;
#  3) Set the correct path to the psql binary;
#  4) Set the postgres credentials to values provided by secrets; and
#  5) Patch a bug in shp2pgsql which can try to create tables with varchar(0)
#     type, which is illegal and will fail. This probably fails silently for
#     most users and results in an incomplete dataset.
patch_load_script () {
    tmp="$1.tmp"
    echo '#!/usr/bin/env bash' > "$tmp"
    echo 'set -ex' >> "$tmp"
    echo >> "$tmp"
    cat "$1" \
        | sed 's^\(PGBIN\)=.*^\1='"$PGBIN"'^' \
        | sed 's^\(PGHOST\)=.*^\1='"$PGHOST"'^' \
        | sed 's^\(PGUSER\)=.*^\1='"$PGUSER"'^' \
        | sed 's^\(PGPASSWORD\)=.*^\1=$(cat /run/secrets/db_pass | tr -d '"'"'\\n'"'"')^' \
        | sed 's^\(PGDATABASE\)=.*^\1='"$PGDATABASE"'^' \
        | sed 's/\(${SHP2PGSQL}.*\) | \(${PSQL}\)/\1 | sed '"'"'s^varchar(0)^varchar(1)^'"'"' | \2/' \
        >> "$tmp"
    mv "$tmp" "$1"
}

# Generate nation script
psql -c "SELECT Loader_Generate_Nation_Script('sh')" -tA > "$SCRIPT_DIR/nation.sh"
patch_load_script "$SCRIPT_DIR/nation.sh"
chmod +x "$SCRIPT_DIR/nation.sh"

# Run the nation script
"$SCRIPT_DIR/nation.sh"

# Select additional features to load for states
# We do this instead of running the Loader_Generate_Census_Script separately,
# as described in the docs:
# http://postgis.net/docs/postgis_installation.html#install_tiger_geocoder_extension
#
# Note that `addrfeat` also looks tempting, but it turns out to be redundant, and
# there is a bug in getting it to load that we'd need to patch:
# https://trac.osgeo.org/postgis/ticket/4655
psql -c "UPDATE tiger.loader_lookuptables SET load = true WHERE lookup_name IN('tract', 'bg', 'tabblock20')" -tA

# Generate the state script
statestr=$(echo $states | sed 's/\([A-Z][A-Z]\)/'"'"'\1'"'"'/gi')
psql -c "SELECT Loader_Generate_Script(ARRAY[$statestr], 'sh')" -tA > "$SCRIPT_DIR/state.sh"
patch_load_script "$SCRIPT_DIR/state.sh"
chmod +x "$SCRIPT_DIR/state.sh"

# Run the state script
"$SCRIPT_DIR/state.sh"

# Run vacuum as recommended in the instructions:
# http://postgis.net/docs/postgis_installation.html#install_tiger_geocoder_extension
cat post-ingest.sql | psql

# Create the view that we can use to run search queries.
cat create-search-view.sql | psql
