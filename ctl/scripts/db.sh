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
