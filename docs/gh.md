# GitHub integration (`cli gh`)

Deterministic GitHub operations for agents and humans. Wraps authenticated **`gh`** with JSON-first output and write gates (same model as `cli git`).

**Integration partner:** [cursor-skills](https://github.com/gardusig/cursor-skills) — `@gh-*` skills invoke these commands instead of embedding raw `gh` bash fences.

## Prerequisites

- `gh` installed and authenticated (`gh auth status`)
- `cli` on PATH

## Global flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `--repo owner/name` | gh context | Target repository |
| `--format json\|table` | `json` | Output shape (agents use json) |
| `--yes` / `-y` | off | Skip interactive write gate (use after Cursor **Proceed**) |

## Double-gate contract

| Context | Cursor skill | cli write |
| --- | --- | --- |
| Agent after **Proceed** | AskQuestion in chat | append **`--yes`** |
| Human in terminal | — | interactive gate or **`--yes`** |
| Read-only | no gate | no **`--yes`** |

## Issue commands

### Read (no gate)

```bash
cli gh issue list --state open --limit 30 --format json
cli gh issue view 42 --format json
cli gh issue search "label:bug" --format json
```

### Write (gate unless `--yes`)

```bash
cli gh issue create --title "1 — Epic" --body-file body.md --label epic:foo --yes
cli gh issue edit 42 --title "1.1 — Child" --yes
cli gh issue close 42 --comment "Done" --yes
cli gh issue delete 42 --yes
cli gh issue comment 42 --body "Note" --yes
cli gh issue batch --file batch.yaml --yes
```

### Batch YAML shape

```yaml
operations:
  - action: create
    title: "1 — Epic title"
    body_file: .cursor/gh/issue/epic.md
    labels: ["epic:slug", "issue-type:epic"]
  - action: create
    title: "1.1 — Child"
    body_file: .cursor/gh/issue/child.md
    labels: ["epic:slug", "issue-type:child"]
  - action: edit
    number: 100
    body_file: .cursor/gh/issue/epic-updated.md
```

## Label commands

Manifest path: **`config/gh/labels.manifest.yaml`** (repo-owned epic/area taxonomy).

```bash
cli gh label list --format json
cli gh label create my-label --color ff0000 --yes
cli gh label delete my-label --yes
cli gh label sync --manifest config/gh/labels.manifest.yaml --yes
cli gh label sync --manifest config/gh/labels.manifest.yaml --prune-orphans --yes
```

Retro-label open issues from a batch file:

```bash
cli gh issue batch --file config/gh/backlog-labelize.batch.yaml --yes
```

Host helpers (when `cli` is on PATH):

```bash
./scripts/gh/sync-labels.sh
./scripts/gh/labelize-backlog.sh
```

## Pull request commands

```bash
cli gh pr list --format json
cli gh pr view 10 --format json
cli gh pr diff 10
cli gh pr create --title "…" --body-file pr.md --yes
cli gh pr edit 10 --body-file pr.md --yes
cli gh pr close 10 --yes
cli gh pr merge 10 --merge-method squash --yes
```

## Repo commands

```bash
cli gh --format json repo view
cli gh --format json repo view --json-fields nameWithOwner,owner,issueTemplates,pullRequestTemplates
```

## Backlog commands

Sequence titles use **`N — Title`** (epic) and **`N.M — Title`** (child).

```bash
cli gh backlog tree --format json
cli gh backlog next --format json
cli gh backlog resequence --file plan.yaml --yes
```

Resequence plan YAML:

```yaml
renames:
  - number: 42
    title: "1.2 — Renamed child"
```

## JSON output examples

**`backlog next`:**

```json
{
  "number": 71,
  "title": "1.1 — PR prevalidate",
  "url": "https://github.com/owner/repo/issues/71",
  "sequence": "1.1 —"
}
```

**`backlog tree`:**

```json
{
  "repo": "owner/repo",
  "roots": [{"number": 70, "title": "1 — Epic", "sequence": "1 —"}],
  "epics": {"epic:slug": [{"number": 71, "title": "1.1 — Child"}]}
}
```

## Tests

Unit tests mock the gh provider: `tests/gh/test_commands.py`.

Run: `./scripts/test/unit.sh`

## See also

- [architecture.md](architecture.md) — CLI → Service → Provider
- [cursor-skills docs/gh.md](https://github.com/gardusig/cursor-skills/blob/main/docs/gh.md)
- cli epic **01** — GitHub integration
