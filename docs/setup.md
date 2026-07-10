# Setup

Install the CLI from PyPI, then configure it.

```bash
pip install gardusig-cli
cli --version
cli configure list
```

The package name is `gardusig-cli`; the command is `cli`.

## Configuration

Use `cli configure` for all paths, API tokens, and service defaults.

```bash
cli configure set notion.token secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
cli configure set gh.token --stdin
cli configure import-env
cli configure check --tasks
```

See `docs/configure.md` and `docs/secrets.md`.

## Verification

Local host test scripts are not supported. CI and maintainers use Docker stages from `.github/Dockerfile`.

From a `gardusig/cli` checkout:

```bash
docker build -f .github/Dockerfile --target unit-test .
```

`.github/Dockerfile` installs from the source checkout with `pip install -e ".[dev]"`; other app repos install `gardusig-cli` from PyPI in their own Dockerfiles.

## Release

Maintainers publish the package with:

```bash
cli configure import-env
cli release main --yes
```

`cli pypi upload --yes` remains the lower-level upload command. Workflow routers, hub-only images (`operator`, `cli-base`), schedules, and secrets live in [`gardusig/cli`](https://github.com/gardusig/cli).
