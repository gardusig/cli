# Release — PyPI publish and runtime image (pip install from PyPI).
# docker build -f docker/release.dockerfile --target <stage> .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CI_DOCKER_BUILD_TIMEOUT=5m \
    CI_TESTPYPI_TIMEOUT=5m \
    CI_RESOLVE_TIMEOUT=2m \
    CI_RELEASE_SMOKE_TIMEOUT=3m \
    CI_DOCKER_PUSH_TIMEOUT=5m

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates g++ coreutils curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

FROM base AS pypi

ARG CLI_RELEASE_VERSION=
ARG PYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_API_TOKEN=${PYPI_API_TOKEN}

COPY pyproject.toml README.md LICENSE ./
COPY scripts/_common.sh scripts/_common.sh
COPY scripts/release/pypi-release.sh scripts/release/pypi-release.sh
COPY src src
RUN bash scripts/release/pypi-release.sh

FROM python:3.12-slim AS runtime

ARG CLI_VERSION=
RUN test -n "${CLI_VERSION}"
RUN pip install --no-cache-dir "gardusig-cli==${CLI_VERSION}"

ENTRYPOINT ["cli"]
CMD ["--help"]
