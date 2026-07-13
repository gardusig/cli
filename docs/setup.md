# Setup

## Install

```bash
pip install gardusig-cli
# or from clone:
pip install -e .
```

## Configure

```bash
cp -r config ~/.config/cli   # or set CLI_CONFIG_DIR to the clone config/
cli configure list
cli configure set notion.token --stdin
```

## Verify

```bash
cli --help
cli git --help
cli test python unit . --dry-run
```

See [install.md](install.md) and [configuration.md](configuration.md).
