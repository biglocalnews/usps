# Addresses API

## Development

We use [poetry](https://python-poetry.org/) for managing the package.
Make sure you have this installed with Python3.10 or higher.

### Getting started

After cloning the repo and installing `poetry`, run the following commands:

```zsh
# Install dependencies
poetry install --with dev

# Install git hooks
poetry run pre-commit install
```

### Running the database

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
./init_tiger_data.sh
```

This will begin downloading and ingesting TIGER data into your database.
It will take a **long** time to run, so go grab a snack.

### Running development server

```zsh
poetry run uvicorn addresses_api:app --reload
```

### Running tests

```zsh
poetry run pytest
```
