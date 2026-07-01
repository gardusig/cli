# Skill checks

Lightweight regression checks for skill metadata and safety wording. Sibling of [`.cursor/scripts/`](../scripts/) (`install.sh` lives there).

## Run

From repo root:

```bash
./.cursor/tests/run.sh
# or
./.cursor/scripts/run.sh
```

**CI:** [`.github/workflows/pr-tests.yml`](../../.github/workflows/pr-tests.yml) runs the same command on pull requests.

## Checks

- `check-public-skills.sh`
  - validates frontmatter `name` and `description` in public workflow skills.
  - validates `public-skills.txt` exactly matches the discovered public skill set.
  - enforces mutation-oriented keywords (`AskQuestion`, `Proceed`, `confirm`, or `Goal`) for public mutation skills.
- `check-public-skill-routing-descriptions.py`
  - reads every path in `public-skills.txt` and enforces routing + structure contracts from `fixtures/public-skill-routing-tokens.json`.
  - **Routing:** folded YAML `description:` must contain each `require_all` substring for that skill’s `name:`; configured pairs must not share the same first description sentence (disambiguation guard).
  - **Before batch:** each public `SKILL.md` must include `## Before batch` (mandatory prep table; **always run first** wording). At least one `@` mention of another public skill (unless `before_batch_no_peer_public` in the manifest). Inside **Before batch** only, the first peer `@` must appear before the first library token when both exist there.
  - **Required internal skills:** `## Required internal skills` after **Before batch**, listing `read-*` / `write-*` libraries (names only).
  - **Recommended next steps:** `## Recommended next steps` after **Verification**, referencing `read-skill-suggestions` and `read-safety-structured-qa` §9 (one optional next-step **AskQuestion**; not auto-orchestration). No `## Follow-up Q&A (optional)`.
  - There is **no** `## After batch` section—public skills stay focused on the current task.
  - **No inline CLI:** public skill bodies must not embed runnable `` `git …` ``, `` `gh issue|pr|project|api …` ``, or ` ```bash ` / ` ```sh ` fences (YAML `description:` is excluded); delegate to `read-*` / `write-*` libraries.
  - **Verification:** each public `SKILL.md` must include `## Verification` with at least two `- [ ]` checklist items (unless `verification_exempt` in the manifest).
- `check-public-skill-dag.py`
  - validates `fixtures/public-skill-dag/graph.json` (required vs optional edges, acyclic **`required`** subgraph, `public-skills.txt` coverage) and fails if `docs/README.md` drifts from the emitted mermaid between `<!-- public-skill-dag:mermaid:start/end -->` markers. Flags: `--emit-mermaid`, `--write-readme`, `--verify-readme`.
- `check-write-skills-keywords.sh`
  - validates internal write helpers under `skills/internal/write/**` and mutating public skills listed in `write-guard-manifest.txt` include write-safety Q&A keywords.
- `check-skill-names.sh`
  - validates that each `skills/**/SKILL.md` `name:` matches the flattened handle produced by `.cursor/scripts/install.sh` (`read-*` / `write-*` for libraries; `gh-issue-*` for issue leaf skills under `skills/gh/issue/`).
- `check-read-write-command-ownership.py`
  - fails when the same `gh` / `git` command appears in multiple read/write skill bash fences.
- `check-no-internal-prefix.sh`
  - fails if `internal-read-` or `internal-write-` appears under `skills/`, `docs/`, `.cursor/tests/`, or root `README.md`.
- `check-public-invoke-names.py`
  - fails on legacy `@gh-issue-view`-style handles when `name:` is `gh-issue-view`.
- `check-stale-skill-refs.py`
  - fails on references to removed paths (GitHub Projects libraries, `@git-zip`, legacy `internal-*` prefixes).
- `check-structured-qa-shape.py`
  - fails on banned phrases that put Q&A summaries inside AskQuestion prompts (`summary in prompt`, etc.).
  - validates canonical `read-safety-structured-qa` §0 / §1f and `read-safety-language-interaction-rules` English-first AskQuestion policy.
- `check-public-no-qa-orchestration.py`
  - fails when public `@git-*` / `@gh-*` skill bodies orchestrate AskQuestion (outside language policy); use **write gate** instead.
- `check-public-skip-env.py`
  - every public skill documents **`## Skip & suggestions`** (`skip`, `SKIP_QA_*`, `SKIP_SUGGESTIONS`) and post-verify **`read-skill-suggestions`** delegation.
- `check-skill-suggestions-catalog.py`
  - every public **`@git-*` / `@gh-*`** skill has a matching **`### \`name\``** section in **`read-skill-suggestions-next-steps-options`**.

## Scope

Public skills are `SKILL.md` files under `skills/git/` and `skills/gh/`. Read/write libraries live under `skills/internal/read/**` and `skills/internal/write/**`.
