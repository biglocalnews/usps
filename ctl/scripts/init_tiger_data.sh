#!/usr/bin/env bash
set -ex

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
# We do four things:
#  1) Set the script to run with bash;
#  2) Set the script to abort execution on failures;
#  3) Set the correct path to the psql binary; and
#  3) Set the postgres credentials to values provided by secrets.
patch_script () {
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
        >> "$tmp"
    mv "$tmp" "$1"
}

# Generate nation script
psql -c "SELECT Loader_Generate_Nation_Script('sh')" -tA > "$SCRIPT_DIR/nation.sh"
patch_script "$SCRIPT_DIR/nation.sh"
chmod +x "$SCRIPT_DIR/nation.sh"

# Run the nation script
"$SCRIPT_DIR/nation.sh"

# Generate the state script
psql -c "SELECT Loader_Generate_Script(ARRAY['VT'], 'sh')" -tA > "$SCRIPT_DIR/state.sh"
patch_script "$SCRIPT_DIR/state.sh"
chmod +x "$SCRIPT_DIR/state.sh"

# Run the state script
"$SCRIPT_DIR/state.sh"
