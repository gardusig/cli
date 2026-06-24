# 📌 DerivedStatus

| | |
| --- | --- |
| **Type** | formula |
| **Board** | **Group by** this property ([board-ui.md](../board-ui.md)) |

Maps each row to a column. **forced status** wins when set.

## 📌 Formula

Property names in `prop("…")` must match Notion exactly (including spaces).

```javascript
if(
  prop("forced status"),
  prop("forced status"),
  if(
    !prop("Due Date"),
    "in review",
    if(
      prop("Due Date") > dateAdd(today(), 4, "weeks"),
      "future",
      if(
        prop("Due Date") > dateAdd(today(), 3, "days"),
        "to do",
        "in progress"
      )
    )
  )
)
```

| Condition (after override) | Status |
| --- | --- |
| No **Due Date** | `in review` |
| Due more than 4 weeks out | `future` |
| Due more than 3 days out (within 4 weeks) | `to do` |
| Due within 3 days | `in progress` |

**Upstream:** [Properties](./README.md)
