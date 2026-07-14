# Pull-request CI — build from source.
# docker build -f docker/pull-request.dockerfile --target <stage> .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CLI_PROFILE=test \
    CI_UNIT_TIMEOUT=5m \
    CI_INTEGRATION_TIMEOUT=3m \
    CI_DOCKER_BUILD_TIMEOUT=5m \
    CI_VERSION_CHECK_TIMEOUT=2m \
    CI_TESTPYPI_TIMEOUT=5m \
    CI_CONSUMER_TIMEOUT=5m \
    CI_RESOLVE_TIMEOUT=2m

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates g++ coreutils curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

FROM base AS resolve

COPY pyproject.toml ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request/resolve-version.sh scripts/pull-request/resolve-version.sh
COPY scripts/pull-request/host-last-published-version.sh scripts/pull-request/host-last-published-version.sh

ENTRYPOINT ["bash", "scripts/pull-request/resolve-version.sh"]

FROM base AS version-check

ARG BASE_VERSION=
ENV BASE_VERSION=${BASE_VERSION}

COPY pyproject.toml ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request/version-check.sh scripts/pull-request/version-check.sh
RUN bash scripts/pull-request/version-check.sh

FROM base AS unit-test

COPY pyproject.toml uv.lock README.md LICENSE coverage-unit.ini ./
COPY scripts/ scripts/
COPY .github/workflows .github/workflows
COPY docker docker
COPY docs docs
COPY src src
COPY tests tests
RUN bash scripts/pull-request/unit-test.sh
