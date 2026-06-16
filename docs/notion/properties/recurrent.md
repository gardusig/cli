# 📌 recurrent

| | |
| --- | --- |
| **Type** | formula |

True when both **Interval** and **Frequency** are set.

## 📌 Formula

```javascript
if(prop("Interval") and prop("Frequency"), true, false)
```

One-shot rows (e.g. **invest**, **resume**, **bags**) leave cadence empty → `false`.

**Upstream:** [Properties](./README.md)
