# Headless operator runner — gardusig-cli + git + gh + docker CLI.
# Build: docker build -f docker/operator.dockerfile --target operator-runner .
# Publish: .github/workflows/operator-runner-publish.yml

FROM python:3.12-slim AS operator-runner

ARG CLI_PACKAGE=gardusig-cli
ARG CLI_VERSION=
ARG DOCKER_CLI_VERSION=27.3.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WORKSPACE=/workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        gh \
    && case "$(uname -m)" in \
         x86_64) docker_arch=x86_64 ;; \
         aarch64) docker_arch=aarch64 ;; \
         *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${docker_arch}/docker-${DOCKER_CLI_VERSION}.tgz" \
         | tar xz -C /usr/local/bin --strip-components=1 docker/docker \
    && rm -rf /var/lib/apt/lists/* \
    && if [ -n "$CLI_VERSION" ]; then \
         pip install --no-cache-dir "${CLI_PACKAGE}==${CLI_VERSION}"; \
       else \
         pip install --no-cache-dir "$CLI_PACKAGE"; \
       fi

WORKDIR /workspace

CMD ["cli", "--version"]
