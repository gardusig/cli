# Markdown Validation

Markdown validation is now part of repo lint: each repository Dockerfile's
`lint` stage calls `cli lint repo /workspace`, which fans out to
`scripts/markdown/lint.sh` when Markdown is present.

## What It Checks

- Finds every `.md` and `.mdx` file in the application repo.
- Runs `markdownlint-cli2` with a shared baseline config.
- Extracts every fenced `mermaid` diagram and renders it with Mermaid CLI.

The validator ignores common generated or dependency directories such as `.git`, `node_modules`, `.venv`, `dist`, `build`, and `coverage`.

## Usage In PR Configs

Use one repo lint job before repo-specific unit tests or validation:

```yaml
jobs:
  - id: lint
    name: Repo lint
    target: lint
  - id: unit
    name: Unit tests
    target: unit-test
    needs: lint
```

The repo Dockerfile receives the target repo as the build context. The CLI
identifies the languages present and runs each related lint script once.

## Standalone Dispatch

Use `markdown.yml` only for deprecated standalone docs validation outside the
normal PR pipeline:

```bash
gh workflow run markdown.yml \
  -f repo_slug=python-cli \
  -f repository=gardusig/python-cli \
  -f ref=main
```

The same workflow accepts `repository_dispatch` with event type `markdown` and payload fields `repo_slug`, `repository`, and `ref`.

`gardusig/cli` is rejected as a target because it is the workflow host.

## Recommendation

Run `lint` before unit tests in pull-request workflows. It includes Markdown and
Mermaid validation plus any other language lint present in the repository.
