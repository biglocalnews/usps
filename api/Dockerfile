FROM python:3.11.2-bullseye

ENV PYTHONFAULTHANDLER=1 \
      PYTHONUNBUFFERED=1 \
      PYTHONHASHSEED=random \
      PIP_NO_CACHE_DIR=off \
      PIP_DISABLE_PIP_VERSION_CHECK=on \
      PIP_DEFAULT_TIMEOUT=100 \
      POETRY_VIRTUALENVS_CREATE=false

# Set up poetry
RUN pip install poetry==1.3.2

WORKDIR /code

# Copy dependency manifests
COPY poetry.lock pyproject.toml /code/

# Install dependencies
RUN poetry install --only main --no-interaction --no-ansi

COPY . /code

CMD ["uvicorn", "addresses_api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
