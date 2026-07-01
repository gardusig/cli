---
name: read-dependencies-discover
description: >-
  Read-only batch: scan READMEs, CI, and repo config to infer stacks, toolchains, coverage expectations,
  and authoritative check commands; then map gaps vs disk (lockfiles, node_modules, venv). Used by @git-review §1–2 and
  @gh-issue-review (read-only context).
---
# Internal: Discover + map gaps (dependencies / stack)

**Library.** Single **batch** of evidence gathering for **`@git-review`**: Discover (§1) and Map gaps (§2). Does not run installs, formatters, tests, or git writes—callers run **[`write-dependencies-install`](../../internal/write/dependencies/install/SKILL.md)** next.

## Language interaction policy

Always apply [`read-safety-language-interaction-rules`](../../safety/language-interaction-rules/SKILL.md) first. Use English by default for all assistant output, including AskQuestion prompts/options, unless the user explicitly requests another full-language response.

## Batch A — Discover

### Documentation (priority)

Read—**do not assume only** `./README.md`:

- `README.md` (root), `README.rst`, `docs/` index READMEs, `CONTRIBUTING.md`, `INSTALL.md`, `DEVELOPMENT.md`.
- Monorepos: nested `README.md` under `packages/`*, `apps/`*, etc., when root points there.

### Configuration signals (infer stacks)

Scan root (and workspace layout) for:

| Area      | Signals                                                                             |
| --------- | ----------------------------------------------------------------------------------- |
| Node / TS | `package.json`, lockfiles, `tsconfig.json`, eslint/prettier/vitest/jest configs     |
| Python    | `pyproject.toml`, `requirements*.txt`, `ruff`, `.flake8`, `.python-version`, `mypy` |
| Rust      | `Cargo.toml`, `rust-toolchain.toml`, `clippy.toml`                                  |
| Go        | `go.mod`, `.golangci.*`                                                             |
| Other     | `Gemfile`, `pom.xml`, `build.gradle*`, `Makefile`, `justfile`, `Taskfile.yml`       |
| CI        | `.github/workflows/*.yml`, `.gitlab-ci.yml`, etc.                                   |

### Internal summary (produce for downstream)

- **Languages / stacks present** (or “docs-only”).
- **Required toolchain** (README, `.nvmrc`, `rust-toolchain.toml`, …).
- **Authoritative check commands** — README → CI → Makefile / `package.json` / `pyproject.toml` scripts → defaults in `[read-config-configuration](../configuration/SKILL.md)` / `[write-quality-evaluate](../../internal/write/quality/evaluate/SKILL.md)`.

If **no** code stack: report “no code checks applicable”; still allow documentation pass later.

### Coverage expectations (§1d analogue)

From README, CI, scripts, config: infer **whether** coverage is required and **which** command(s) / thresholds apply for `[write-quality-evaluate](../../internal/write/quality/evaluate/SKILL.md)` §7b.

### API surface signals (for `docs/api/` gating)

Use when **`read-docs-wiki`** needs to decide whether **`docs/api/`** is warranted. **Presence-only** scan (read paths / globs; do not assume runtime):

- OpenAPI / Swagger: `openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`
- GraphQL: `*.graphql`, `schema.graphql`, common `graphql` schema filenames
- gRPC: `*.proto`
- Framework hints: `routes.ts`, `router.go`, `urls.py`, `APIRouter`, `app/api/`, `pages/api/`, `src/routes/` (when clearly HTTP APIs)

If **none** of the above are credible for this repo, report **no API docs scaffold** unless the user overrides in chat.

### Monorepo / multi-package hints

Top-level **`services/`**, **`apps/`**, **`packages/`**, or workspace config (`pnpm-workspace.yaml`, `go.work`, etc.)—surface in the internal summary for **`monorepo`** / profile selection (**`read-docs-wiki`**).

---

## Batch B — Map gaps

From Batch A, compare **documented / CI** expectations to **disk**:

- Lockfile vs `node_modules` / vendor / `venv` / `.venv` presence when README requires install.
- CI step order vs what has been run locally (e.g. `npm ci` vs `npm install`).
- README vs CI mismatch — prefer README for **local dev**, **call out** divergence.

**Output:** Targeted gap list for `[write-dependencies-install](../../internal/write/dependencies/install/SKILL.md)`.

---

## Do not

- Install packages, run tests, or edit files.
- Skip CI/README when inferring commands.

## See also

- [`read-config-configuration`](../configuration/SKILL.md) — resolve command matrix.
- [`read-docs-wiki`](../doc-wiki/SKILL.md) — **`docs/api/`** gating and doc profiles.
- [`read-safety-structured-qa`](../../../internal/read/safety/structured-qa/SKILL.md) — **§3a** confirmations for destructive prep (via **`write-dependencies-install`**).
