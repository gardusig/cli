# Multi-stage CI for gardusig/cli (app context = repo root).
# Build: docker build -f .github/Dockerfile --target <stage> .
# Stage entrypoints: scripts/ci/<stage>.sh (raw shell — independent from cli package).

# -----------------------------------------------------------------------------
# lint — markdown + mermaid validation
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS lint

ENV PUPPETEER_SKIP_DOWNLOAD=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLI_LINT_MERMAID=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates chromium chromium-common \
        fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
        libcups2 libdrm2 libgbm1 libgtk-3-0 libnss3 libxcomposite1 \
        libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
        curl gnupg git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g markdownlint-cli2 @mermaid-js/mermaid-cli \
    && rm -rf /var/lib/apt/lists/*

RUN printf '%s\n' \
      '{"executablePath":"/usr/bin/chromium","args":["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu","--headless","--single-process","--no-zygote"]}' \
      > /usr/local/share/puppeteer-no-sandbox.json

WORKDIR /workspace
COPY . .
RUN bash scripts/ci/lint.sh

# -----------------------------------------------------------------------------
# base — Python runtime + dev dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates tar zip g++ coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# -----------------------------------------------------------------------------
# integration — Docker CLI for socket tests
# -----------------------------------------------------------------------------
FROM base AS integration

ARG DOCKER_CLI_VERSION=27.3.1
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && case "$(uname -m)" in \
         x86_64) docker_arch=x86_64 ;; \
         aarch64) docker_arch=aarch64 ;; \
         *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${docker_arch}/docker-${DOCKER_CLI_VERSION}.tgz" \
         | tar xz -C /usr/local/bin --strip-components=1 docker/docker \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# core-gates
# -----------------------------------------------------------------------------
FROM integration AS core-gates

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .
RUN bash scripts/ci/core-gates.sh

# -----------------------------------------------------------------------------
# package-unit
# -----------------------------------------------------------------------------
FROM base AS package-unit

ARG PACKAGE=cli
ENV PACKAGE=${PACKAGE}

COPY . .
RUN bash scripts/ci/package-unit.sh

# -----------------------------------------------------------------------------
# package-integration
# -----------------------------------------------------------------------------
FROM integration AS package-integration

ARG PACKAGE=cli
ENV PACKAGE=${PACKAGE}

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .
RUN bash scripts/ci/package-integration.sh

CMD ["python3", "tests/integration/check_docker_commands.py", "--live"]

# -----------------------------------------------------------------------------
# selective-gate
# -----------------------------------------------------------------------------
FROM base AS selective-gate

COPY scripts/ci/selective-gate.sh scripts/ci/_common.sh /workspace/scripts/ci/
RUN bash /workspace/scripts/ci/selective-gate.sh

# -----------------------------------------------------------------------------
# unit-test
# -----------------------------------------------------------------------------
FROM base AS unit-test

COPY . .
RUN bash scripts/ci/unit-test.sh

# -----------------------------------------------------------------------------
# repo-hygiene
# -----------------------------------------------------------------------------
FROM base AS repo-hygiene

ARG HYGIENE_POLICY_JSON=
ENV HYGIENE_POLICY_JSON=${HYGIENE_POLICY_JSON}

COPY . .
RUN bash scripts/ci/repo-hygiene.sh

# -----------------------------------------------------------------------------
# workspace-paths — reusable workspace manifest validator
# -----------------------------------------------------------------------------
FROM base AS workspace-paths

COPY . .
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python3", "tests/meta/hygiene_gate.py"]

# -----------------------------------------------------------------------------
# version-check
# -----------------------------------------------------------------------------
FROM base AS version-check

ARG BASE_VERSION=
ENV BASE_VERSION=${BASE_VERSION}

COPY . .
RUN bash scripts/ci/version-check.sh

# -----------------------------------------------------------------------------
# version-suggest
# -----------------------------------------------------------------------------
FROM base AS version-suggest

COPY . .
RUN bash scripts/ci/version-suggest.sh

# -----------------------------------------------------------------------------
# command-surface
# -----------------------------------------------------------------------------
FROM base AS command-surface

COPY . .
RUN bash scripts/ci/command-surface.sh

# -----------------------------------------------------------------------------
# integration-test
# -----------------------------------------------------------------------------
FROM integration AS integration-test

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .
RUN bash scripts/ci/integration-test.sh

CMD ["python3", "tests/integration/check_docker_commands.py", "--live"]

# -----------------------------------------------------------------------------
# pypi-test — build + optional TestPyPI upload
# -----------------------------------------------------------------------------
FROM base AS pypi-test

ARG CLI_RELEASE_VERSION=
ARG TESTPYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}

COPY . .
RUN bash scripts/ci/pypi-test.sh

# -----------------------------------------------------------------------------
# pr — version gate + unit (≥80%) + TestPyPI (single build)
# -----------------------------------------------------------------------------
FROM base AS pr

ARG CLI_RELEASE_VERSION=
ARG BASE_VERSION=
ARG TESTPYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    BASE_VERSION=${BASE_VERSION} \
    TESTPYPI_API_TOKEN=${TESTPYPI_API_TOKEN}

COPY . .
RUN bash scripts/ci/pr.sh

# -----------------------------------------------------------------------------
# testpypi-consumer — install from TestPyPI + consumer integration
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS testpypi-consumer

ARG CLI_RELEASE_VERSION=
ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_INDEX=testpypi

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY scripts/ci/testpypi-consumer.sh /workspace/scripts/ci/
COPY scripts/ci/consumer /workspace/scripts/ci/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/ci/testpypi-consumer.sh

# -----------------------------------------------------------------------------
# testpypi-verify — install from TestPyPI → consumer smoke → integration
# -----------------------------------------------------------------------------
FROM integration AS testpypi-verify

ARG CLI_RELEASE_VERSION=
ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_INDEX=testpypi \
    CLI_DOCKER_INTEGRATION=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt requirements-dev.txt pyproject.toml ./
COPY tests ./tests
COPY config/ci ./config/ci
COPY scripts/ci/testpypi-verify.sh scripts/ci/testpypi-integration.sh \
  scripts/ci/_common.sh \
  ./scripts/ci/
COPY scripts/ci/consumer ./scripts/ci/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/ci/testpypi-verify.sh

# -----------------------------------------------------------------------------
# release — production PyPI publish
# -----------------------------------------------------------------------------
FROM base AS release

ARG CLI_RELEASE_VERSION=
ARG PYPI_API_TOKEN=

ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_API_TOKEN=${PYPI_API_TOKEN}

COPY . .
RUN bash scripts/ci/pypi-release.sh

# -----------------------------------------------------------------------------
# pypi-consumer — install from PyPI + consumer integration
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS pypi-consumer

ARG CLI_RELEASE_VERSION=
ENV CLI_RELEASE_VERSION=${CLI_RELEASE_VERSION} \
    PYPI_INDEX=pypi

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY scripts/ci/pypi-consumer.sh /workspace/scripts/ci/
COPY scripts/ci/consumer /workspace/scripts/ci/consumer
RUN CLI_RELEASE_VERSION="${CLI_RELEASE_VERSION}" bash scripts/ci/pypi-consumer.sh
