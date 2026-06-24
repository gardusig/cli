# Drive commands

**`cli drive`** owns the tag-zip lifecycle after git tagging: local store (iCloud) and cloud upload.

| Phase | Command | What it does |
| --- | --- | --- |
| Local hub | `drive status` | Git tags vs zips under `backup.tags_dir` |
| Local hub | `drive ingest` | Zip every git tag for configured repos (or one `PATH`) |
| Local hub | `drive list` · `drive delete` | Inspect or remove local zips |
| Cloud | `drive upload` | Deploy missing zips to cloud replicas (append-only) |
| Cloud + USB | `drive deploy` | Deploy to all replicas (cloud drives and USB paths) |
| **All-in-one** | `drive sync` | Ingest all `backup.repositories`, then deploy to replicas |

Parent epic: [issue #4](https://github.com/gardusig/cli/issues/4). Future: [cloud download #29](https://github.com/gardusig/cli/issues/29).

## Local store

Default on macOS:

```
~/Library/Mobile Documents/com~apple~CloudDocs/git-tags/
  {repo-name}/
    {repo-name}-2026-06-12.zip
```

Set via `backup.tags_dir` in `config/config.yaml`. iCloud syncs this folder automatically.

## Commands

```bash
cli drive status
cli drive ingest                    # all backup.repositories
cli drive ingest ~/git-local/foo    # one repo
cli drive list
cli drive delete ~/git-local/foo 2026-06-11 --yes
cli drive upload
cli drive upload google
cli drive deploy
cli drive deploy usb-backup
cli drive sync                        # ingest all + deploy all replicas
```

Shell wrappers: `./scripts/drive/status.sh`, `ingest.sh`, `upload.sh`, `sync.sh`.

See [issue #30](https://github.com/gardusig/cli/issues/30) for sync hardening (dry-run, logging, launchd).

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

`drive deploy` copies missing zips to every replica. Cloud replicas use the same append-only upload as before; USB replicas copy files to the configured mount path.

```yaml
drives:
  google:
    enabled: true
    root: git-tags
  onedrive:
    enabled: true
    root: git-tags
  proton:
    enabled: true
    root: git-tags
```

`drive upload` deploys to **cloud** replicas only. `drive deploy` includes USB replicas. When `backup.replicas` is empty, enabled providers in `drives.yaml` are used as cloud replicas. Provider APIs are stubs until OAuth is wired ([#12](https://github.com/gardusig/cli/issues/12)–[#14](https://github.com/gardusig/cli/issues/14)).

## Legacy

`cli backup …` is a hidden alias (`backup status` → `drive status`, `backup repository sync` → `drive ingest`).
