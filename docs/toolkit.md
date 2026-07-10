# Language Toolkit

`gardusig-cli` exposes action-first commands with Python-native orchestration:

- Python owns Typer command UX, command catalog data, repo/language detection,
  prerequisite checks, environment setup, and command handlers.
- Python handlers run terminal commands (`npm`, `pytest`, `mvn`, `clang-format`,
  `markdownlint-cli2`, etc.).
- Dockerfiles and workflow YAML stay in `gardusig/cli`.

## Commands

```bash
cli lint repo /workspace
cli lint markdown /workspace
cli test python unit /workspace
cli test java unit /workspace
cli structure check /workspace --policy-file policy.yaml
cli validate tasks /workspace
cli languages list
cli languages show java
```

`cli lint repo` is the default CI lint entrypoint. It detects the languages
present in the repo and calls each related Python handler once.

## Dependency Model

The CLI package stays lean. Language dependencies are OS tools installed by the
developer machine or by the relevant Docker stage. For example, Java commands
check only Java/Maven/Gradle prerequisites and do not require Node or pytest.

## Hub CI

`gardusig/cli` workflow YAML calls yaml-local scripts for resolver and Docker
orchestration. Consumer Dockerfiles install `gardusig-cli` for `cli lint` and
`cli structure check`. See [gh-workflows.md](gh-workflows.md) for dispatching hub
workflows with `cli gh wf run`.
