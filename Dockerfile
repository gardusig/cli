# CI for gardusig/github-pipelines — lint → structure
FROM python:3.12-slim AS lint

ENV PUPPETEER_SKIP_DOWNLOAD=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        chromium \
        ca-certificates \
        git \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g markdownlint-cli2 @mermaid-js/mermaid-cli \
    && pip install --no-cache-dir "gardusig-cli @ git+https://github.com/gardusig/python-cli@main"

RUN printf '%s\n' \
      '{"executablePath":"/usr/bin/chromium","args":["--no-sandbox","--disable-setuid-sandbox"]}' \
      > /usr/local/share/puppeteer-no-sandbox.json

WORKDIR /workspace
COPY . .
RUN cli lint repo /workspace

FROM python:3.12-slim AS repo-hygiene

ARG HYGIENE_POLICY_JSON=

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "gardusig-cli @ git+https://github.com/gardusig/python-cli@main"

WORKDIR /workspace
COPY . .

RUN if [ -n "$HYGIENE_POLICY_JSON" ]; then \
      printf '%s' "$HYGIENE_POLICY_JSON" > /tmp/hygiene-policy.json; \
      cli structure check /workspace --require-structure --policy-file /tmp/hygiene-policy.json; \
    else \
      cli structure check /workspace --require-structure; \
    fi
