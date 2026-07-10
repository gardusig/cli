# Project workflows

Recurrent board polling for `cli project recurrence check`.

## Project recurrence

**File:** `.github/workflows/project-recurrence.yml`

Runs `cli project recurrence check --yes` on a schedule (Mondays 09:00 UTC) or
manual dispatch. Advances closed maintenance pairs to the next cycle per
`docs/project.md` in the CLI repo.

### Inputs

| Input | Default | Purpose |
| --- | --- | --- |
| `repository` | `gardusig/python-cli` | App repo with `config/project/` pairs |
| `ref` | `main` | Branch ref |
| `sha` | — | Commit SHA (preferred checkout) |

### Example

```bash
gh workflow run project-recurrence.yml -R gardusig/cli \
  -f repository=gardusig/python-cli \
  -f ref=main
```

## Related

- `docs/project.md` in `gardusig/python-cli` — pairs, recurrence, auto-link
- `ghcr.io/gardusig/operator-runner` — container image
