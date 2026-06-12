# shuttle-cli

macOS CLI for **git shortcuts** (deterministic, no AI) and future backup/sync workflows.

## Quickstart (macOS)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
python -m shuttle --help
```

Optional install to `~/.local/bin`:

```bash
./scripts/install.sh
shuttle git --help
```

## Common git commands

| Task | Command |
| --- | --- |
| **Sync main** (before/after work) | `shuttle git reset --yes` (`--main-only` to skip branch prune) |
| **Start issue** (align main + branch) | `shuttle git start issue-9-slug --yes` |
| **During work** (add + commit + push) | `shuttle git push --yes` (on `main`, starts random branch first) |
| Branch in place (no align) | `shuttle git start [name] --no-prep` |
| Commit only | `shuttle git commit` |
| Sync feature branch | `shuttle git pull` |
| Delete merged branch | `shuttle git branch-delete BRANCH --yes` |
| Clear all branches (keep `main`) | `shuttle git branch-clear --yes` |
| Tag release | `shuttle git tag` (today's date) · `shuttle git zip TAG` |

Short alias: `shuttle g push --yes` == `shuttle git push --yes`.

Shell wrappers for every [cursor-skills git skill](https://github.com/gardusig/cursor-skills/tree/main/skills/git) live in `scripts/git/` (e.g. `./scripts/git/review.sh`).

**Safety:** destructive actions (reset, clean, delete, push) require `--yes` or an interactive confirmation. Default `shuttle git start` aligns main then branches; pass `--no-prep` to branch from the current state.

## Chrome bookmarks

```bash
./scripts/chrome/export-bookmarks.sh   # → data/bookmarks/bookmarks.html
./scripts/chrome/import-bookmarks.sh   # restore from backup
```

See [docs/bookmarks.md](docs/bookmarks.md).

## Docker

Local Docker monitor and cleanup (requires `docker` on PATH; no container start):

| Task | Command |
| --- | --- |
| **Dashboard** (CPU, memory, storage) | `shuttle docker top` |
| **By domain** | `shuttle docker stats --by cpu` / `memory` / `storage` |
| **Storage lists** | `shuttle docker images` · `shuttle docker containers` · `shuttle docker df` |
| **Stop running** | `shuttle docker stop --yes` |
| **Delete containers** | `shuttle docker container-delete --yes` |
| **Prune images** | `shuttle docker image-delete --yes` (`--all-images` for all unused) |
| **Full reset** | `shuttle docker reset --yes` |
| Targeted cleanup | `shuttle docker clean containers --yes` · `clean images` · `clean all` |

Shell wrappers live in `scripts/docker/` (e.g. `./scripts/docker/reset.sh --yes`).

Destructive commands use the write gate; pass `--yes` in scripts.

## Testing

```bash
./scripts/test-unit.sh          # unit tests + ≥80% coverage (matches CI macOS job)
./scripts/test-in-docker.sh     # full pytest + smoke inside a container
./scripts/test-integration.sh   # container smoke + live docker CLI on host
```

Mocked docker CLI checks (no daemon):

```bash
source .venv/bin/activate
python scripts/integration/check_docker_commands.py
```

## Docker integration (CI)

CI on every pull request runs:

- **Unit** (macOS): `./scripts/test-unit.sh`
- **Integration** (Ubuntu): container smoke via `./scripts/test-in-docker.sh`, then live `shuttle docker` against the host daemon

See [docs/docker.md](docs/docker.md).

## Docs

- [Setup](docs/setup.md)
- [Git commands](docs/git.md)
- [Chrome bookmarks](docs/bookmarks.md)
- [Docker integration](docs/docker.md)
- [Configuration](docs/configuration.md)
- [Architecture](docs/architecture.md)

## Related

- [cursor-skills](https://github.com/gardusig/cursor-skills) — `@gh-*` AI workflows for issues/PRs
- Bootstrap spec: [shuttle-cli #3](https://github.com/gardusig/shuttle-cli/issues/3)
- Bookmarks: [shuttle-cli #1](https://github.com/gardusig/shuttle-cli/issues/1)
- Docker integration: [shuttle-cli #9](https://github.com/gardusig/shuttle-cli/issues/9)
