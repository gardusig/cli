# Test config fixtures

Used when `CLI_PROFILE=test` (pytest autouse fixture sets `CLI_CONFIG_DIR` here).

Not shipped in the PyPI wheel — runtime defaults live in `src/data/`; user settings in `~/.config/cli`.

Optional local overrides: export env vars or use a project-root `.env` (see [docs/secrets.md](../../docs/secrets.md)). CI uses env injection, not a committed `.env`.
