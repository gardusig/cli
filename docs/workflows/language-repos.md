# Language library repos

Public `gardusig/*` language repos share a lint → structure scaffold via `docker/language-repo.dockerfile`.

```bash
cli pipeline run pull-request python --ref my-branch
cli pipeline run pull-request rust --ref my-branch
```

`go` and `cpp` keep dedicated test/compile pipelines. The other top-10 language repos start as `lib/` + `examples/` scaffolds.
