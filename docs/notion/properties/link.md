# 📌 link

| | |
| --- | --- |
| **Type** | url |
| **Source** | **`gardusig/private`** private repo (`gh.issues.repo`) — derived from `body_filepath` on deploy and ingest |

GitHub blob URL for the task runbook markdown under `tasks/` in the database repo:

`https://github.com/{gh.issues.repo}/blob/{notion.link_branch}/tasks/{body_filepath}`

Example: `body/clean/kitchen.md` →  
`https://github.com/gardusig/private/blob/main/tasks/body/clean/kitchen.md`

**Deploy:** always sets Notion `link` from the pair’s `body_filepath` (optional yaml `link` override in header).

**Ingest:** writes the repo-derived url into header yaml; Notion board `link` is not authoritative.

**Upstream:** [Properties](./README.md)
