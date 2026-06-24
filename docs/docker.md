# Docker

## CLI shortcuts

Monitor and cleanup only (no `docker run` from cli):

| Command | Purpose |
| --- | --- |
| `cli docker top` | Dashboard: CPU, memory, and storage leaders |
| `cli docker stats --by cpu` | Top consumers by domain (`memory`, `storage`, `all`) |
| `cli docker ps` / `containers` / `images` / `df` | Lists and disk summary |
| `cli docker stop --yes` | Stop running containers |
| `cli docker container-delete --yes` | Remove containers |
| `cli docker image-delete --yes` | Prune unused images |
| `cli docker reset --yes` | Full wipe: stop, delete containers, prune images + cache |
| `cli docker clean TARGET --yes` | Targeted: `containers`, `images`, `cache`, `all` |

Shell wrappers: `scripts/docker/` (`reset.sh`, `stop.sh`, `container-delete.sh`, `image-delete.sh`, `stats.sh`).

## Install vs verify

- **Install (host):** `./scripts/bootstrap.sh` / `./scripts/install.sh` — runtime deps only; use `cli` on macOS.
- **Verify (Docker):** everything in this document — pytest, coverage, smoke, public API checks, live docker.

Host `pytest` is intentionally unsupported. Dev dependencies (`pytest`, `pytest-cov`) install only inside the container copy (`CLI_BOOTSTRAP_DEV=1`) or in the pre-built image layer.

## Dev / test image

Issue [#9](https://github.com/gardusig/cli/issues/9) tracks Docker-based test and onboarding lanes.

Root [`Dockerfile`](../Dockerfile) (multi-stage): shared **python** base plus decorated targets.

```text
python:3.12-slim
       └── python          cli:python     requirements-dev.txt + editable install
            ├── unit       cli:unit       pytest / coverage
            ├── integration cli:integration (+ Docker CLI; alias cli:dev)
            └── contest    cli-contest:runner  (+ g++, coreutils)
```

| Target | Tag | Build | Purpose |
| --- | --- | --- | --- |
| `python` | `cli:python` | `./scripts/docker/build-image.sh` with `CLI_DOCKER_TARGET=python` | Shared Python + cli dev install |
| `unit` | `cli:unit` | `docker build --target unit` | Legacy stage (same base as integration; tests use `cli:integration`) |
| `integration` | `cli:integration` | `./scripts/test-unit.sh` / `./scripts/test-integration.sh` (auto) | Full pytest + smoke + live docker |
| `integration` | `cli:dev` | alias of integration | Backward-compatible dev/onboard tag |
| `contest` | `cli-contest:runner` | `./scripts/docker/build-contest-image.sh` | `cli contest validate` |

```bash
./scripts/docker/build-images.sh         # build all stages
./scripts/docker/build-image.sh          # one stage (CLI_DOCKER_TARGET)
./scripts/docker/build-contest-image.sh  # contest stage
./scripts/test-unit.sh                   # unit tests (CI gate)
./scripts/test-integration.sh            # integration pytest + smoke + live docker
./scripts/docker/shell.sh                # onboard: interactive shell
```

Build one stage manually:

```bash
docker build --target unit -t cli:unit .
docker build --target integration -t cli:integration .
docker build --target contest -t cli-contest:runner .
```

Build context is always the **repository root**.

Host repo is mounted read-only; each run copies a fresh tree to `/tmp/cli` (see `scripts/docker/common.sh`). Integration tests mount `/var/run/docker.sock` so live `cli docker` checks run against your host daemon without a host Python venv.

## CI (GitHub Actions)

| Workflow | Trigger | What runs |
| --- | --- | --- |
| [`test`](../.github/workflows/test.yml) | **Pull requests** | Unit + integration Docker gates |
| [`release`](../.github/workflows/release.yml) | **Tags** `v*` | PyPI publish |

See [`.github/README.md`](../.github/README.md) for required secrets.

On `main`, require both PR status checks in **Settings → Branches → Branch protection** (no workflow — configure manually in GitHub).

## Run tests

```bash
./scripts/docker/build-image.sh   # optional; skipped when image already exists
./scripts/test-unit.sh            # full pytest + coverage gate
./scripts/test-integration.sh     # full integration gate
```

The runner:

1. Builds root `Dockerfile` with target `unit` or `integration` (or uses `CLI_DOCKER_SKIP_BUILD=1` with a pre-built tag).
2. Mounts the repository read-only at `/workspace/src`.
3. Copies the repo into `/tmp/cli` inside the container, excluding `.git`, `.venv`, and cache directories.
4. Initializes a disposable git repo, bootstraps a venv inside the copy, then runs the test gate.

Because tests run from the copied tree in `/tmp`, commands like `cli git start` and bookmark export fixtures cannot mutate your host checkout.

## Smoke coverage

The container smoke test checks:

- `tests/integration/check_public_endpoints.py` — every public CLI command (56 checks): read-only paths, write-gate refusals, and `--yes` success paths with **remote git mocked** (`fetch` / `push` / `ls-remote` never hit the network)
- `python -m cli --help` and `--version`
- placeholder endpoints: `restore`, `drive`, `notion`, `chrome`
- shell syntax for `scripts/chrome`, `scripts/git`, and root smoke scripts
- Chrome bookmark export/import using local fixture files and `CLI_SKIP_CHROME_AUTOMATION=1`
- `cli git start` inside a temporary git repository
