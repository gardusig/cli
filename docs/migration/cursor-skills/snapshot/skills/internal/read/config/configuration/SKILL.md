---
name: read-config-configuration
description: >-
  Read-only batch: from discovery output, resolve umbrella/format/lint/test/coverage commands to run.
  No shell installs or test execution. Used by @git-review between prepare and evaluate.
---
# Internal: Check command configuration

**Library.** Turns **discovery** (from **[`read-dependencies-discover`](../discover-dependencies/SKILL.md)**) into an **ordered verify command list** for **[`write-quality-evaluate`](../../internal/write/quality/evaluate/SKILL.md)**. Does **not** run commands—**evaluate** runs them.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Input

- Discovery summary: stacks present, README/CI hints, coverage expectations.
- **Post-install** state: e.g. `node_modules` exists, `cargo metadata` ok.

---

## Output (conceptual)

Record for each applicable stack:

1. **Umbrella** — Single entry if present (`make check`, `npm run check`, `pnpm validate`, `task check`, …) or **none**.
2. **Format** — Prefer **fix** scripts when present (`npm run format`, `cargo fmt`, `ruff format`, …); otherwise check-only (`prettier --review`, …). See **[`write-quality-evaluate`](../../internal/write/quality/evaluate/SKILL.md)** §5. **Skip** if no formatter.
3. **Lint** — `cargo clippy`, `ruff check`, `eslint`, `golangci-lint`, … per stack.
4. **Test** — Primary test script or `cargo test` / `pytest` / `go test ./...`.
5. **Coverage** — Commands + thresholds from discovery, or **omit** if §1d found no expectation.

Prefer **documented** order: umbrella **first** when it clearly subsumes format+lint+test; otherwise run §5–7 of **`@git-review`** as in **[`write-quality-evaluate`](../../internal/write/quality/evaluate/SKILL.md)**.

---

## Do not

- Run installs or checks.
- Invent `npm test` / `cargo clippy` without signals from discovery + repo config.

## See also

- **[`write-quality-evaluate`](../../internal/write/quality/evaluate/SKILL.md)** — executes the matrix.
