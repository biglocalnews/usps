# Addresses API

## Development

We use [poetry](https://python-poetry.org/) for managing the package.
Make sure you have this installed with Python3.10 or higher.

### Getting started

First, make sure you have the PostGIS database with TIGER data running.
(Steps documented elsewhere.)

After cloning the repo and installing `poetry`, run the following commands:

```zsh
# Install dependencies
poetry install --with dev

# Install git hooks
poetry run pre-commit install
```

### Running development server

```zsh
poetry run uvicorn addresses_api:app --reload
```

### Running tests

```zsh
poetry run pytest
```
