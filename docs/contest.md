# Contest validate

Docker-backed two-tier validation for competitive programming solutions.

## Overview

`cli contest validate` checks a fast C++ solution against a Python brute on:

| Tier | Input | Goal |
| --- | --- | --- |
| **small** | Corner cases, tiny inputs | Brute and fast outputs **must match** |
| **large** | Stress inputs | Fast must finish; brute should **TLE** (warning if brute also finishes) |

Fast solutions are **not** stored in cli. You provide three paths:

- `--fast` — C++ solution (outside this repo)
- `--brute` — Python slow reference
- `--generator` — Python input generator

Templates: [`config/contest/templates/`](../config/contest/templates/)

## Setup

Build the contest runner image once (see [docker.md](docker.md#dev--test-image)):

```bash
./scripts/docker/build-contest-image.sh
```

Requires Docker on the host.

## Usage

```bash
cli contest validate \
  --fast      /path/to/solution.cpp \
  --brute     /path/to/brute.py \
  --generator /path/to/gen.py \
  --timeout 10 \
  --memory-mb 256
```

Optional YAML config (paths and limits):

```yaml
fast: ../solutions/foo.cpp
brute: ./brute.py
generator: ./gen.py
timeout: 10
memory_mb: 256
```

```bash
cli contest validate --config contest.yaml
```

Defaults: [`config/contest/defaults.yaml`](../config/contest/defaults.yaml) (`timeout: 10`, `memory_mb: 256`).

## Generator contract

The generator must support two CLI tiers:

```bash
python gen.py small   # → corner-case multi-test stdin batch
python gen.py large   # → stress multi-test stdin batch
```

Required functions:

```python
def small_cases() -> list[Case]: ...
def large_cases() -> list[Case]: ...
def format_one(payload) -> list[str]: ...
```

Copy [`config/contest/templates/generator.py`](../config/contest/templates/generator.py) as a starting point.

## Brute contract

Reads multi-test stdin (`T` on first line), writes one answer line per case. See [`config/contest/templates/brute.py`](../config/contest/templates/brute.py).

## Outcomes

| Result | Meaning |
| --- | --- |
| **PASS** | Small outputs match; fast OK on large; brute TLE on large |
| **PASS + warning** | Small match; fast OK on large; brute also finished on large |
| **FAIL** | Small mismatch, compile error, or fast failed on large |

## Example (external competitions repo)

```bash
cli contest validate \
  --fast ../solutions/codeforces/2237-a.cpp \
  --brute ../competitions/test/brutes/codeforces/2237-a.brute.py \
  --generator ../competitions/test/generators/codeforces/2237-a.gen.py
```

Existing generators need `small_cases()` / `large_cases()` split (replace single `cases()`).

## Execution model

1. Generator runs **locally** → `small.txt`, `large.txt` in a temp workspace
2. C++ compiled once in Docker (`cli-contest:runner`)
3. **Phase 1:** brute + fast on `small.txt` in parallel → compare outputs
4. **Phase 2:** (if small matches) brute + fast on `large.txt` in parallel → check TLE behavior
5. Temp workspace deleted; summary printed

`--timeout` and `--memory-mb` apply to every solution container.
