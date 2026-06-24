# 📌 forced status

| | |
| --- | --- |
| **Type** | select |
| **Source** | [header/](../header/) **`forced_status`** field (usually empty) |
| **Default** | *(none / empty)* |
| **Allowed** | `in review` · `in progress` · `to do` · `future` |

Manual override of **DerivedStatus**. When set, [derived-status.md](./derived-status.md) returns this value instead of computing from **Due Date**.

**Upstream:** [Properties](./README.md)
