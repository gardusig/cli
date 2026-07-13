# CI and release pipeline — build with: docker build --target <stage> .
#
# Pull request: version-check, unit-test, testpypi, testpypi-consumer
# Release:      pypi, runtime

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CLI_PROFILE=test \
    CI_UNIT_TIMEOUT=5m \
    CI_INTEGRATION_TIMEOUT=3m \
    CI_DOCKER_BUILD_TIMEOUT=10m \
    CI_VERSION_CHECK_TIMEOUT=2m \
    CI_TESTPYPI_TIMEOUT=8m \
    CI_CONSUMER_TIMEOUT=5m \
    CI_RESOLVE_TIMEOUT=2m \
    CI_RELEASE_SMOKE_TIMEOUT=3m \
    CI_DOCKER_PUSH_TIMEOUT=5m

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates g++ coreutils curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# --- Pull request -----------------------------------------------------------------

FROM base AS version-check

ARG BASE_VERSION=
ENV BASE_VERSION=${BASE_VERSION}

COPY . .
RUN bash scripts/pull-request/version-check.sh

FROM base AS unit-test

COPY . .
RUN bash scripts/pull-request/unit-test.sh

FROM base AS testpypi

ARG CLI_RELEASE_VERSION=
ARG TESTPYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}

COPY . .
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
COPY config/config.yaml config/config.test.yaml config/drives.yaml /workspace/config/
COPY scripts/pull-request/testpypi-consumer.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/_smoke.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/integration-smoke.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/consumer /workspace/scripts/pull-request/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/pull-request/testpypi-consumer.sh

# --- Release ----------------------------------------------------------------------

FROM base AS pypi

ARG CLI_RELEASE_VERSION=
ARG PYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_API_TOKEN=${PYPI_API_TOKEN}

COPY . .
RUN bash scripts/release/pypi-release.sh

FROM python:3.12-slim AS runtime

ARG CLI_VERSION=
RUN test -n "${CLI_VERSION}"
RUN pip install --no-cache-dir "gardusig-cli==${CLI_VERSION}"

ENTRYPOINT ["cli"]
CMD ["--help"]
