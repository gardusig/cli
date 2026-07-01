# cursor-skills migration archive

Verbatim embed of [`gardusig/cursor-skills`](https://github.com/gardusig/cursor-skills) before local repo removal.

## Contents

| Path | Purpose |
|------|---------|
| [`snapshot/`](snapshot/) | Full copy of `skills/`, `docs/`, `tests/` (was `.cursor/tests`), `scripts/` (was `.cursor/scripts`), root README |
| [`distill/`](distill/) | Curated extracts for active cli porting |
| [`MANIFEST.json`](MANIFEST.json) | File list + SHA-256 checksums |

## Source commit

See `source_commit` in `MANIFEST.json`.

## Port status

See [`distill/INDEX.md`](distill/INDEX.md) for `@gh-*` → `cli` command mapping.

## Deletion policy

The standalone `cursor-skills` repository is deprecated. All normative skill content lives here until ported into:

- `cli craft issue` / `cli craft pr` / `cli review pr`
- `src/providers/opencode.py`
- `docs/workflows.md`
- `tests/pack/`
