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

Local host test scripts are not supported. CI and maintainers use Docker stages from `gardusig/github-pipelines`.

From a `python-cli` checkout:

```bash
docker build --target unit-test \
  -f ../github-pipelines/docker/python-cli.dockerfile \
  --ignorefile ../github-pipelines/docker/python-cli.dockerignore \
  .
```

`python-cli` is the only repo whose Docker PR stages install from the source checkout; every other repo installs `gardusig-cli` from PyPI.

## Release

Maintainers publish the package with:

```bash
cli configure import-env
cli pypi upload --yes
```

Pipelines consume the latest published package via `pip install gardusig-cli`.
