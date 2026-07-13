# Pull-request CI — version gate, unit tests, TestPyPI publish, consumer integration
# Build: docker build -f docker/pull-request.dockerfile --target <stage> .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates g++ coreutils curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

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
    PYPI_INDEX=testpypi

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY scripts/pull-request/testpypi-consumer.sh /workspace/scripts/pull-request/
COPY scripts/pull-request/consumer /workspace/scripts/pull-request/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/pull-request/testpypi-consumer.sh
