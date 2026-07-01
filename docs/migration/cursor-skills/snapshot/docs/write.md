# Write libraries (`skills/internal/write/**`)

Path-faithful naming rule: `skills/internal/write/<path>/SKILL.md` => `name: write-<path-with-dashes>`.

## Domain roots

| Domain | Write root |
| --- | --- |
| Workflow | [`skills/internal/write/workflow/git/SKILL.md`](../skills/internal/write/workflow/git/SKILL.md) |
| GitHub | [`skills/internal/write/SKILL.md`](../skills/internal/write/SKILL.md) |

**Related:** [Read libraries](read.md) · [Wiki hub](README.md) · [GitHub skills](gh.md)

## Safety (read libraries)

- [`skills/internal/read/safety/structured-qa/SKILL.md`](../skills/internal/read/safety/structured-qa/SKILL.md)
- [`skills/internal/read/safety/skill-safety/SKILL.md`](../skills/internal/read/safety/skill-safety/SKILL.md)

Pair with read-only routing from [`docs/read.md`](read.md) before any mutation. **Command ownership** table (which skill owns which `gh`/`git` fence) lives in [read.md](read.md#command-ownership-gh--git-in-bash-fences).

## Installed handle mapping

Installed `@` handles flatten from the tree:

- `skills/internal/read/**` → `read-*` (path segments dash-joined after `internal/read/`)
- `skills/internal/write/**` → `write-*` (path segments dash-joined after `internal/write/`)

See [`.cursor/scripts/install.sh`](../.cursor/scripts/install.sh) for `--clean`, `--dry-run`, and `--verify-only`.

## Q&A bypass ENV

Default behavior is **unset/false**:

| Flag | Effect |
| --- | --- |
| `SKIP_QA_<PUBLIC_SKILL>=true` | Routine Q&A bypass for that public skill (e.g. `SKIP_QA_GIT_TAG=true`) |
| `SKIP_QA_WRITE=true` | Shared bypass for write-oriented routine prompts where the owning workflow allows |

High-risk actions still require session-level confirm per **skill-safety** even when flags are set.
