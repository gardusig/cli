# Task board — formulas hub

Notion formulas for the personal task board. **Data:** private `header/` yaml. **UI:** [board-ui.md](./board-ui.md). **Columns:** [properties/](./properties/README.md).

## Logic summary

```text
yaml last_done + frequency/interval  →  recurrent  →  Due Date  →  DerivedStatus
         ↑                               ↑              ↑
    git / ingest                    formulas      forced_status (optional)
```

**Yaml inputs** (private `header/`): `name`, `tag`, `priority`, `frequency`, `interval`, `last_done`, `forced_status`, `enabled`.

**Notion formulas:** [recurrent](./properties/recurrent.md) · [Due Date](./properties/due-date.md) · [DerivedStatus](./properties/derived-status.md).

**Board sort (live):** **priority** ↑ then **Due Date** ↑ — see [board-ui.md § Sort](./board-ui.md#sort).

**Upstream:** [Notion hub](../notion.md)
