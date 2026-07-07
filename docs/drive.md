# Drive commands

**`cli drive`** owns the tag-zip lifecycle after git tagging: local store (iCloud) and cloud upload.

Drive workflows are local-only in the merged workflow catalog. They can affect any repository listed in `backup.repositories`, including public and private repos, but they should not get pipeline workflow files unless backup credentials and provider OAuth are moved into CI by a separate decision.

| Phase | Command | What it does |
| --- | --- | --- |
| Local hub | `drive status` | Git tags vs zips under `backup.tags_dir` |
| Local hub | `drive status --replicas` | Add read-only replica gap summary |
| Local hub | `drive ingest` | Zip every git tag for configured repos (or one `PATH`) |
| Local hub | `drive list` · `drive delete` | Inspect or remove local zips |
| Cloud | `drive upload` | Deploy missing zips to cloud replicas (append-only) |
| Cloud | `drive download` | Restore missing remote zips into local hub (one-way) |
| Cloud + USB | `drive deploy` | Deploy to all replicas (cloud drives and USB paths) |
| **All-in-one** | `drive sync` | Ingest all `backup.repositories`, then deploy to replicas |

Parent epic: [issue #4](https://github.com/gardusig/python-cli/issues/4). Download: [cloud download #29](https://github.com/gardusig/python-cli/issues/29). Sync hardening: [issue #30](https://github.com/gardusig/python-cli/issues/30).

## Local store

Default on macOS:

```text
~/Library/Mobile Documents/com~apple~CloudDocs/git-tags/
  {repo-name}/
    {repo-name}-2026-06-12.zip
```

Set via `backup.tags_dir` in `config/config.yaml`. iCloud syncs this folder automatically.

## Commands

```bash
cli drive status
cli drive status --replicas
cli drive ingest                    # all backup.repositories
cli drive ingest ~/git-local/foo    # one repo
cli drive list
cli drive delete ~/git-local/foo 2026-06-11 --yes
cli drive upload
cli drive upload google --dry-run
cli drive download onedrive
cli drive deploy --format json
cli drive deploy usb-backup
cli drive sync                        # ingest all + deploy all replicas
cli drive sync --dry-run              # deploy plan only (ingest skipped)
```

`--dry-run` and `--format json|table` apply to `upload`, `deploy`, `sync`, and `download`. JSON output lists replica names plus uploaded/skipped/failed (or downloaded) paths. Commands exit non-zero when any replica or file operation fails.

## Workflow with git

Single repo (cwd):

```bash
cli git tag --yes
cli git zip              # same as ingest for one tag, current repo
cli drive upload
```

Multi-repo:

```bash
cli drive ingest
cli drive status
cli drive upload
```

`git zip` zips one tag from the current repo. `drive ingest` zips **all** local tags for every configured repository (create or replace).

## Tag backup automation (#15)

No shell scripts or launchd plists live in this repo. The supported end-of-day chain is:

```bash
cli git tag --yes
cli git zip
cli drive upload          # or: cli drive sync
```

For all configured repositories:

```bash
cli drive sync
```

## Local workflow catalog

| Workflow | Sequence | Scope |
| --- | --- | --- |
| `drive-status` | `cli drive status` | Read git tags vs local zips for configured repositories |
| `drive-ingest` | `cli drive ingest` | Zip all tags for `backup.repositories`, or one selected path |
| `drive-upload` | `cli drive upload [provider]` | Upload missing zips to enabled cloud replicas |
| `drive-download` | `cli drive download [provider]` | Download missing zips from cloud replicas into local hub |
| `drive-deploy` | `cli drive deploy [replica]` | Deploy local zips to cloud and USB replicas |
| `drive-sync` | `cli drive sync` | **Primary:** ingest all `backup.repositories`, then deploy all replicas |
| `tag-backup-cloud` | `cli git tag --yes` -> `cli git zip` -> `cli drive upload` | Current repo end-of-day backup |
| `multi-repo-drive-sync` | `cli drive sync --dry-run` -> `cli drive sync` | Plan then run full backup loop |

**Primary daily workflow:**

```bash
cli drive sync --dry-run --format json   # ingest + deploy plan
cli drive sync                         # ingest all repos, deploy all replicas
```

Use `--no-strict` to continue when one repository ingest fails but others succeed.

`github-pipelines` is not a target workflow repo for Drive. If it appears in `backup.repositories`, it is only a local backup source.

## Configuration

`config/config.yaml`:

```yaml
backup:
  tags_dir: ~/Library/Mobile Documents/com~apple~CloudDocs/git-tags
  repositories:
    - path: ~/git-local/cli
    - path: ~/git-local/private
      encrypted: true
  replicas:
    - type: cloud
      provider: google
      root: git-tags
    - type: usb
      path: /Volumes/Backup/git-tags
```

Public repos use plain `git archive` zips. Repos with `encrypted: true` require `BACKUP_ZIP_PASSWORD` in the environment (`zip -er`).

### Cloud credentials

Tokens are never committed. Export OAuth access tokens or point `auth.yaml` at token files:

| Provider | Env var | Config key |
| --- | --- | --- |
| Google Drive | `GOOGLE_DRIVE_TOKEN` | `auth.google_drive.token_file` |
| OneDrive | `ONEDRIVE_TOKEN` | `auth.onedrive.token_file` |

See `config/secrets.manifest.yaml` and `.env.example`.

`drive deploy` copies missing zips to every replica. Cloud replicas use append-only upload (skip existing remote paths). USB replicas copy files to the configured mount path.

```yaml
drives:
  google:
    enabled: true
    root: git-tags
  onedrive:
    enabled: true
    root: git-tags
  proton:
    enabled: false
    root: git-tags
```

`drive upload` deploys to **cloud** replicas only. `drive deploy` includes USB replicas. When `backup.replicas` is empty, enabled providers in `drives.yaml` are used as cloud replicas.

## Proton Drive {#proton-drive}

Proton Drive is **deferred** ([#14](https://github.com/gardusig/python-cli/issues/14)). Proton does not expose a stable, documented third-party upload API suitable for this CLI. Leave `drives.proton.enabled: false` (default in repo `drives.yaml`). Use Google Drive, OneDrive, or a USB replica instead.

## Download semantics (#29)

`cli drive download` is one-way restore: remote zips missing locally are fetched into `backup.tags_dir`. Existing local files are skipped unless `--force` is passed. Proton download is deferred with upload.

## Legacy

`cli backup …` is a hidden alias (`backup status` → `drive status`, `backup repository sync` → `drive ingest`).
