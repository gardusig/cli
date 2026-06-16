# 📌 Due Date

| | |
| --- | --- |
| **Type** | formula |

Next due from **last done** and cadence, or **last done** alone when not recurrent.

## 📌 Formula

```javascript
if(
  prop("recurrent"),
  dateAdd(prop("last done"), prop("Interval"), prop("Frequency")),
  prop("last done")
)
```

| Case | Result |
| --- | --- |
| **recurrent** | **last done** + **Interval** × **Frequency** |
| **Not recurrent** | **Due Date** = **last done** (one-shot; status still from [derived-status.md](./derived-status.md)) |

Depends on [recurrent.md](./recurrent.md).

**Upstream:** [Properties](./README.md)
