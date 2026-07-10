# chrome-extensions

`gardusig/chrome-extensions` owns browser extension source. It does not own workflow or Docker orchestration.

## Pull request

- `markdown`: lint `.md` / `.mdx` files and validate fenced Mermaid diagrams
- `unit-test`: format, lint, typecheck, coverage
- `build`: production bundle

## Repo review

Manual `repo-review.yml` jobs:

- `unit-test`
- `build`

Both jobs use `docker/chrome-extensions.dockerfile`.
