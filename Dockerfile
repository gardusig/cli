# Multi-stage CI for gardusig/cli (app context = repo root).
# Build: docker build --target <stage> -f Dockerfile .

# -----------------------------------------------------------------------------
# lint — markdown + mermaid validation (first stage)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS lint

ENV PUPPETEER_SKIP_DOWNLOAD=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
RUN pip install --no-cache-dir -e . \
    && CLI_LINT_MERMAID=0 cli lint repo /workspace

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
# integration — Docker CLI for socket tests (must precede stages that FROM integration)
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
# core-gates — integration coverage + public command surface
# -----------------------------------------------------------------------------
FROM integration AS core-gates

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && python3 tests/integration/check_integration_coverage.py \
    && python3 tests/integration/check_public_commands.py

# -----------------------------------------------------------------------------
# package-unit — focused pytest for one CLI package
# -----------------------------------------------------------------------------
FROM base AS package-unit

ARG PACKAGE=cli

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli test packages run "${PACKAGE}" --no-integration

# -----------------------------------------------------------------------------
# package-integration — focused integration leg for one CLI package
# -----------------------------------------------------------------------------
FROM integration AS package-integration

ARG PACKAGE=cli

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli test packages run "${PACKAGE}" --no-unit

CMD ["python", "tests/integration/check_docker_commands.py", "--live"]

# -----------------------------------------------------------------------------
# selective-gate — no-op marker after selective package legs
# -----------------------------------------------------------------------------
FROM base AS selective-gate

RUN echo "selective tests complete"

# -----------------------------------------------------------------------------
# unit-test — pytest unit gate + coverage
# -----------------------------------------------------------------------------
FROM base AS unit-test

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli test python unit /workspace

# -----------------------------------------------------------------------------
# repo-hygiene — repository layout and language allowlists
# -----------------------------------------------------------------------------
FROM base AS repo-hygiene

ARG HYGIENE_POLICY_JSON=

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && if [ -n "$HYGIENE_POLICY_JSON" ]; then \
         printf '%s' "$HYGIENE_POLICY_JSON" > /tmp/hygiene-policy.json; \
         cli structure check /workspace --require-structure --policy-file /tmp/hygiene-policy.json; \
       else \
         cli structure check /workspace --require-structure; \
       fi

# -----------------------------------------------------------------------------
# version-check — fail if branch version is not greater than main
# -----------------------------------------------------------------------------
FROM base AS version-check

ARG BASE_VERSION=
COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && if [ -n "$BASE_VERSION" ]; then \
         cli pypi version check --base-version "$BASE_VERSION"; \
       else \
         (git fetch origin main 2>/dev/null || true) \
         && cli pypi version check --base origin/main; \
       fi

# -----------------------------------------------------------------------------
# version-suggest — print recommended next semver
# -----------------------------------------------------------------------------
FROM base AS version-suggest

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli pypi version suggest

# -----------------------------------------------------------------------------
# command-surface — registered commands stay covered by public command checks
# -----------------------------------------------------------------------------
FROM base AS command-surface

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli test python command-surface /workspace

# -----------------------------------------------------------------------------
# integration-test — full pytest + smoke (live docker via docker run + socket)
# -----------------------------------------------------------------------------
FROM integration AS integration-test

ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_ROOT=/workspace \
    CLI_CONFIG_DIR=/workspace/config/ci

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli test python integration /workspace \
    && python -m src --help >/dev/null \
    && python -m src --version >/dev/null

# Live docker socket checks — workflow runs: docker run -v /var/run/docker.sock ...
CMD ["python", "tests/integration/check_docker_commands.py", "--live"]

# -----------------------------------------------------------------------------
# pypi-test — build + optional TestPyPI upload
# -----------------------------------------------------------------------------
FROM base AS pypi-test

ARG CLI_RELEASE_VERSION=1.0.0
ARG TESTPYPI_API_TOKEN=

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && cli pypi upload --yes --version "${CLI_RELEASE_VERSION}" --build-only \
    && if [ -n "$TESTPYPI_API_TOKEN" ]; then \
         cli pypi upload --yes --version "${CLI_RELEASE_VERSION}" --testpypi --skip-build --skip-existing; \
       else \
         echo "skip TestPyPI upload (TESTPYPI_API_TOKEN not set)"; \
       fi

# -----------------------------------------------------------------------------
# testpypi-consumer — install published candidate without source checkout
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS testpypi-consumer

ARG CLI_RELEASE_VERSION=1.0.0

RUN pip install --no-cache-dir \
      --index-url https://test.pypi.org/simple/ \
      --extra-index-url https://pypi.org/simple/ \
      "gardusig-cli==${CLI_RELEASE_VERSION}" \
    && cli --help >/dev/null \
    && cli languages list >/dev/null \
    && cli lint --help >/dev/null

# -----------------------------------------------------------------------------
# release — PyPI publish
# -----------------------------------------------------------------------------
FROM base AS release

ARG CLI_RELEASE_VERSION
ARG PYPI_API_TOKEN

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt \
    && pip install --no-cache-dir -e ".[dev]" \
    && test -n "$CLI_RELEASE_VERSION" \
    && test -n "$PYPI_API_TOKEN" \
    && cli pypi upload --yes --version "${CLI_RELEASE_VERSION}"
