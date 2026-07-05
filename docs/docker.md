# Docker

Docker orchestration lives in `gardusig/github-pipelines`.

App repos do not own Dockerfiles or Docker helper scripts. To run a gate, build the relevant pipeline Dockerfile from the app repo root.

```bash
docker build --target <target> \
  -f ../github-pipelines/docker/<repo>.dockerfile \
  .
```

## CLI Inside Docker

Pipeline images install the published CLI package:

```dockerfile
RUN pip install --no-cache-dir gardusig-cli \
    && cli configure import-env \
    && cli structure check /workspace
```

The exception is `python-cli.dockerfile`, which installs the PR checkout with `pip install -e ".[dev]"` so unreleased CLI changes can be tested before publishing.

## CLI Base Image

`github-pipelines/docker/cli-base.dockerfile` is the lean Linux image for
workflow jobs that mostly run `gardusig-cli` shortcuts. It starts from Python,
installs common orchestration tools, and installs `gardusig-cli` from PyPI.

Language-focused checks still use repo Dockerfiles based on Node, Java, Ubuntu,
or other toolchain images when the repository needs those tools.

## Docker CLI Commands

`cli docker` is for monitoring and cleanup only:

| Command | Purpose |
|---------|---------|
| `cli docker top` | Resource dashboard |
| `cli docker stats` | Top resource consumers |
| `cli docker stop --yes` | Stop running containers |
| `cli docker image-delete --yes` | Prune unused images |
| `cli docker reset --yes` | Stop containers and prune Docker cache |

No `src/scripts/docker/` wrappers are required.
