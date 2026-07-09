# GitHub Actions workflows (`cli gh wf`)

Short form first; long form in parentheses.

## Command tree

```
cli gh wf  (= cli gh workflow)
├── list | view | enable | disable
└── run
    ├── <workflow.yml>  [-f k=v …]     # start a run
    ├── list | view | failed | watch | cancel | rerun | delete
```

## Examples

```bash
# Start hub PR checks
cli gh wf run dispatch.yml -R gardusig/yaml \
  -f workflow=pull-request -f repository=gardusig/database -f ref=main -f repo_slug=database

# Debug a failed PR run
cli gh wf run list -R gardusig/private --workflow "Pull request" --limit 5
cli gh wf run view 29015588872 -R gardusig/private
cli gh wf run failed 29015588872 -R gardusig/private
cli gh wf run rerun 29015588872 -R gardusig/private --failed
```

Equivalent long form: `cli gh workflow run failed …`.
