# Docker

Docker orchestration lives in `gardusig/github-pipelines`. This repo owns only the `cli docker` monitor and cleanup commands.

App repos do not own Dockerfiles, compose files, workflow YAML, or Docker helper scripts. To run a gate, build the relevant pipeline Dockerfile from the app repo root:

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

The exception is `python-cli.dockerfile`, which lives in `github-pipelines` and installs the PR checkout with `pip install -e ".[dev]"` so unreleased CLI changes can be tested before publishing.

## CLI Base Image

`github-pipelines/docker/cli-base.dockerfile` is the lean Linux image for workflow jobs that mostly run `gardusig-cli` shortcuts. It starts from Python, installs common orchestration tools, and installs `gardusig-cli` from PyPI.

Language-focused checks still use repo Dockerfiles based on Node, Java, Ubuntu, or other toolchain images when the repository needs those tools.

## Docker CLI Commands

`cli docker` is monitor/cleanup only. It does not start containers, run services, or invoke compose.

### Command matrix

Epic 12 ([#70](https://github.com/gardusig/python-cli/issues/70)) acceptance checklist. Integration gate exercises JSON and filter rows in `docker_integration.py`.

| Command | Read/Write | `--format json` | Filters | Write gate |
| --- | --- | --- | --- | --- |
| `ps` | read | yes | `--name`, `--filter` | — |
| `containers` | read | yes | `--name`, `--status`, `--filter`, `--running` | — |
| `images` | read | yes | `--repository`, `--filter` | — |
| `stats` | read | yes | `--name`, `--filter` | — |
| `top` | read | yes | `--name`, `--repository`, `--filter` | — |
| `df` | read | yes (`{"text":…}`) | — | — |
| `stop` | write | yes (`stopped`, `count`) | — | `--yes` |
| `container-delete` | write | yes (`deleted`, `count`) | — | `--yes` |
| `image-delete` | write | yes (`image_prune`, `all_images`) | — | `--yes` |
| `clean` | write | yes (per-target payload) | — | `--yes` |
| `reset` | write | yes (full summary object) | — | `--yes` |

Read-only commands:

| Command | Purpose |
| --- | --- |
| `cli docker ps` | Running containers sorted by writable layer size |
| `cli docker containers` | All containers sorted by on-disk size |
| `cli docker images` | Images sorted by size |
| `cli docker stats` | Top CPU, memory, or storage consumers |
| `cli docker top` | Dashboard across CPU, memory, container storage, and image storage |
| `cli docker df` | `docker system df` disk usage summary |

Cleanup commands require a write gate or `--yes`:

| Command | Purpose |
| --- | --- |
| `cli docker stop --yes` | Stop running containers |
| `cli docker container-delete --yes` | Remove containers with `docker rm -f` |
| `cli docker image-delete --yes` | Prune unused images |
| `cli docker clean containers --yes` | Remove containers only |
| `cli docker clean images --yes` | Prune images only |
| `cli docker clean cache --yes` | Prune build cache only |
| `cli docker clean all --yes` | Remove containers and prune images/cache |
| `cli docker reset --yes` | Stop all, remove all containers, prune images and cache |

## JSON Output

Read-only commands default to rich tables for humans. Use `--format json` for agents:

```bash
cli docker ps --format json
cli docker containers --status exited --format json
cli docker images --format json
cli docker stats --by all --format json
cli docker top --format json
cli docker df --format json
```

`df --format json` wraps the raw Docker text as `{"text": "..."}` because `docker system df` is not a stable structured API across installed Docker versions.

Write commands also accept `--format json` after a successful `--yes` run:

```bash
cli docker stop --yes --format json
cli docker container-delete web --yes --format json
cli docker reset --yes --format json
```

Example `stop` payload: `{"stopped": ["abc123"], "count": 1}`.

## Install vs verify

| Requirement | Read commands | Live integration |
| --- | --- | --- |
| `docker` on PATH | required | required |
| Docker daemon socket | required for real data | required (`check_docker_commands.py --live`) |

Mocked integration (`python tests/integration/check_docker_commands.py`) patches `run_docker` and does not need a daemon.

## Filters

Container commands accept Docker `ps` filters plus a convenience name filter:

```bash
cli docker ps --name cli --format json
cli docker containers --status exited --format json
cli docker stats --filter label=cli --format json
cli docker top --name cli --format json
```

Image commands accept Docker image filters plus a convenience repository/reference filter:

```bash
cli docker images --repository cli-contest:runner --format json
cli docker images --filter dangling=false --format json
cli docker top --repository cli-contest:runner --format json
```

Filters affect monitoring output only. Cleanup commands still require explicit names or write-gated broad cleanup.

## Contest Runner Lifecycle

`cli contest validate` uses the `cli-contest:runner` image for Docker-backed competitive programming checks. The image build recipe belongs to `github-pipelines`; `python-cli` documents and monitors it.

Useful read-only checks:

```bash
cli docker images --repository cli-contest:runner --format json
cli docker containers --name cli-contest --format json
cli docker stats --name cli-contest --format json
```

Use cleanup commands only after reviewing the write-gate preview:

```bash
cli docker container-delete cli-contest-runner --yes
cli docker image-delete --yes
```
