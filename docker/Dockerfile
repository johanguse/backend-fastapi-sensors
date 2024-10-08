FROM python:3.11.9-slim as base

# Install system dependencies
RUN apt-get update \
    && apt-get -y install libpq-dev gcc

# Configure Poetry
ENV POETRY_VERSION=1.8.2
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install Poetry
RUN python3 -m venv $POETRY_VENV && \
    $POETRY_VENV/bin/pip install -U pip setuptools && \
    $POETRY_VENV/bin/pip install "poetry==$POETRY_VERSION"

# Add Poetry to PATH
ENV PATH="${PATH}:$POETRY_VENV/bin"

# Set workdir
WORKDIR /data/backend
COPY . /data/backend

# Install service dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-interaction --no-ansi
CMD [ "poetry", "shell" ]

# Run the application

## For development
FROM base as development
CMD [ "poetry", "run", "python", "-c", "print('development')" ]

## For production
FROM base as production
CMD [ "poetry", "run", "python", "-c", "print('production')" ]


