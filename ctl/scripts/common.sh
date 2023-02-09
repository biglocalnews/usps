export states="$1"

# Check if argument was missing
if [ -z "$states" ]; then
    echo "Pass in a comma separated list of states to load, e.g. 'CA,NV'. Pass 'all' to load everything."
    exit 1
fi

# Expand 'all'
if [ "$states" = "all" ]; then
    echo "Loading EVERY state!! This will take a very, very long time!"
    export states="AL,AK,AZ,AR,CA,CO,CT,DE,DC,FL,GA,HI,ID,IL,IN,IA,KS,KY,LA,ME,MD,MA,MI,MN,MS,MO,MT,NE,NV,NH,NJ,NM,NY,NC,NH,OH,OK,OR,PA,RI,SC,SD,TN,TX,UT,VT,VA,WA,WV,WI,WY"
fi

# Make sure to use upper case. TIGER scripts don't work otherwise.
export states=$(echo "$states" | tr '[:lower:]' '[:upper:]')

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
