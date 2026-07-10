# Secrets

Secrets are configured through `cli configure` or readable environment variables. Workflow files only pass GitHub secrets as environment variables; they do not define secret semantics.

## Required Values

| Configure key | Env var | Example shape | GitHub secret | Get it |
|---------------|---------|---------------|---------------|--------|
| `notion.token` | `NOTION_TOKEN` | `secret_...` | `gardusig/cli` / `tasks` / `NOTION_TOKEN` | [Google](https://www.google.com/search?q=how+to+create+notion+internal+integration+token) |
| `gh.token` | `GH_TOKEN` | `ghp_...` | `gardusig/cli` / `tasks` / `CENTRAL_PIPELINE_PAT` | [Google](https://www.google.com/search?q=how+to+create+a+github+fine+grained+personal+access+token) |
| `pypi.token` | `PYPI_API_TOKEN` | `pypi-...` | `gardusig/cli` / `release` / `PYPI_API_TOKEN` | [Google](https://www.google.com/search?q=how+to+create+a+pypi+api+token) |
| `docker.token` | `DOCKERHUB_TOKEN` | `dckr_pat_...` | `gardusig/cli` / default / `DOCKERHUB_TOKEN` | [Google](https://www.google.com/search?q=how+to+create+a+docker+hub+access+token) |
| `docker.username` | `DOCKERHUB_USERNAME` | Docker Hub user | vault / `cli configure set` | — |
| `testpypi.token` | `TESTPYPI_API_TOKEN` | `pypi-...` | `gardusig/cli` / default / `TESTPYPI_API_TOKEN` | [Google](https://www.google.com/search?q=how+to+create+a+testpypi+api+token) |
| `backup.password` | `BACKUP_ZIP_PASSWORD` | long random password | local-only | [Google](https://www.google.com/search?q=how+to+generate+a+strong+random+password+openssl) |
| `deepseek.token` | `DEEPSEEK_API_KEY` | `sk-...` | local-only | [Google](https://www.google.com/search?q=how+to+create+a+deepseek+api+key) |

## GitHub Actions Pattern

```yaml
env:
  NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
  GH_TOKEN: ${{ secrets.CENTRAL_PIPELINE_PAT }}
run: |
  cli configure import-env
  cli configure check --tasks
```

## Gemini Prompts

Open [Gemini](https://gemini.google.com/app), then paste one of these prompts:

### Notion

```text
How do I create a Notion internal integration token for API access? List the exact steps and what the token looks like.
```

### GitHub

```text
How do I create a GitHub fine-grained personal access token that can read repositories, write contents, and manage issues?
```

### PyPI

```text
How do I create a PyPI API token scoped to one project and use it in GitHub Actions?
```

### TestPyPI

```text
How do I create a TestPyPI API token for package upload testing?
```

The machine-readable manifest is `config/secrets.manifest.yaml`.
