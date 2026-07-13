# Secrets

| Key | Env var | Used by |
| --- | --- | --- |
| `notion.token` | `NOTION_TOKEN` | `cli notion`, `cli tasks` |
| `backup.password` | `BACKUP_ZIP_PASSWORD` | encrypted drive zips |
| `deepseek.token` | `DEEPSEEK_API_KEY` | `cli opencode` |
| `pypi.token` | `PYPI_API_TOKEN` | `cli pypi upload`, `cli release` |
| `google_drive.token` | `GOOGLE_DRIVE_TOKEN` | `cli drive` (Google) |
| `onedrive.token` | `ONEDRIVE_TOKEN` | `cli drive` (OneDrive) |

Canonical manifest: [`config/secrets.manifest.yaml`](../config/secrets.manifest.yaml).

```bash
cli configure set notion.token --stdin
```
