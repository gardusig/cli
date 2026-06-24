# Multi-stage images: python base + decorated targets (unit, integration, contest).
# Build: docker build --target <stage> -t <tag> .

# -----------------------------------------------------------------------------
# python — cli runtime + dev deps (shared foundation)
# -----------------------------------------------------------------------------
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

COPY cli ./cli
RUN pip install --no-cache-dir -e .

# -----------------------------------------------------------------------------
# release — PyPI publish (build + twine; same image base as unit)
# -----------------------------------------------------------------------------
FROM python AS release

WORKDIR /workspace
CMD ["bash"]

# -----------------------------------------------------------------------------
# unit — pytest / coverage (no Docker CLI)
# -----------------------------------------------------------------------------
FROM python AS unit

WORKDIR /workspace
CMD ["bash"]

# -----------------------------------------------------------------------------
# integration — host Docker socket checks (Docker CLI static binary)
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

WORKDIR /workspace
CMD ["bash"]

# -----------------------------------------------------------------------------
# contest — compile/run C++ and Python solutions (g++, timeout)
# -----------------------------------------------------------------------------
FROM python AS contest

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["bash"]
