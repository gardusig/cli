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

# Explicit source tree — no repo-root .dockerignore.
FROM base AS ci-source
COPY pyproject.toml uv.lock README.md LICENSE coverage-unit.ini ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request scripts/pull-request
COPY src src
COPY tests tests

FROM ci-source AS version-check

ARG BASE_VERSION=
ENV BASE_VERSION=${BASE_VERSION}

RUN bash scripts/pull-request/version-check.sh

FROM ci-source AS unit-test

RUN bash scripts/pull-request/unit-test.sh

FROM ci-source AS testpypi

ARG CLI_RELEASE_VERSION=
ARG TESTPYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}

RUN bash scripts/pull-request/testpypi-release.sh

FROM python:3.12-slim AS testpypi-consumer

ARG CLI_RELEASE_VERSION=
ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_INDEX=testpypi \
    CLI_PROFILE=test \
    CI_CONSUMER_TIMEOUT=5m \
    CI_INTEGRATION_TIMEOUT=3m

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY tests/fixtures/config/config.yaml tests/fixtures/config/config.test.yaml tests/fixtures/config/drives.yaml /workspace/tests/fixtures/config/
COPY scripts/pull-request/testpypi-consumer.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/_smoke.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/integration-smoke.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/consumer /workspace/scripts/pull-request/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/pull-request/testpypi-consumer.sh
