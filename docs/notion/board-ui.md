# Task board — Notion UI

How the **Board** view is configured in Notion. Formula paste targets live under [properties/](./properties/README.md). Row data comes from private `header/` + `body/` via deploy.

## Sort

**Board** view — **⋯ → Sort** (top rule wins first, then tie-break):

| # | Property | Type | Order |
| --- | --- | --- | --- |
| 1 | **priority** | select | Ascending (`1` → `2` → `3`) |
| 2 | **Due Date** | formula | Ascending |

Within each **DerivedStatus** column, higher-priority cards float up; same priority sorts by earliest due.

## Property visibility

**Board** cards — **⋯ → Properties** (shown on card vs hidden but still in database).

### Shown on card

| Property | Type |
| --- | --- |
| **Name** | title |
| **tag** | select |
| **priority** | select |
| **link** | url |
| **Due Date** | formula |

### Hidden on card *(still used by formulas / yaml)*

| Property | Type |
| --- | --- |
| **recurrent** | formula |
| **last done** | date |
| **forced status** | select |
| **DerivedStatus** | formula |
| **Frequency** | select |
| **Interval** | number |

**Why hide:** keeps cards compact; cadence and overrides matter when editing the page or working in **Table** view.

## Layout

**Board** view — **⋯ → Layout**:

| Setting | Value |
| --- | --- |
| Show page icon | Off |
| Wrap all content | On |
| **Group by** | **DerivedStatus** |
| Color columns | On |
| Open pages in | Center peek |
| Card preview | None |
| Card size | Medium |
| **Card layout** | **Compact** |

Column order on the board follows **DerivedStatus** buckets (`in progress` → `to do` → `future` → `in review` — confirm order in Notion).

## Table view

Use for bulk edits in Notion or cross-check against git yaml. Suggested sort (all ascending):

| # | Property |
| --- | --- |
| 1 | **priority** |
| 2 | **tag** |
| 3 | **Name** |
| 4 | **recurrent** |
| 5 | **Frequency** |
| 6 | **Interval** |

**Upstream:** [Notion hub](../notion.md)
