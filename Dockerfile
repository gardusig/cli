# gardusig-cli — Docker pipeline targets (local + GitHub Actions).
#
# Test:    ./scripts/test/all.sh
# Deploy:  ./scripts/deploy/deploy.sh
# Release: ./scripts/release/build.sh && ./scripts/release/publish.sh
#
# Targets: version | unit (2m) | integration (8m) | pypi-test | deploy | release | pypi-publish

FROM python:3.12-slim AS python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates tar zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/cli

COPY pyproject.toml README.md requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY src ./src
RUN pip install --no-cache-dir -e .

# -----------------------------------------------------------------------------
# version — PR version bump check (repo mounted at /repo)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS version

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/docker/run-version.sh /usr/local/bin/run-version.sh
COPY scripts/ci/version-check.sh /repo/scripts/ci/version-check.sh
RUN chmod +x /usr/local/bin/run-version.sh /repo/scripts/ci/version-check.sh
WORKDIR /repo
CMD ["run-version.sh"]

# -----------------------------------------------------------------------------
# unit — pytest unit + coverage (2 minute timeout on host)
# -----------------------------------------------------------------------------
FROM python AS unit

WORKDIR /app
COPY . .
ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_CONFIG_DIR=/app/config/ci
RUN chmod +x scripts/docker/run-unit.sh scripts/docker/bootstrap.sh
CMD ["./scripts/docker/run-unit.sh"]

# -----------------------------------------------------------------------------
# integration — full pytest + smoke + live docker (8 minute timeout)
# -----------------------------------------------------------------------------
FROM python AS integration

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

WORKDIR /app
COPY . .
ENV CLI_DOCKER_INTEGRATION=1 \
    CLI_CONFIG_DIR=/app/config/ci
RUN chmod +x scripts/docker/run-integration.sh scripts/docker/bootstrap.sh scripts/test/smoke.sh
CMD ["./scripts/docker/run-integration.sh"]

# -----------------------------------------------------------------------------
# pypi-test — packaging smoke (after integration)
# -----------------------------------------------------------------------------
FROM integration AS pypi-test

RUN chmod +x scripts/docker/run-pypi-test.sh scripts/pypi/*.sh
CMD ["./scripts/docker/run-pypi-test.sh"]

# -----------------------------------------------------------------------------
# regression — pack + workflow checks (third PR gate)
# -----------------------------------------------------------------------------
FROM integration AS regression

RUN chmod +x scripts/docker/run-regression.sh
CMD ["./scripts/docker/run-regression.sh"]

# -----------------------------------------------------------------------------
# deploy — tag main on push (repo mounted at /repo)
# -----------------------------------------------------------------------------
FROM python AS deploy

COPY scripts/docker/run-deploy.sh /usr/local/bin/run-deploy.sh
RUN chmod +x /usr/local/bin/run-deploy.sh
WORKDIR /repo
CMD ["run-deploy.sh"]

# -----------------------------------------------------------------------------
# release — build wheel/sdist into /artifacts
# -----------------------------------------------------------------------------
FROM python AS release

COPY scripts/docker/run-release-artifacts.sh /usr/local/bin/run-release-artifacts.sh
COPY scripts/pypi/ /repo/scripts/pypi/
RUN chmod +x /usr/local/bin/run-release-artifacts.sh /repo/scripts/pypi/*.sh
WORKDIR /repo
CMD ["run-release-artifacts.sh"]

# -----------------------------------------------------------------------------
# pypi-publish — upload to PyPI on v* tag (repo mounted at /repo)
# -----------------------------------------------------------------------------
FROM python AS pypi-publish

COPY scripts/docker/run-pypi-publish.sh /usr/local/bin/run-pypi-publish.sh
COPY scripts/pypi/ /repo/scripts/pypi/
COPY scripts/docker/run-release.sh /repo/scripts/docker/run-release.sh
RUN chmod +x /usr/local/bin/run-pypi-publish.sh /repo/scripts/pypi/*.sh /repo/scripts/docker/run-release.sh
WORKDIR /repo
CMD ["run-pypi-publish.sh"]

# -----------------------------------------------------------------------------
# contest — C++/Python contest runner (optional)
# -----------------------------------------------------------------------------
FROM python AS contest

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["bash"]

# -----------------------------------------------------------------------------
# runner — lean CI/local shuttle (git, gh, gardusig-cli; opencode optional at runtime)
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash git ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
         | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
         > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/cli
COPY pyproject.toml README.md requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY src ./src
RUN pip install --no-cache-dir -e .

WORKDIR /repo
ENTRYPOINT ["cli"]
CMD ["--help"]
