# Notion task pairs manifest (committed)

`tasks.pairs.json` lists metadata/body path pairs. Task **files** (`metadata/`, `body/`) live in your private task root (`notion.task_root` in `config/config.yaml`).

Refresh after adding or renaming pairs:

```bash
shuttle notion pairs build
```

This overwrites `config/notion/tasks.pairs.json` in this repo.
