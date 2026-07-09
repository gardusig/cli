# Runtime image for gardusig-cli — installs from PyPI only (no repo source).
FROM python:3.12-slim

ARG CLI_VERSION=
RUN test -n "${CLI_VERSION}"
RUN pip install --no-cache-dir "gardusig-cli==${CLI_VERSION}"

ENTRYPOINT ["cli"]
CMD ["--help"]
