# Configuration layout

## Runtime (installed CLI)

Out of the box the CLI uses **code defaults only** — no config file required until you opt in.

| Step | Command |
| --- | --- |
| Bootstrap storage | `cli configure init` |
| Set a path or token | `cli configure set notion.task_root ~/tasks` |
| Set a secret | `cli configure set notion.token --stdin` |
| Inspect keys | `cli configure list` |
| Show config dir | `cli configure path` |

User config lives at the **OS-standard path** (`platformdirs`):

- Linux: `$XDG_CONFIG_HOME/cli` (default `~/.config/cli`)
- macOS: `~/Library/Application Support/cli`

Files after `cli configure init`:

| Path | Role |
| --- | --- |
| `auth.yaml` | Maps credential names → env vars + token files |
| `secrets/` | Token files (mode `600`) |
| `config.yaml` | Created on first `cli configure set` (or `init --example`) |

**Precedence:** environment variables → user `config.yaml` / token files → Pydantic code defaults.

Override the directory: `CLI_CONFIG_DIR=/path` (disables profile merge).

## Repo `config/` (contributors + CI)

The bundled `config/` tree is **not** loaded automatically. Tests and Docker set:

```bash
export CLI_CONFIG_DIR=$PWD/config
export CLI_PROFILE=test   # merges config.test.yaml
```

| Path | Role |
| --- | --- |
| [`config.yaml`](config.yaml) | Safe repo defaults for CI overlay base |
| [`config.example.yaml`](config.example.yaml) | Template for `cli configure init --example` |
| [`config.test.yaml`](config.test.yaml) | Test/CI overlay (fixture paths) |
| [`drives.yaml`](drives.yaml) | Cloud drive upload targets |
| [`auth.example.yaml`](auth.example.yaml) | Reference layout for `auth.yaml` |

## Docker

Pass secrets via `-e` (`NOTION_TOKEN`, etc.). CI images set `CLI_PROFILE=test` and copy `config/` into the container.

## What is not runtime config

- `config/project/examples/` — documentation samples
- `config/release/config.yaml` — GitHub Actions deploy placeholder
- `config/gh/phase5/*.batch.yaml` — one-off migration batches (reference only)
