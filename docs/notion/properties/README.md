# 📋 Task board — properties

One page per Notion column. **Formulas** — paste into **Edit property → Formula**. **Inputs** — from private `header/` yaml (see [task-pairs.md](../task-pairs.md)).

## 📊 Summary

- **Files:** 13 markdown (this tree)
- **Size:** ~6.4 KB (this tree)
- **Children:** derived-status 1 / ~885 B · due-date 1 / ~603 B · forced-status 1 / ~443 B · frequency 1 / ~318 B · interval 1 / ~249 B · last-done 1 / ~313 B · link 1 / ~236 B · name 1 / ~210 B · priority 1 / ~647 B · recurrent 1 / ~338 B · tag 1 / ~308 B

## 🧭 Index

1. [Derived status](./derived-status.md)
   1. Formula — board column from due date and forced status. · 1 files · ~885 B
2. [Due date](./due-date.md)
   1. Formula — next due from last done and recurrence. · 1 files · ~603 B
3. [Forced status](./forced-status.md)
   1. Select — manual override for DerivedStatus. · 1 files · ~443 B
4. [Frequency](./frequency.md)
   1. Select — days, weeks, months cadence unit. · 1 files · ~318 B
5. [Interval](./interval.md)
   1. Number — multiplier for Frequency. · 1 files · ~249 B
6. [Last done](./last-done.md)
   1. Date — last completion stamp. · 1 files · ~313 B
7. [Enabled](./enabled.md)
   1. Yaml — pause task for current life; skipped on deploy. · 1 files
8. [Name](./name.md)
   1. Title — task label on the board. · 1 files · ~210 B
9. [Priority](./priority.md)
   1. Select — priority 1 through 5. · 1 files · ~647 B
10. [Recurrent](./recurrent.md)
   1. Formula — whether the row repeats. · 1 files · ~338 B
11. [Tag](./tag.md)
   1. Select — domain tag for filtering. · 1 files · ~308 B

Board UI (sort, visibility, layout) is documented in [board-ui.md](../board-ui.md).

---

## 📌 Data flow

```text
header/**/*.yaml  →  deploy  →  Notion row properties
body/**/*.md        →  deploy  →  Notion page body
                    ↓
              recurrent (formula)
                    ↓
              Due Date (formula)
                    ↓
              DerivedStatus (formula)  →  board columns
                    ↑
              forced_status (optional override)
```

**Upstream:** [Notion hub](../../notion.md)
