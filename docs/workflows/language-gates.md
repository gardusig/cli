# Language Gates

`gardusig/cli` enforces repository language policies during pull-request
CI. The policy lives in each per-repo workflow YAML and is forwarded to the
Docker `repo-hygiene` target as `HYGIENE_POLICY_JSON`.

## Policy Location

Pull-request policies are declared under:

```text
.github/workflows/pull-request/
```

Each `repo-hygiene` job may define:

```yaml
hygiene_policy:
  allowed_extensions:
    - .md
    - .py
  allowed_filenames:
    - README.md
    - LICENSE
  ignored_prefixes:
    - .git/
```

## Runtime Flow

1. `cli pipeline config resolve` includes `hygiene_policy` in the job matrix.
2. `cli pipeline docker run` serializes that policy into the Docker build argument
   `HYGIENE_POLICY_JSON`.
3. The repo Dockerfile writes the JSON to `/tmp/hygiene-policy.json`.
4. `cli structure check /workspace --policy-file /tmp/hygiene-policy.json`
   validates the checkout.

The CLI check is the source of truth for language, root file/folder, depth, and
layout policy.

## Docker-First Setup

Do not require contributors or automation to install repo dependencies locally
for verification. Each repository has a Dockerfile under `docker/`; use that
file as the setup contract for local and CI validation.

Examples:

```bash
docker build --target repo-hygiene -f docker/gardusig/cli.dockerfile .
docker build --target repo-hygiene -f docker/wiki.dockerfile /path/to/wiki
```

## Contract

- Policies are allowlists. A file extension or extensionless filename must be
  explicitly allowed unless ignored by path prefix.
- Generated and dependency folders should be ignored by prefix rather than
  widening the language allowlist.
- App repositories should not add local Dockerfiles, CI shell directories, or
  extra workflow files.
