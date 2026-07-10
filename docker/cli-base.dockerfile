# Lean CLI runtime for workflow jobs that mostly run gardusig-cli shortcuts.
#
# Language-specific repositories should still use their own focused Dockerfiles
# when they need Node, Java, C++, browser, or other toolchains.

FROM python:3.12-slim AS cli-base

ARG CLI_PACKAGE=gardusig-cli

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        gh \
    && rm -rf /var/lib/apt/lists/* \
    && case "$(uname -m)" in \
         x86_64) docker_arch=x86_64 ;; \
         aarch64) docker_arch=aarch64 ;; \
         *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${docker_arch}/docker-27.3.1.tgz" \
         | tar xz -C /usr/local/bin --strip-components=1 docker/docker \
    && pip install --no-cache-dir "$CLI_PACKAGE"

CMD ["cli", "--help"]

