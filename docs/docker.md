# Docker

Workflow routers live in [`gardusig/cli`](https://github.com/gardusig/cli). This repo owns the root `Dockerfile`, `.dockerignore`, `scripts/pull-request/`, `scripts/release/`, the `cli docker` monitor/cleanup commands, and pipeline contracts under [`.github/workflows/`](../.github/workflows/).

Run a gate from the repo root:

```bash
docker build --target <stage> .
```

Common PR targets: `version-check`, `unit-test`, `testpypi`, `testpypi-consumer`.

Release targets: `pypi`, `runtime`.

## CI image layout

Each Dockerfile stage copies the repo (or consumer scripts only) and runs stage scripts under `scripts/pull-request/` or `scripts/release/`. Local verification:

```bash
docker build --target unit-test .
```

## CLI base image (hub)

`gardusig/cli` may publish a lean hub image for jobs that run pip-installed `gardusig-cli` shortcuts. Language repos use their own `Dockerfile` bases.

## Docker CLI Commands

`cli docker` is monitor/cleanup only. It does not start containers, run services, or invoke compose.

### Command matrix

Public `cli docker` acceptance checklist. Integration gate exercises JSON and filter rows in `docker_integration.py`.

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

`cli contest validate` uses the `cli-contest:runner` image for Docker-backed competitive programming checks. The image build recipe belongs to the CI hub; this repo documents and monitors it.

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
