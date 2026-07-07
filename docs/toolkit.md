# Language Toolkit

`gardusig-cli` exposes action-first commands with Python-native orchestration:

- Python owns Typer command UX, command catalog data, repo/language detection,
  prerequisite checks, environment setup, and command handlers.
- Python handlers run terminal commands (`npm`, `pytest`, `mvn`, `clang-format`,
  `markdownlint-cli2`, etc.).
- Dockerfiles and workflow YAML stay in `github-pipelines`.

## Commands

```bash
cli lint repo /workspace
cli lint markdown /workspace
cli test python unit /workspace
cli test java unit /workspace
cli structure check /workspace --policy-file policy.yaml
cli validate vault /workspace --base origin/main
cli languages list
cli languages show java
```

`cli lint repo` is the default CI lint entrypoint. It detects the languages
present in the repo and calls each related Python handler once.

## Dependency Model

The CLI package stays lean. Language dependencies are OS tools installed by the
developer machine or by the relevant Docker stage. For example, Java commands
check only Java/Maven/Gradle prerequisites and do not require Node or pytest.

## Pipeline Runtime

`github-pipelines` workflow YAML calls CLI-owned runtime commands:

```bash
cli pipeline config resolve --family pull-request --pipeline-src pipeline-src
cli pipeline docker run --job-json "$JOB_JSON" --pipeline-src pipeline-src --app-src app-src
cli pipeline task run --command-json "$TASK_COMMAND" --repo-dir database-src
```

These commands call `src.services.pipeline_runtime` directly and keep resolver,
Docker job, and task-action behavior inside the CLI package.
