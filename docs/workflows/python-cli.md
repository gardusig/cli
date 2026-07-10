# python-cli

`gardusig/python-cli` owns reusable shortcut commands. It does not own workflow policy.

## Pull request

- `repo-lint`: aggregate language lint via `cli lint repo`
- `repo-hygiene`: structure and root allowlist gate
- `unit-test`: `cli test python unit`
- `pypi-test`: build and publish the PR candidate to TestPyPI
- `testpypi-consumer`: install `gardusig-cli` from TestPyPI without source checkout and run smoke checks

## Repo review

Manual `repo-review.yml` jobs:

- `version-check`
- `version-suggest`
- `command-surface`

All jobs run as Docker targets from the CLI repo's root `Dockerfile`.

## CLI workflows

Separate CLI workflow definitions should live under `.github/workflows/cli/python-cli/`. They target the CLI repo itself, but the workflow files and secrets remain in `gardusig/cli`.

| Workflow | Command sequence | Purpose |
| --- | --- | --- |
| `python-cli-repo-hygiene` | repo hygiene target | Ensure app-local workflow/Docker orchestration has not leaked into `python-cli` |
| `python-cli-unit-test` | unit-test Docker target | Fast package and command tests |
| `python-cli-pypi-test` | pypi-test Docker target | Build/package validation and optional TestPyPI path |
| `python-cli-release-pypi` | release Docker target | Publish release artifacts using pipeline-owned PyPI secrets |
| `python-cli-version-check` | `cli pypi version check` | Compare package version against `origin/main` |
| `python-cli-version-suggest` | `cli pypi version suggest` | Suggest the next package version |
| `python-cli-command-surface` | public command surface check | Keep docs, command registration, and public CLI shape aligned |
| `python-cli-pipeline-dispatch-smoke` | `cli pipeline run ... --dry-run` | Verify dispatch payloads for known centralized workflows |

## Integrated release lane

`.github/workflows/python-cli-main-release.yml` is the end-to-end main release workflow:

1. Check out `gardusig/python-cli` at `main` or the requested ref.
2. Run `cli release main --yes` to tag, publish PyPI, verify, and create the GitHub release.
3. Build `docker/cli-base.dockerfile` with `gardusig-cli==<released-version>`.

## Command contract lane

`python-cli-command-contract` groups command-surface checks that protect downstream workflows:

1. Verify public command registration.
2. Check docs and links for renamed commands.
3. Smoke `cli pipeline run ... --dry-run` against `database` and `python-cli` workflow targets.
