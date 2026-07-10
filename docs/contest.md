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

Build or pull the contest runner image through the central pipeline assets in `gardusig/cli`.

Requires Docker on the host. The runner image is `cli-contest:runner`; its Dockerfile and build workflow live in `gardusig/cli`, not in this repo.

Monitor the image and any leftover containers with `cli docker`:

```bash
cli docker images --repository cli-contest:runner --format json
cli docker containers --name cli-contest --format json
cli docker stats --name cli-contest --format json
```

`cli docker` is monitor/cleanup only. It can remove containers or prune images after a write gate, but it does not start contest containers; `cli contest validate` owns execution.

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
image: cli-contest:runner
cxx_std: c++17
```

```bash
cli contest validate --config contest.yaml
```

Defaults: [`config/contest/defaults.yaml`](../config/contest/defaults.yaml) (`timeout: 10`, `memory_mb: 256`, `image: cli-contest:runner`, `cxx_std: c++17`).

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

## Codeforces-Style Walkthrough

Keep real solutions in an external competitions repo. Copy the templates once:

```bash
mkdir -p ../competitions/codeforces/2237-a
cp config/contest/templates/{generator.py,brute.py,lib.py} ../competitions/codeforces/2237-a/
```

Create a generator that emits a multi-test input for each tier. The small tier should include samples and corner cases; the large tier should be heavy enough that the brute is expected to TLE.

```python
from lib import Case, format_multi_test

def format_one(payload: dict) -> list[str]:
    values = payload["values"]
    return [str(len(values)), " ".join(map(str, values))]

def small_cases() -> list[Case]:
    return [
        Case("single", {"values": [7]}),
        Case("zeros", {"values": [0, 0, 0]}),
        Case("negative", {"values": [-3, 5, -2]}),
    ]

def large_cases() -> list[Case]:
    return [Case("stress", {"values": list(range(1, 45001))})]

if __name__ == "__main__":
    import sys
    tier = sys.argv[1]
    cases = small_cases() if tier == "small" else large_cases()
    sys.stdout.write(format_multi_test(cases, format_one))
```

Implement the brute as the slow, trusted reference. It must read `T` on the first line and print one answer per case:

```python
import sys

def solve_case() -> str:
    n = int(sys.stdin.readline())
    arr = list(map(int, sys.stdin.readline().split()))
    total = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                total += arr[i]
    return str(total)

t = int(sys.stdin.readline())
print("\n".join(solve_case() for _ in range(t)))
```

Write the fast C++ solution in the external repo:

```cpp
#include <iostream>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        long long sum = 0;
        for (int i = 0; i < n; ++i) {
            int x;
            cin >> x;
            sum += x;
        }
        cout << sum << "\n";
    }
}
```

Run validation:

```bash
cli contest validate \
  --fast ../competitions/codeforces/2237-a/solution.cpp \
  --brute ../competitions/codeforces/2237-a/brute.py \
  --generator ../competitions/codeforces/2237-a/generator.py \
  --timeout 10 \
  --memory-mb 256 \
  --cxx-std c++17
```

Or keep paths and limits in `contest.yaml`:

```yaml
fast: ../competitions/codeforces/2237-a/solution.cpp
brute: ../competitions/codeforces/2237-a/brute.py
generator: ../competitions/codeforces/2237-a/generator.py
timeout: 10
memory_mb: 256
image: cli-contest:runner
cxx_std: c++17
```

```bash
cli contest validate --config ../competitions/codeforces/2237-a/contest.yaml
```

Existing generators need the `small_cases()` / `large_cases()` split (replace a single `cases()` function).

## Result Interpretation

- **PASS:** small outputs match; fast solution succeeds on large.
- **PASS + warning:** small outputs match and fast succeeds, but the brute also finished on the large tier, so the stress case may be too weak.
- **FAIL with small diff:** brute and fast disagree on the small tier. Fix the fast solution or the brute before trusting stress tests.
- **FAIL compile error:** the C++ solution failed to compile inside `cli-contest:runner`.
- **FAIL runtime error:** brute or fast exited nonzero.
- **FAIL TLE on fast:** the optimized solution timed out on large input.

## Execution model

1. Generator runs **locally** → `small.txt`, `large.txt` in a temp workspace
2. C++ compiled once in Docker (`cli-contest:runner`)
3. **Phase 1:** brute + fast on `small.txt` in parallel → compare outputs
4. **Phase 2:** (if small matches) brute + fast on `large.txt` in parallel → check TLE behavior
5. Temp workspace deleted; summary printed

`--timeout` and `--memory-mb` apply to every solution container.
