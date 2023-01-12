# US Addresses Sampler

This project runs a webapp to allow fast sampling of US addresses.

## Development

There are three parts of the stack: the PostGIS database, the Python API, and the UI.

### PostGIS

We use Postgres with the PostGIS extension for geospatial analysis.

In addition, we use the TIGER extension for PostGIS to provide geographic context.

You can run a database locally with docker-compose.

```zsh
docker-compose up --build
```

#### Ingesting data (first time)

When you are setting up a new PostGIS database, you will need to ingest data from TIGER.

We provide a container in the docker-compose environment to make this easy.

```zsh
# Get a shell in the controller container:
docker exec -it addresses_ctl_1 /bin/bash

# Run TIGER ingestion script.
# Here I'm only pulling Vermont data; you can pass any state here, or `all`.
./init_tiger_data.sh VT
```

This will begin downloading and ingesting TIGER data into your database.
It will take a **long** time to run, so go grab a snack.

#### Resetting dev database

If you want to nuke everything in the DB and start over, you can delete the docker volume:

First, stop the docker-compose process if it's running. Then:

```zsh
docker rm addresses_db_1 && docker volume rm addresses_pgdata
```

Now you will have a fresh PostGIS database when you start docker-compose again.
You will of course have to re-ingest TIGER data, but hopefully it is at least cached still from the last time you ran it.

### API

See the [api/README](api/README.md).

### UI

See the [app/README](app/README.md).
