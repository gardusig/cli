# Notion task pairs manifest (committed)

`tasks.pairs.json` lists header/body path pairs. Task **files** (`header/`, `body/`) live in your private task root (`notion.task_root` in `config/config.yaml`).

Pair scaffolds for new rows: [templates/](./templates/README.md).

Refresh after adding or renaming pairs:

```bash
cli notion pairs build
```

This overwrites `config/notion/tasks.pairs.json` in this repo.
