# US Place Sampler

This project runs a webapp to allow fast sampling of US addresses
within arbitrary (but usually CENSUS-based) geometries.

## Usage / development

There are four parts of the stack:

1.  The PostGIS database
2.  A "work box" VM that has all the CLI tools for working with the DB
3.  The Python API
4.  The UI

The full stack can be run with:

```zsh
docker compose up --build
```

The app will be served at `http://localhost/`.
You will need to ingest some TIGER and OpenAddresses data to use it.
(See below!)

### PostGIS

We use Postgres with the PostGIS extension for geospatial analysis.

In addition, we use the TIGER extension for PostGIS to provide geographic context.

You can run a database locally with docker-compose.

### Work Box `ctl`

See the scripts in `./ctl/` for more info.

For development, it's useful to just run the `ctl` and `db` VMs in docker.

```zsh
docker compose up db ctl --build
```

#### Ingesting data (only need to do once)

When you are setting up a new PostGIS database, you will need to ingest data from TIGER.

We provide a container in the docker-compose environment to make this easy.

```zsh
# Get a shell in the controller container:
docker exec -it usps_ctl_1 /bin/bash

# Run TIGER ingestion script.
# Here I'm only pulling Vermont data; you can pass any state here, or `all`.
./init_tiger_data.sh VT

# Run OpenAddresses ingestion script.
# Again, only doing one small (but mighty) state for demoing.
./init_addr_data.sh VT
```

This will begin downloading and ingesting TIGER data into your database.
Ingesting the entire country will take a **long** time to run
(many hours, even days), so make sure you have a snack handy.

### API

See the [api/README](api/README.md).

### UI

See the [app/README](app/README.md).

## Production

You can add a supplemental `docker-compose.prod.yml` to expand the cluster for deployment.

Tips:

1.  Use a better nginx config (with SSL)
2.  `certbot/cerbot` can handle certificates
3.  The `postgresql.conf` should be tuned for your hardware
4.  The `services.db.shm_size` might need to be increased for large volumes of data
5.  Use production-ready secrets as needed
6.  Configure the volumes in docker compose to be persistent on a disk (preferablly SSD for Postgres data!)
