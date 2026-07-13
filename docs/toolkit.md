# Toolkit commands

`cli lint`, `cli test`, `cli structure`, `cli validate`, and `cli languages` wrap repository checks.

## Examples

```bash
cli lint python .
cli test python unit .
cli structure check . --require-layout
cli validate tasks
cli languages list
```

## Selective CI

```bash
cli test packages resolve --changed-path src/commands/git.py --format json
cli test packages run git --dry-run --format table
cli test packages suite --format json
```

See [ci-workflows.md](ci-workflows.md) for the in-repo Docker pipeline.
