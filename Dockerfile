ARG WORKDIR="/app"

# ---- Stage 1: Build dependencies ----
FROM public.ecr.aws/amazonlinux/amazonlinux:2023 AS builder

# Renew (https://stackoverflow.com/a/53682110):
ARG WORKDIR

# Install system dependencies
RUN dnf update -y && dnf install -y \
    python3.12 python3-pip \
    findutils gcc python3.12-devel \
    && dnf clean all

# Install Poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Set working directory inside container
WORKDIR ${WORKDIR}

# Copy dependency files first (Leverage Docker caching)
COPY src/pyproject.toml src/poetry.lock ./

# Install dependencies only (without dev dependencies)
RUN poetry install --no-root --only main


# ---- Stage 2: Production image ----
FROM public.ecr.aws/amazonlinux/amazonlinux:2023

# Renew (https://stackoverflow.com/a/53682110):
ARG WORKDIR

# Install Python runtime and utilities
RUN dnf update -y && dnf install -y \
    python3.12 python3-pip \
    && dnf clean all

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/app/.venv/bin:$PATH"

# Set working directory inside container
WORKDIR ${WORKDIR}

# Copy installed dependencies from builder stage
COPY --from=builder ${WORKDIR}/.venv ${WORKDIR}/.venv
COPY src ${WORKDIR}
RUN chmod -R 755 ${WORKDIR}/data

# Expose the Dash server port (8050)
EXPOSE 8050

# Set the entrypoint to run the app
CMD ["./.venv/bin/python", "main.py"]