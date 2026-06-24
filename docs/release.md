# Release to PyPI

Production releases publish **`gardusig-cli`** to [PyPI](https://pypi.org/project/gardusig-cli/). The console command stays **`cli`**.

## One entrypoint

Everything goes through **`./scripts/release.sh`** — locally and in GitHub Actions ([`release.yml`](../.github/workflows/release.yml)).

That script:

1. Resolves the version from `GITHUB_REF_NAME` (CI), `CLI_RELEASE_VERSION`, or the current `v*` git tag
2. Builds the **`cli:release`** Docker image (`Dockerfile` target `release` — Python 3.12, `build`, `twine`, project deps)
3. Copies the repo into an isolated container workdir (read-only mount; no host `.env`)
4. Runs [`scripts/docker/run-release.sh`](../scripts/docker/run-release.sh) → [`scripts/pypi/release.sh`](../scripts/pypi/release.sh) → `cli pypi upload`
5. Confirms the version appears on the [PyPI project page](https://pypi.org/project/gardusig-cli/) (JSON API) before finishing

## GitHub Actions

Push an annotated tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Workflow [`.github/workflows/release.yml`](../.github/workflows/release.yml) only checks out the repo and runs:

```bash
./scripts/release.sh
```

| Secret | Required |
| --- | --- |
| `PYPI_API_TOKEN` | Yes — PyPI API token with upload scope |

Tag `v1.2.3` publishes version **`1.2.3`** (leading `v` stripped).

## Local release (same as CI)

```bash
export PYPI_API_TOKEN='pypi-...'   # or add to .env (not copied into the container; export on host)
./scripts/release.sh
```

From an exact tag checkout:

```bash
git checkout v1.0.0
export PYPI_API_TOKEN='pypi-...'
./scripts/release.sh
```

Override version without a tag:

```bash
CLI_RELEASE_VERSION=1.0.0 ./scripts/release.sh
```

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine). First run builds `cli:release`; set `CLI_DOCKER_SKIP_BUILD=1` if the image already exists.

## Lower-level scripts

| Script | Role |
| --- | --- |
| [`scripts/release.sh`](../scripts/release.sh) | **Canonical** — Docker wrapper (local + CI) |
| [`scripts/docker/run-release.sh`](../scripts/docker/run-release.sh) | In-container bootstrap + `pypi/release.sh` |
| [`scripts/pypi/release.sh`](../scripts/pypi/release.sh) | Version resolve + `upload.sh` |
| [`scripts/pypi/upload.sh`](../scripts/pypi/upload.sh) | `cli pypi upload --yes` |
| [`scripts/pypi/build.sh`](../scripts/pypi/build.sh) | Build only |
| [`scripts/release-pypi.sh`](../scripts/release-pypi.sh) | Deprecated → `scripts/release.sh` |

## TestPyPI (pull requests)

PR CI uses [`scripts/test-pypi.sh`](../scripts/test-pypi.sh) (integration image, version `1.0.0`, optional `TESTPYPI_API_TOKEN`). That is separate from production release.

## Checklist

- [ ] `PYPI_API_TOKEN` in GitHub repo secrets
- [ ] `./scripts/test-unit.sh` and `./scripts/test-integration.sh` green on `main`
- [ ] Tag `vX.Y.Z` on the commit you want to ship
- [ ] `git push origin vX.Y.Z` — watch **release** workflow on GitHub Actions
