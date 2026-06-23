# Backup (deprecated)

**Use [`drive.md`](drive.md)** — `cli backup` is a hidden alias for `cli drive`.

| Old | New |
| --- | --- |
| `backup status` | `drive status` |
| `backup repository sync` | `drive ingest` |
| `backup repository list` | `drive list` |
| `backup repository delete` | `drive delete` |

Encrypted private repos use `encrypted: true` + `BACKUP_ZIP_PASSWORD`. Deploy replicas with `cli drive deploy` (cloud + USB).
