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

FROM base AS version-check

ARG BASE_VERSION=
ENV BASE_VERSION=${BASE_VERSION}

COPY pyproject.toml ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request/version-check.sh scripts/pull-request/version-check.sh
RUN bash scripts/pull-request/version-check.sh

FROM base AS unit-test

COPY pyproject.toml uv.lock README.md LICENSE coverage-unit.ini ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request scripts/pull-request
COPY scripts/release scripts/release
COPY .github/workflows .github/workflows
COPY docker docker
COPY docs docs
COPY src src
COPY tests tests
RUN bash scripts/pull-request/unit-test.sh

FROM base AS testpypi

ARG CLI_RELEASE_VERSION=
ARG TESTPYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}

COPY pyproject.toml README.md LICENSE ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request/testpypi-release.sh scripts/pull-request/testpypi-release.sh
COPY src src
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
COPY tests/fixtures/config/config.yaml tests/fixtures/config/config.test.yaml tests/fixtures/config/drives.yaml tests/fixtures/config/
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/pull-request/_smoke.sh scripts/pull-request/_smoke.sh
COPY scripts/pull-request/testpypi-consumer.sh scripts/pull-request/testpypi-consumer.sh
COPY scripts/pull-request/testpypi-consumer-body.sh scripts/pull-request/testpypi-consumer-body.sh
COPY scripts/pull-request/consumer/_common.sh scripts/pull-request/consumer/_common.sh
COPY scripts/pull-request/consumer/run.sh scripts/pull-request/consumer/run.sh
RUN bash scripts/pull-request/testpypi-consumer.sh
