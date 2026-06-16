# Task pair templates

Every board row is a **pair**: one `header/*.yaml` + one `body/*.md` with the **same relative path stem** under `notion.task_root`. Never add a header without its body (or the reverse). Register new pairs in [tasks.pairs.json](../tasks.pairs.json) — see [Notion docs](../../../docs/notion/task-pairs.md).

## Pair rule

```text
header/<category>/<task>.yaml  ↔  body/<category>/<task>.md
```

Example: `header/clean/kitchen.yaml` ↔ `body/clean/kitchen.md`

| File | Role |
| --- | --- |
| **Header** | Notion title (`name`), cadence (`frequency`, `interval`, `last_done`), `priority`, `tag` |
| **Body** | Page content only — `## Steps` and `## Done when` |

Cadence lives in **header only**. Steps and checklists live in **body only**.

## Templates

1. [header.yaml](./header.yaml) — copy when creating a new row
2. [body.md](./body.md) — copy when creating a new row

## Header (`header/*.yaml`)

Machine-readable board metadata. Shuttle and Notion read these fields; the body file must not repeat them.

| Field | Required | Notes |
| --- | --- | --- |
| `name` | yes | Unique Notion title — emoji + short label (e.g. `🛒 buy perishable`) |
| `frequency` | yes | `days` · `weeks` · `months` · `years` |
| `interval` | yes | Integer — every N units of `frequency` |
| `last_done` | yes | ISO date `'YYYY-MM-DD'` — update when you finish in real life |
| `priority` | yes | P-level integer |
| `tag` | yes | Board grouping — `buy` · `clean` · `sync` · `pay` · etc. |

**Do:** keep names stable; bump `last_done` after each completion.  
**Don't:** put steps, links, or long prose in yaml.

## Body (`body/*.md`)

Deploy-ready Notion page content — what you see when you open the task.

| Section | Purpose |
| --- | --- |
| `## Steps` | Numbered actions — smallest concrete moves first |
| `## Done when` | Checkbox list — objective “finished” criteria |

**Do:** tables, inline lists, quantities when the task needs them.  
**Don't:** title line, cadence intro, `frequency`/`last_done`, links to other wiki files, or references to yaml/board plumbing.

After creating both files under `notion.task_root`, run `shuttle notion pairs build`.

**Upstream:** [Notion hub](../../../docs/notion.md)
