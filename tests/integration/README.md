# Integration tests

Dockerized checks validate every public command surface with mocked external APIs where needed.

## Layout

- `check_integration_coverage.py` — ok/fail inventory gate
- `check_public_commands.py` — full public command runner
- `check_package_integration.py` — per-package legs (`git`, `notion`, `drive`, `chrome`, …)

## Config

Default `CLI_CONFIG_DIR=config/ci` (see `tests/conftest.py`). Workflow E2E uses disposable git repos under `.integration-scratch/`.

## Run

```bash
cli test python integration .
```
